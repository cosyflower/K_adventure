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
from onebyone import get_or_create_1on1_spreadsheet, get_spreadsheet_service, find_spreadsheet_in_shared_drive, update_spreadsheet_on_oneByone, match_people, get_name_list_from_json, is_valid_week_oneByone
from security_system import update_authority
import pandas as pd
import json
from directMessageApi import send_direct_message_to_user
from term_deposit_rotation import get_pending_payments_per_month, get_pending_payments_per_quarter, update_deposit_df
import math


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
    today_vacation_data = get_today_vacation_data(spreadsheet_id, json_keyfile_path)

    # Vacation requested and transformed
    formatted_vacation_data = format_vacation_data(today_vacation_data)
    client = WebClient(token=config.bot_token_id)

    # user_info and authority <= 3
    with open("users_info.json", 'r', encoding='utf-8') as file:
        users_data = json.load(file)

    # bot admin이 반영되어 있지 않은 애들만 append()
    # 권한이 3이하인 사람들만 반영한다
    user_ids = []
    for id in users_data:
        name = users_data[id].get('name')
        if users_data[id].get('authority') <= 3 and 'bot' not in name and 'admin' not in name:
            user_ids.append(users_data[id].get('id'))

    # dm to all users
    if len(today_vacation_data) == 0:
        vacation_msg = ":palm_tree:연차 사용이 없는 날입니다. 다들 좋은 하루 되셔요!"
    else:
        formatted_data = '\n'.join(formatted_vacation_data)
        vacation_msg = f":palm_tree:금일 휴가자 명단입니다\n\n{formatted_data}"

    for slack_id in user_ids:
        try:
            response = client.chat_postMessage(
                channel=slack_id,
                text= vacation_msg
            )
        except SlackApiError as e:
            print(f"Error sending message to {slack_id}: {e.response['error']}")
    
    print("휴가 DM 보내기 완료! 배포 결과를 확인하세요!!")

def notify_one_by_one_partner():
    # 14일 이상 차이가 나지 않은 경우에는 아무것도 하지 않음
    if not is_valid_week_oneByone():
        return

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
    client = WebClient(token=config.bot_token_id)

    # 모든 행을 조회하여 슬랙 다이렉트 메시지 전송
    for row in values:
        slack_id = row[1]
        partner_name = row[2]
        
        try:
            response = client.chat_postMessage(
                channel=slack_id,
                text=f"안녕하세요, 이번주 금요일에 진행할 1on1 미팅 안내 드립니다.\n"
                f"이번주는 Esther와(과) 함께 피드백을 주고 받으면 어떨까요?\n"
                f"1on1을 어떻게 해야 하는지 막막하다면, 아래 링크의 'KV 사람들이 말하는 법'을 참고하시기 바랍니다.\n"
                f"https://kakaoventures.oopy.io/how-to-speak \n"
                f"꼭 레몬베이스에 기록하는 것 잊지 마시고요.금주 1on1 매칭 대상은 {partner_name}입니다"
            )
        except SlackApiError as e:
            print(f"Error sending message to {slack_id}: {e.response['error']}")

    print("1on1 DM 보내기 완료! 배포 결과를 확인하세요!!")

def notify_pending_payments_per_month():
    # ['우리은행  정기예금 1020-867-606019', '1,000,000,000', '3.69%', '2024-06-13', '2024-08-01', '49', '4940163.934']
    update_deposit_df()
    result = get_pending_payments_per_month()
    
    # result에 담긴 데이터를 하나씩 순회합니다
    # 각 데이터를 한번씩 출력합니다
    # 각 데이터의 6번째 값들의 합을 구합니다. 이 때 값에 소수점이 있는 경우 내림을 취하고 합을 구합니다
    # 6번째 값들의 합은 순회를 마친 다음 최종적으로 1번 출력합니다 
    # 최종 출력 멘트는 "현재일을 기준으로 미수금액의 총합은 {합}입니다" 로 작성합니다
    # 6번째 값들의 합을 구하기 위한 변수 초기화
    total_sum = 0
    send_slack_message(config.deposit_channel_id, "월별 미수 금액 리스트를 출력합니다")

    # result에 담긴 데이터를 하나씩 순회합니다
    for data in result:
        # 각 데이터를 한번씩 출력합니다
        # ['우리은행  정기예금 1020-867-606019', '1,000,000,000', '3.69%', '2024-06-13', '2024-08-01', '49', '4940163.934']
        current_date = datetime.now().strftime('%Y-%m-%d')
        if current_date == data[3]:
            
            print(data)

            send_slack_message(config.deposit_channel_id, data)
            # 각 데이터의 6번째 값 (인덱스로는 5번째)을 가져옵니다
            amount = float(data[6])
            # 소수점이 있는 경우 내림을 취합니다
            amount = math.floor(amount)
            # 값을 합산합니다
            total_sum += amount

    # print(total_sum)
    send_slack_message(config.deposit_channel_id, f"현재일을 기준으로 미수금액의 총합은 {"{:,}".format(total_sum)}입니다")

def notify_pending_payments_per_quarter():
    all_data = get_pending_payments_per_quarter()
    total_sum = 0

    send_slack_message(config.deposit_channel_id, "분기별 미수 금액 리스트를 출력합니다")

    for element in all_data:
        if isinstance(element, dict) and "data" in element:
            data = element["data"]
            current_date = datetime.now().strftime('%Y-%m-%d')
            if data and current_date == data[3]:
                send_slack_message(config.deposit_channel_id, data)
                # if data:  # data 리스트가 비어있지 않다면
                last_row = data[-1]  # 마지막 행을 가져옴
                last_value = float(last_row[-1])  # 마지막 값을 가져옴 (소수점 처리 가능성 고려)
                # 소수일 경우 내림 처리
                last_value = math.floor(last_value)
                # 합계에 더하기
                total_sum += last_value
    
    send_slack_message(config.deposit_channel_id, f"현재일을 기준으로 미수금액의 총합은  {"{:,}".format(total_sum)}입니다")


def notify_deposit_info():
    user1 = config.deposity_user1_id
    user2 = config.deposity_user2_id
    user3 = config.deposity_user3_id
    channel_id = config.deposit_channel_id
    deposit_df = extract_deposit_df()
    send_slack_message(channel_id, "예금 정보를 조회 중입니다...\n")
    deposit_df['만기일'] = pd.to_datetime(deposit_df['만기일'])
    today = datetime.now()
    is_friday = today.weekday() == 4
    if is_friday:
        threshold_dates = [today + timedelta(days=i) for i in range(4, 7)]
        filtered_df = deposit_df[deposit_df['만기일'].isin(threshold_dates)]
    else:
        threshold_date = today + timedelta(days=4)
        filtered_df = deposit_df[deposit_df['만기일'] == threshold_date]
    if filtered_df.empty:
        send_slack_message(channel_id, "4일 이내로 만기 예정된 상품이 없습니다")
    else:
        send_slack_message(channel_id, f"<@{user1}> <@{user2}> <@{user3}> 4일 이내로 만기 예정된 상품의 정보는 다음과 같습니다\n{filtered_df}")

# if __name__ == "__main__":
#     # notify_deposit_info()
#     # notify_pending_payments_per_month()
#     notify_pending_payments_per_quarter()

"""
# 스케줄러 기능 활성화 하는 방법
schedule.every().day.at("08:00").do(notify_today_vacation_info())

# 스케줄러 실행
while True:
    schedule.run_pending()
    time.sleep(1)
"""
