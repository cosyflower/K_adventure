import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import googleapi
import chatgpt
import re
import time
import json
import config
import schedule
import time
import threading
from user_commend import docx_generate, security_system, vacation_system_list, call_slack_bot, term_deposit_rotation_list, one_and_one # 사용자 명령어 DB

from document4create import docx_generating_company_name_handler, docx_generating_inv_choice_handler #, docx_generating_docx_category_handler

from security_system import security_system_user_function_handler, security_system_authority_category_handler, security_system_authority_update_json_file_handler, security_system_advisor_authority_make_handler, security_system_advisor_authority_delete_handler, get_user_authority, update_authority

from rosebot import rose_bot_handler
from term_deposit_rotation import deposit_rotation_system_handler, deposit_rotation_system_low_model_handler, deposit_rotation_system_high_model_handler
# Testing for vacation
from notification import notify_today_vacation_info, notify_deposit_info, notify_one_by_one_partner
from formatting import process_user_input
from googleVacationApi import request_vacation_handler, cancel_vacation_handler, vacation_purpose_handler
from directMessageApi import send_direct_message_to_user
from config import dummy_vacation_directory_id
from onebyone import find_oneByone_handler, update_spreadsheet_on_oneByone, match_people, get_name_list_from_json, find_oneByone
# slack bot system


# testing for validating on generating docx
import gspread
import datetime

def check_the_user_purpose(user_input,user_id):
    user_input = user_input.replace(" ","")
    if user_input in docx_generate:
        return docx_generate[0]
    elif user_input in vacation_system_list:
        return vacation_system_list[0]
    elif user_input in security_system:
        return security_system[0]
    elif user_input in call_slack_bot:
        return call_slack_bot[0]
    elif user_input in term_deposit_rotation_list:
        return term_deposit_rotation_list[0]
    elif user_input in one_and_one:
        return one_and_one[0]
    else:
        return chatgpt.analyze_user_purpose(user_input)


app = App(token=config.bot_token_id)

# Scheduler 관련 함수 정의
# 평일 오전 8시에 notify_today_vacation_info 함수 실행
schedule.every().monday.at("08:00").do(notify_today_vacation_info)
schedule.every().tuesday.at("08:00").do(notify_today_vacation_info)
schedule.every().wednesday.at("08:00").do(notify_today_vacation_info)
schedule.every().thursday.at("08:00").do(notify_today_vacation_info)
schedule.every().friday.at("08:00").do(notify_today_vacation_info)

# schedule.every().day.at("08:00").do(notify_deposit_info)

# 시트 생성 후 다이렉트 메세지 전송시도하지 않은 상태 (실제 배포시 테스트 진행하기)
schedule.every().monday.at("08:00").do(notify_one_by_one_partner)

# 스케줄러 실행 함수
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

#slack_bot에 사용되는 변수
user_states = {}
user_input_info = {}

#문서 4종 생성에 사용되는 변수
inv_list_info = {}
inv_info = {}

# 보안 시스템에 사용되는 변수
security_system_user_info_list = {}
security_system_advisor_user_info_list = {}

# 연차 프로세스를 실행한 적 없을 때 딕셔너리 내 값 생성
user_vacation_status = {}
user_vacation_info = {}
# 휴가 취소 프로세스
cancel_vacation_status = {}

# 다이렉트 메시지에서만 호출되도록 필터링하는 함수
def message_im_events(event, next):
    if event.get("channel_type") == "im":
        next()

