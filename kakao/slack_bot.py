import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import googleapi
import chatgpt
import re
import time
import json
import config
import schedule
import time
import threading
from user_commend import docx_generate, security_system, vacation_system_list, call_slack_bot, term_deposit_rotation_list # 사용자 명령어 DB

from document4create import docx_generating_company_name_handler, docx_generating_inv_choice_handler, docx_generating_docx_category_handler

from security_system import security_system_user_function_handler, security_system_authority_category_handler, security_system_authority_update_json_file_handler, security_system_advisor_authority_make_handler, security_system_advisor_authority_delete_handler, get_user_authority, is_fake_advisor, is_real_advisor, update_authority

from rosebot import rose_bot_handler
from term_deposit_rotation import deposit_rotation_system_handler
# Testing for vacation
from notification import notify_today_vacation_info
from formatting import process_user_input
from googleVacationApi import request_vacation_handler, cancel_vacation_handler, vacation_purpose_handler, get_remained_vacation, \
get_today_vacation_info

# slack bot system


# testing for validating on generating docx
import gspread
import datetime

"""
사용자로부터 입력을 받았을 때 처음으로 입력에 대한 분석이 진행되는 함수
- 토큰을 확인하고 그에 알맞은 문자열을 리턴하는 함수
"""
def check_the_user_purpose(user_input):
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
    else:
        print("chatgpt 사용 + 3원")
        return chatgpt.analyze_user_purpose(user_input)


app = App(token=config.bot_token_id)

# Scheduler 관련 함수 정의
# 매일 오전 8시에 notify_today_vacation_info 함수 실행
schedule.every().day.at("08:00").do(notify_today_vacation_info)

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

@app.event("message")
def handle_message_events(body, logger):
    # 이벤트로부터 메시지의 내용을 추출하고 로그로 기록합니다.
    logger.info(body)

@app.event("app_mention")
def handle_message_events(event, say):
    user_id = event['user']
    user_input = event['text']
    ### 사용자 명령어 인식 프로세스
    user_input = process_user_input(user_input)

    if user_id not in user_states:
        user_purpose_handler(event, say) # 안내 문구 출력 - 알맞은 user_states[user_id] 배정하는 역할
    else: # 슬랙봇을 실행한 상황에 user_states[user_id]를 부여받은 상황일 때 진행
        #########################   문서4종시스템    ########################################
        if user_states[user_id] == 'docx_generating_waiting_company_name': 
            docx_generating_company_name_handler(event, say, user_states, inv_list_info, inv_info)
        elif user_states[user_id] == 'docx_generating_waiting_inv_choice':
            docx_generating_inv_choice_handler(event, say, user_states, inv_list_info, inv_info)
        elif user_states[user_id] == 'docx_generating_waiting_docx_category':
            docx_generating_docx_category_handler(event, say, user_states, inv_list_info, inv_info)
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


def user_purpose_handler(message, say):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)

    purpose = check_the_user_purpose(user_input)

    if purpose == "문서 4종 생성해줘":
        if get_user_authority(user_id) < 3:
            say(f"<@{user_id}> 문서 4종 생성을 진행합니다. 회사명을 입력해주세요 (종료를 원하시면 '종료'를 입력해주세요)")
            user_states[user_id] = 'docx_generating_waiting_company_name'
        else:
            say(f"<@{user_id}> 권한이 없습니다.")
    elif purpose == "보안시스템 작동해줘":
        if get_user_authority(user_id) < 4:
            say(f"<@{user_id}> 보안시스템을 작동합니다. 원하는 기능의 번호를 입력해주세요. (번호만 입력해주세요) \n"
                "1. 전체 사용자 권한 조회\n"
                "2. 신규 사용자 권한 배정\n"
                "3. 내 권한 조회\n"
                "4. 권한이 변경된 사용자 조회([임시]관리자 전용)\n"
                "5. 권한 업데이트([임시]관리자 전용)\n"
                "6. 임시 관리자 배정(관리자 전용)\n"
                "7. 임시 관리자 목록 조회(관리자 전용)\n"
                "8. 임시 관리자 회수(관리자 전용)\n(종료를 원하시면 '종료'를 입력해주세요)"
                )
            user_states[user_id] = 'security_system_waiting_function_number'
        else:
            say(f"<@{user_id}> 권한이 없습니다.")
    elif purpose == "휴가 시스템 작동해줘":
        if get_user_authority(user_id) < 4:
            say(f"<@{user_id}> 휴가시스템을 작동합니다. 원하는 기능의 번호를 입력해주세요. (번호만 입력해주세요) \n"
                "1. 신청된 휴가 조회\n"
                "2. 신규 휴가 신청\n"
                "3. 기존 휴가 삭제\n"
                "4. 남은 휴가 일수 조회\n"
                "(종료를 원하시면 '종료'를 입력해주세요)"
                )
            user_states[user_id] = 'vacation_purpose_handler'
        else:
            say(f"<@{user_id}> 권한이 없습니다.")
    elif purpose == "로제봇 도와줘":
        say("슬랙봇 시스템을 작동합니다. 무엇을 도와드릴까요? 종료를 원한다면 \'종료\'를 입력해주세요\n"
            "1. 휴가 신청\n"
            "2. 보안 시스템\n"
            "3. 문서 작성\n"
            "4. 정기예금 회전 시스템\n"
            "5. 회수 상황판\n"
            "6. 검색\n"
            "7. 1on1\n"
        )
        user_states[user_id] = 'rosebot_waiting_only_number'
    elif purpose == "정기예금 회전시스템":
        say("정기예금 회전 시스템을 작동합니다. 종료를 원한다면 \'종료\'를 입력해주세요\n"
                "1. 질문하기(일반모델)(약 1원)\n"
                "2. 질문하기(상위모델)(약 10원)\n"
                "3. 최종 만기일이 다가온 정기예금 상품조회\n"
            )
        user_states[user_id] = 'deposit_rotation_waiting_only_number'
    else:
        say(f"<@{user_id}> 없는 기능입니다. 다시 입력해주세요")

if __name__ == "__main__":
    update_authority()
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()
    SocketModeHandler(app,config.app_token_id).start()
    