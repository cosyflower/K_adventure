
from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
import config

def send_direct_message(user_id, direct_message):
    # user_id = event['user']
    # user_input = event['text']
    print("호출시작\n")
    client = WebClient(token=config.bot_token_id)
    try:
        # 다이렉트 메시지 전송
        response = client.chat_postMessage(
            channel=user_id,
            text=direct_message
        )
        print("호출완료\n")
    except SlackApiError as e:
        error_message = client.chat_postMessage(
            channel = user_id,
            text = f"Error sending DM: {e.response['error']}"
        )