@app.event("message", middleware=[message_im_events])
def handle_message_events(event, say):
    user_id = event['user']
    user_input = event['text']

    # Test - Should be deleted!!
    # test 용 함수 - "test" 입력하면 내가 원하는 함수 호출
    # if process_user_input(user_input) == 'test':
    #     notify_today_vacation_info()
    #     return

    if user_id not in user_states:
        user_purpose_handler(event, say) # 안내 문구 출력 - 알맞은 user_states[user_id] 배정하는 역할
    else: # 슬랙봇을 실행한 상황에 user_states[user_id]를 부여받은 상황일 때 진행
        #########################   문서4종시스템    ########################################
        if user_states[user_id] == 'docx_generating_waiting_company_name': 
            docx_generating_company_name_handler(event, say, user_states, inv_list_info, inv_info)
        elif user_states[user_id] == 'docx_generating_waiting_inv_choice':
            docx_generating_inv_choice_handler(event, say, user_states, inv_list_info, inv_info)
        # elif user_states[user_id] == 'docx_generating_waiting_docx_category':
        #     docx_generating_docx_category_handler(event, say, user_states, inv_list_info, inv_info)
        #########################   보안시스템    ########################################
        elif user_states[user_id] == 'security_system_waiting_function_number':
            security_system_user_function_handler(event, say, user_states, security_system_user_info_list, security_system_advisor_user_info_list)
        elif user_states[user_id] == 'security_system_waiting_authority_category':
            security_system_authority_category_handler(event, say, user_states, security_system_user_info_list, security_system_advisor_user_info_list)
        elif user_states[user_id] == 'security_system_json_file':
            security_system_authority_update_json_file_handler(event, say, user_states, security_system_user_info_list, security_system_advisor_user_info_list)
        elif user_states[user_id] == 'security_system_advisor_authority_make':
            security_system_advisor_authority_make_handler(event, say, user_states, security_system_user_info_list, security_system_advisor_user_info_list)
        elif user_states[user_id] == 'security_system_advisor_authority_delete':
            security_system_advisor_authority_delete_handler(event, say, user_states, security_system_user_info_list, security_system_advisor_user_info_list)
        #########################   휴가시스템    ########################################
        elif user_states[user_id] == 'vacation_purpose_handler':
            vacation_purpose_handler(event, say, user_states, cancel_vacation_status, user_vacation_info, user_vacation_status)
        elif user_states[user_id] == 'request_vacation':
            request_vacation_handler(event, say, user_states, user_vacation_status, user_vacation_info)
        elif user_states[user_id] == 'cancel_vacation':
            cancel_vacation_handler(event, say, user_states, cancel_vacation_status)    
        ######################### 로제봇 시스템 ###################################
        elif user_states[user_id] == 'rosebot_waiting_only_number':
            rose_bot_handler(event, say, user_states)
        ######################### 정기예금 회전 시스템 ###################################
        elif user_states[user_id] == 'deposit_rotation_waiting_only_number':
            deposit_rotation_system_handler(event, say, user_states)
        elif user_states[user_id] == 'deposit_rotation_waiting_low_chatgpt_input':
            deposit_rotation_system_low_model_handler(event, say, user_states)
        # elif user_states[user_id] == 'deposit_rotation_waiting_high_chatgpt_input':
        #     deposit_rotation_system_high_model_handler(event, say, user_states)

# Function to handle channel messages with specific keywords
@app.event("message")
def handle_channel_messages(event, say):
    channel_type = event.get("channel_type")
    text = event.get("text")
    
    if channel_type != "im" and ("로제봇" in text or "도와줘" in text):
        channel_id = event['channel']
        say(text="DM으로 답변드리겠습니다.", channel=channel_id)
        user_purpose_handler(event, say)

# @app.event("message")
# def handle_message_events(body, logger):
#     logger.info(body)

@app.event("app_mention")
def handle_message_events(event, say):
    user_id = event['user']
    user_input = event['text']
    ### 사용자 명령어 인식 프로세스
    user_input = process_user_input(user_input)
    # send_direct_message_to_user(user_id, user_input)

