
from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
import config

def send_direct_message_to_user(user_id, direct_message):
    # user_id = event['user']
    # user_input = event['text']
    client = WebClient(token=config.bot_token_id)
    try:
        # 다이렉트 메시지 전송
        response = client.chat_postMessage(
            channel=user_id,
            text=direct_message
        )
    except SlackApiError as e:
        error_message = client.chat_postMessage(
            channel = user_id,
            text = f"Error sending DM: {e.response['error']}"
        )