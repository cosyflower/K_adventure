import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import schedule
import time
import config
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from translator import format_vacation_data
from googleVacationApi import  get_today_vacation_data



def send_slack_message(channel_id, text):
    try:
        client = WebClient(token=config.bot_user_token_id)
        response = client.chat_postMessage(
            channel=channel_id,
            text=text
        )
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

def notify_today_vacation_info():
    channel_id = config.test_slack_channel_id
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

"""
# 매일 오전 8시에 notify_today_vacation_info 함수 실행
schedule.every().day.at("08:00").do(notify_today_vacation_info())

# 스케줄러 실행
while True:
    schedule.run_pending()
    time.sleep(1)
"""