def user_purpose_handler(message, say):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    purpose = check_the_user_purpose(user_input,user_id)

    if purpose == "문서 4종":
        if get_user_authority(user_id) < 3:
            msg = (f"문서 4종 생성을 진행합니다. 회사명을 입력해주세요 (종료를 원하시면 '종료'를 입력해주세요)")
            send_direct_message_to_user(user_id, msg)
            user_states[user_id] = 'docx_generating_waiting_company_name'
        else:
            msg = (f"<@{user_id}>님은 권한이 없습니다. 종료합니다")
            send_direct_message_to_user(user_id, msg)
    elif purpose == "보안시스템":
        if get_user_authority(user_id) < 4:
            msg = (f"보안시스템을 작동합니다. 원하는 기능의 번호를 입력해주세요. (번호만 입력해주세요) \n"
                "1. 전체 사용자 권한 조회\n"
                "2. 신규 사용자 권한 배정\n"
                "3. 내 권한 조회\n"
                "4. 권한이 변경된 사용자 조회([임시]관리자 전용)\n"
                "5. 권한 업데이트([임시]관리자 전용)\n"
                "6. 임시 관리자 배정(관리자 전용)\n"
                "7. 임시 관리자 목록 조회(관리자 전용)\n"
                "8. 임시 관리자 회수(관리자 전용)\n(종료를 원하시면 '종료'를 입력해주세요)"
                )
            send_direct_message_to_user(user_id, msg)
            user_states[user_id] = 'security_system_waiting_function_number'
        else:
            msg = (f"<@{user_id}> 권한이 없습니다. 종료합니다")
            send_direct_message_to_user(user_id, msg)
    elif purpose == "휴가신청시스템":
        if get_user_authority(user_id) < 4:
            msg = (f"휴가시스템을 작동합니다. 원하는 기능의 번호를 입력해주세요. (번호만 입력해주세요) \n"
                "1. 신청된 휴가 조회\n"
                "2. 신규 휴가 신청\n"
                "3. 기존 휴가 삭제\n"
                "4. 남은 휴가 일수 조회\n"
                "(종료를 원하시면 '종료'를 입력해주세요)"
                )
            send_direct_message_to_user(user_id, msg)
            user_states[user_id] = 'vacation_purpose_handler'
        else:
            msg = (f"<@{user_id}>님은 권한이 없습니다. 종료합니다")
            send_direct_message_to_user(user_id, msg)
    elif purpose == "로제봇":
        msg = ("슬랙봇 시스템을 작동합니다. 무엇을 도와드릴까요? 종료를 원한다면 \'종료\'를 입력해주세요\n"
            "1. 휴가 신청\n"
            "2. 보안 시스템\n"
            "3. 문서 작성\n"
            "4. 정기예금 회전 시스템\n"
            "5. 회수 상황판\n"
            "6. 검색\n"
            "7. 1on1\n"
        )
        send_direct_message_to_user(user_id, msg)
        user_states[user_id] = 'rosebot_waiting_only_number'
    elif purpose == "정기예금회전시스템":
        if get_user_authority(user_id) < 3:
            msg = ("정기예금 회전 시스템을 작동합니다. 종료를 원한다면 \'종료\'를 입력해주세요\n"
                    "1. 질문하기\n"
                    # "2. 질문하기(상위모델)\n"
                    # "3. 최종 만기일이 다가온 정기예금 상품조회\n"
                )
            send_direct_message_to_user(user_id, msg)
            user_states[user_id] = 'deposit_rotation_waiting_only_number'
            msg = "공사중...종료합니다"
            send_direct_message_to_user(user_id, msg)
        else:
            msg = (f"<@{user_id}>님은 권한이 없습니다. 종료합니다")
            send_direct_message_to_user(user_id, msg)
    elif purpose == "일대일미팅":
        if get_user_authority(user_id) < 4:
            # 바로 실행 - user_states[user_id] 반영하지 않음
            msg = (f"일대일매칭 기능을 진행합니다. 최신 매칭 대상을 조회합니다.\n")
            send_direct_message_to_user(user_id, msg)
            
            partner = find_oneByone(user_id)
            # # 삭제 예정
            # print(f"partner : {partner}")
            msg = (f"<@{user_id}>님의 매칭 대상은 : {partner}입니다. 일대일매칭 기능을 종료합니다\n")
            send_direct_message_to_user(user_id, msg)
        else:
            msg = (f"<@{user_id}>님은 권한이 없습니다. 종료합니다")
            send_direct_message_to_user(user_id, msg)
    else:
        msg = (f"없는 기능입니다. 다시 입력해주세요")
        send_direct_message_to_user(user_id, msg)

if __name__ == "__main__":
    update_authority()
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()
    SocketModeHandler(app,config.app_token_id).start()
    