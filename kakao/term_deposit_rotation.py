from formatting import process_user_input, get_proper_file_name
import googleapi
import gspread
import chatgpt
import json
import requests
from config import intern_channel_id, executives_channel_id, management_channel_id, advisor_id

def deposit_rotation_system_handler(message, say, user_states):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        say(f"<@{user_id}> 정기예금 회전 시스템을 종료합니다.\n")
        del user_states[user_id]
    else:
        if user_input.isdigit():
            if user_input == "1": ## 휴가신청시스템
                say(f"<@{user_id}> 1 공사중 종료합니다\n")
                del user_states[user_id]
            elif user_input == "2": ## 보안시스템
                say(f"<@{user_id}> 2 공사중 종료합니다\n")
                del user_states[user_id]
            elif user_input == "3": ## 문서 4종 생성
                say(f"<@{user_id}> 3 공사중 종료합니다\n")
                del user_states[user_id]
            else:
                say(f"<@{user_id}> 잘못된 숫자를 입력했습니다. 다시 입력해주세요.\n")
                user_states[user_id] = 'deposit_rotation_waiting_only_number'
        else:
            say(f"<@{user_id}> 숫자만 입력해주세요. 다시 입력해주세요.")
            user_states[user_id] = 'deposit_rotation_waiting_only_number'