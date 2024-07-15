import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import time
import config
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from translator import format_vacation_data
from googleVacationApi import  get_today_vacation_data
from term_deposit_rotation import extract_deposit_df
from formatting import get_current_year, create_leave_string
from googleVacationApi import get_spreadsheet_id_in_folder
from onebyone import get_or_create_1on1_spreadsheet, get_spreadsheet_service, find_spreadsheet_in_shared_drive, update_spreadsheet_on_oneByone, match_people, get_name_list_from_json
from security_system import update_authority
import pandas as pd


def send_slack_message(channel_id, text):
    try:
        client = WebClient(token=config.bot_token_id)
        response = client.chat_postMessage(
            channel=channel_id,
            text=text
        )
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

def notify_today_vacation_info():
    channel_id = config.all_bot_channel

    search_file_name = create_leave_string(get_current_year())
    spreadsheet_id = get_spreadsheet_id_in_folder(search_file_name, config.dummy_vacation_directory_id)
    
    if spreadsheet_id == None:
        msg = ("휴가 스프레드 시트를 재확인해주세요.\n")
        send_slack_message(channel_id, msg)    
        msg = ("금일 휴가 조회를 종료합니다.\n\n")
        send_slack_message(channel_id, msg)
        return
    
    json_keyfile_path = config.kakao_json_key_path
    send_slack_message(channel_id, "금일 휴가자 정보를 조회합니다. 잠시만 기다려주세요.\n")
    today_vacation_data = get_today_vacation_data(spreadsheet_id, json_keyfile_path)
    
    if len(today_vacation_data) == 0:
        send_slack_message(channel_id, "금일 휴가자 정보가 존재하지 않습니다. 금일 휴가 조회를 종료합니다")
        return
    
    formatted_vacation_data = format_vacation_data(today_vacation_data)
    
    for data in formatted_vacation_data:
        send_slack_message(channel_id, data)
    send_slack_message(channel_id, "금일 휴가 조회를 종료합니다")


def notify_one_by_one_partner():
    # New matching
    update_authority()
    spreadsheet_id = update_spreadsheet_on_oneByone(match_people(get_name_list_from_json()))

    sheets_serivce, drive_service = get_spreadsheet_service()
    
    # Determine the title for the new spreadsheet
    current_year = datetime.now().year
    new_title = f"{current_year}1on1"

    sheet_metadata = sheets_serivce.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = sheet_metadata.get('sheets', [])
    last_sheet = sheets[-1]
    last_sheet_id = last_sheet['properties']['sheetId']
    last_sheet_name = last_sheet['properties']['title']

    # Retrieve data from the last sheet
    range_name = f"{last_sheet_name}!A:C"  # Adjust the range as per your data layout
    result = sheets_serivce.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    
    # Remove the first row (header)
    if values:
        values = values[1:]

    # values 내 모든 데이터를 모두 조회할거야
    # 하나의 행에서 두번째 데이터에는 슬랙 아이디가 존재하는 상황
    # 해당 슬랙 아이디에게 다이렉트 메세지를 보낼거야. 내용은 해당 행에서의 세번째 데이터를 담아서 보낼거야

    """
    client = WebClient(token=config.bot_token_id)

    # 모든 행을 조회하여 슬랙 다이렉트 메시지 전송
    
    for row in values:
        slack_id = row[1]
        message_content = row[2]
        
        try:
            response = client.chat_postMessage(
                channel=slack_id,
                text=f"금주 1on1 매칭 대상은 {message_content}입니다"
            )
            # print(f"Message sent to {slack_id}: {message_content}")
        except SlackApiError as e:
            print(f"Error sending message to {slack_id}: {e.response['error']}")
    """
    

def notify_deposit_info():
    user1 = config.deposity_user1_id
    user2 = config.deposity_user2_id
    user3 = config.deposity_user3_id
    channel_id = config.deposit_channel_id
    deposit_df = extract_deposit_df()
    send_slack_message(channel_id, "예금 정보를 조회 중입니다...\n")
    deposit_df['만기일'] = pd.to_datetime(deposit_df['만기일'])
    # 현재 날짜와 만기일이 4일 이내인 행 필터링
    today = datetime.now()
    threshold_date = today + timedelta(days=4)
    filtered_df = deposit_df[deposit_df['만기일'] <= threshold_date]
    if filtered_df.empty:
        send_slack_message(channel_id, "3일 이내로 만기 예정된 상품이 없습니다")
    else:
        send_slack_message(channel_id, f"<@{user1}> <@{user2}> <@{user3}> 3일 이내로 만기 예정된 상품의 정보는 다음과 같습니다\n{filtered_df}")

if __name__ == "__main__":
    notify_deposit_info()

"""
# 스케줄러 기능 활성화 하는 방법
schedule.every().day.at("08:00").do(notify_today_vacation_info())

# 스케줄러 실행
while True:
    schedule.run_pending()
    time.sleep(1)
"""
