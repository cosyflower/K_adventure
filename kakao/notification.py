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
    channel_id = config.test_slack_second_channel_id
    spreadsheet_id = config.dummy_vacation_db_id
    json_keyfile_path = config.kakao_json_key_path

    send_slack_message(channel_id, "금일 휴가자 정보를 조회합니다. 잠시만 기다려주세요.\n")
    
    today_vacation_data = get_today_vacation_data(spreadsheet_id, json_keyfile_path)
    
    if len(today_vacation_data) == 0:
        send_slack_message(channel_id, "금일 휴가자 정보가 존재하지 않습니다. 금일 휴가 조회를 종료합니다")
        return
    
    formatted_vacation_data = format_vacation_data(today_vacation_data)
    
    for data in formatted_vacation_data:
        send_slack_message(channel_id, data)

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
