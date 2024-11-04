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
    # essential part 
    today_vacation_data = get_today_vacation_data(spreadsheet_id, json_keyfile_path)

    # Debug - print
    # for data in today_vacation_data:
    #     print(data)
    
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
            
    

def notify_one_by_one_partner():
    # 14일 이상 차이가 나지 않은 경우에는 아무것도 하지 않음
    if not is_valid_week_oneByone():
        print('not valid. Nothing created')
        # names = get_name_list_from_json()
        # for name in names:
        #     print(name)
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

    # Debug-print
    # print("Completed")

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
                f"이번주는  {partner_name}와(과) 함께 피드백을 주고 받으면 어떨까요?\n"
                f"1on1을 어떻게 해야 하는지 막막하다면, 아래 링크의 'KV 사람들이 말하는 법'을 참고하시기 바랍니다.\n"
                f"https://kakaoventures.oopy.io/how-to-speak \n"
                f"꼭 레몬베이스에 기록하는 것 잊지 마시고요.금주 1on1 매칭 대상은 {partner_name}입니다"
            )
        except SlackApiError as e:
            print(f"Error sending message to {slack_id}: {e.response['error']}")

def notify_pending_payments_per_month():
    # 데이터 업데이트 및 조회
    update_deposit_df()
    result = get_pending_payments_per_month()

    total_sum = 0
    send_slack_message(config.deposit_channel_id, "월별 미수 금액 리스트를 출력합니다")

    # 결과 데이터 순회
    for data in result:
        current_date = datetime.now().strftime('%Y-%m-%d')
        # ['우리은행  정기예금 1020-867-606019', '1,000,000,000', '3.69%', '2024-06-13', '2024-08-01', '49', '4940163.934']
        
        if current_date == data[4]:
            # 데이터를 형식화하여 출력
            bank_info = data[0]
            principal_amount = int(data[1].replace(',', ''))
            interest_rate = data[2]
            start_date = data[3]
            end_date = data[4]
            days = data[5]
            pending_amount = float(data[6])
            pending_amount = math.floor(pending_amount)

            # 깔끔하게 형식화된 출력 문자열 작성
            formatted_message = (
                f"은행 정보: {bank_info}\n"
                f"원금: {principal_amount:,.0f}원\n"
                f"이자율: {interest_rate}\n"
                f"시작일: {start_date}\n"
                f"계산 기준일: {end_date}\n"
                f"일수: {days}일\n"
                f"미수 금액: {pending_amount:,.0f}원"
                f"\n"
            )

            # print(formatted_message)

            # 슬랙으로 메시지 전송
            send_slack_message(config.deposit_channel_id, formatted_message)

            # 총 합산 금액 계산
            total_sum += pending_amount

    # 총 미수 금액을 출력
    final_message = f"총 미수 금액: {total_sum:,.0f}원"
    # print(final_message)
    send_slack_message(config.deposit_channel_id, final_message)

def notify_pending_payments_per_quarter():
    all_data = get_pending_payments_per_quarter()
    total_sum = 0

    send_slack_message(config.deposit_channel_id, "분기별 미수 금액 리스트를 출력합니다")

    for element in all_data:
        if isinstance(element, dict) and "data" in element:
            data = element["data"]
            current_date = datetime.now().strftime('%Y-%m-%d')

            for each_data in data:
                # print(each_data)

                if current_date == each_data[4]:
                # 데이터를 형식화하여 출력
                    bank_info = each_data[0]
                    principal_amount = int(each_data[1].replace(',', ''))
                    interest_rate = each_data[2]
                    start_date = each_data[3]
                    end_date = each_data[4]
                    days = each_data[5]
                    pending_amount = float(each_data[6])
                    pending_amount = math.floor(pending_amount)

                    # 깔끔하게 형식화된 출력 문자열 작성
                    formatted_message = (
                        f"은행 정보: {bank_info}\n"
                        f"원금: {principal_amount:,.0f}원\n"
                        f"이자율: {interest_rate}\n"
                        f"시작일: {start_date}\n"
                        f"계산 기준일: {end_date}\n"
                        f"일수: {days}일\n"
                        f"미수 금액: {pending_amount:,.0f}원"
                        f"\n"
                    )

                    # print(formatted_message)

                    # 슬랙으로 메시지 전송
                    send_slack_message(config.deposit_channel_id, formatted_message)
                    # 총 합산 금액 계산
                    total_sum += pending_amount

    # 총 미수 금액을 출력
    final_message = f"총 미수 금액: {total_sum:,.0f}원"
    # print(final_message)
    send_slack_message(config.deposit_channel_id, final_message)


def notify_deposit_info():
    user1 = config.deposity_user1_id
    user2 = config.deposity_user2_id
    user3 = config.deposity_user3_id
    #channel_id = config.deposit_channel_id
    channel_id = "C07ETQP9HJB" ## 임시 테스트용 채널 (제로,에스더 채팅방)
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
    # notify_deposit_info()
    # notify_pending_payments_per_month()
    # notify_pending_payments_per_quarter()

"""
# 스케줄러 기능 활성화 하는 방법
schedule.every().day.at("08:00").do(notify_today_vacation_info())

# 스케줄러 실행
while True:
    schedule.run_pending()
    time.sleep(1)
"""
