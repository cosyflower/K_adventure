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
import calendar
import gspread

from user_commend import docx_generate, security_system, vacation_system_list, call_slack_bot, term_deposit_rotation_list, one_and_one, hr_and_admin_list, ocr_system_list # 사용자 명령어 DB

from document4create import docx_generating_company_name_handler, docx_generating_inv_choice_handler #, docx_generating_docx_category_handler

from security_system import security_system_user_function_handler, security_system_authority_category_handler, security_system_authority_update_json_file_handler, security_system_advisor_authority_make_handler, security_system_advisor_authority_delete_handler, get_user_authority, update_authority

from rosebot import rose_bot_handler
from term_deposit_rotation import deposit_rotation_system_handler, deposit_rotation_system_low_model_handler#, deposit_rotation_system_high_model_handler
# Testing for vacation
from notification import notify_today_vacation_info, notify_deposit_info, notify_one_by_one_partner
from formatting import process_user_input
from googleVacationApi import request_vacation_handler, cancel_vacation_handler, vacation_purpose_handler
from directMessageApi import send_direct_message_to_user
from config import dummy_vacation_directory_id
from onebyone import find_oneByone_handler, update_spreadsheet_on_oneByone, match_people, get_name_list_from_json, find_oneByone
from notification import notify_pending_payments_per_month, notify_pending_payments_per_quarter, send_slack_message
from ocr import ocr_transform_handler
from ocr_view import check_yes_or_no_init
from slack_view import execute_rosebot_by_button
# testing for validating on generating docx
from datetime import datetime, timedelta

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
    elif user_input in hr_and_admin_list:
        return hr_and_admin_list[0]
    elif user_input in ocr_system_list:
        return ocr_system_list[0]
    else:
        return chatgpt.analyze_user_purpose(user_input)


app = App(token=config.bot_token_id)
client = app.client

# Terminated
# 추가된 변수 - 봇의 활성 상태를 관리
is_bot_active = True

# 수정된 데코레이터 정의
def check_bot_active(func):
    def wrapper(event, say, *args, **kwargs):
        global is_bot_active
        user_id = event.get("user")
        user_input = event.get("text", "").strip()

        # 비활성화 상태에서 "활성화" 명령을 관리자가 입력한 경우 예외적으로 처리
        # 관리자는 유저 아이디 정보를 활용해서 진행하면 됨
        if not is_bot_active and user_input == "활성화" and user_id == 'U05R7FD8Y85':
            is_bot_active = True
            say(f"<@{user_id}> 님, 로제봇이 다시 활성화되었습니다.")
            return
        
        # 비활성화 상태일 때는 종료 메시지 출력
        if not is_bot_active:
            say(f"<@{user_id}>님, 현재 로제봇이 종료된 상태입니다. 관리자에게 문의해주세요.")
            return
        
        # 활성화 상태일 때만 원래 함수 실행
        return func(event, say, *args, **kwargs)
    return wrapper

# Scheduler 관련 함수 정의
# 평일 오전 8시에 notify_today_vacation_info 함수 실행

schedule.every().monday.at("08:00").do(notify_today_vacation_info)
schedule.every().tuesday.at("08:00").do(notify_today_vacation_info)
schedule.every().wednesday.at("08:00").do(notify_today_vacation_info)
schedule.every().thursday.at("08:00").do(notify_today_vacation_info)
schedule.every().friday.at("08:00").do(notify_today_vacation_info)

schedule.every().monday.at("08:00").do(notify_deposit_info)
schedule.every().tuesday.at("08:00").do(notify_deposit_info)
schedule.every().wednesday.at("08:00").do(notify_deposit_info)
schedule.every().thursday.at("08:00").do(notify_deposit_info)
schedule.every().sunday.at("08:00").do(notify_deposit_info)

# 2주마다 월요일 오]전 8시에 작업을 실행하도록 스케줄 설정
schedule.every().monday.at("08:00").do(notify_one_by_one_partner)

# notify_pending_payments_per_month() 함수를 월말에 알림
# notify_pending_payments_per_quarter() 함수를 3,6,9,12월말에 알림
def is_last_day_of_month():
    today = datetime.today()
    last_day_of_month = calendar.monthrange(today.year, today.month)[1]
    return today.day == last_day_of_month

def is_last_day_of_quarter():
    # 오늘이 분기말인지 확인 (3, 6, 9, 12월의 말일)
    today = datetime.today()
    if today.month in [3, 6, 9, 12]:
        # 해당 월의 마지막 날 계산
        last_day_of_month = calendar.monthrange(today.year, today.month)[1]
        return today.day == last_day_of_month
    return False

# 스케줄 설정 - per month 8:00
schedule.every().day.at("08:00").do(
    lambda: notify_pending_payments_per_month() if is_last_day_of_month() else None
)

# per quarter 8:00
schedule.every().day.at("08:00").do(
    lambda: notify_pending_payments_per_quarter() if is_last_day_of_quarter() else None
)

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
# 사용자의 응답을 저장할 딕셔너리
user_responses = {}

class StateManager:
    def __init__(self, global_states):
        self.global_states = global_states

    # Generic methods to handle state
    def set_state(self, category, user_id, state):
        """Set a state for a specific user under a given category."""
        if category not in self.global_states:
            raise KeyError(f"Invalid category: {category}")
        self.global_states[category][user_id] = state

    def get_state(self, category, user_id):
        """Get the state of a specific user under a given category."""
        if category not in self.global_states:
            raise KeyError(f"Invalid category: {category}")
        return self.global_states[category].get(user_id)

    def remove_state(self, category, user_id):
        """Remove the state of a specific user under a given category."""
        if category not in self.global_states:
            raise KeyError(f"Invalid category: {category}")
        self.global_states[category].pop(user_id, None)

    def get_all_states(self, category):
        """Get all states under a given category."""
        if category not in self.global_states:
            raise KeyError(f"Invalid category: {category}")
        return self.global_states[category]

    def clear_category(self, category):
        """Clear all states in a category."""
        if category not in self.global_states:
            raise KeyError(f"Invalid category: {category}")
        self.global_states[category].clear()

    def delete_category(self, category):
        """Delete a whole category from global_states."""
        if category not in self.global_states:
            raise KeyError(f"Invalid category: {category}")
        del self.global_states[category]

    def clear_all_states(self):
        """Clear all states in global_states."""
        self.global_states.clear()

global_states = {
    "user_states": user_states,
    "user_input_info": user_input_info,
    "inv_list_info": inv_list_info,
    "inv_info": inv_info,
    "security_system_user_info_list": security_system_user_info_list,
    "security_system_advisor_user_info_list": security_system_advisor_user_info_list,
    "user_vacation_status": user_vacation_status,
    "user_vacation_info": user_vacation_info,
    "cancel_vacation_status": cancel_vacation_status,
    "user_responses": user_responses,
}

state_manager = StateManager(global_states)

# 다이렉트 메시지에서만 호출되도록 필터링하는 함수
def message_im_events(event, next):
    if event.get("channel_type") == "im":
        next()

# 예 / 아니오 셀렉션 액션 만들기
@app.action("yes_button_init") # action_id - make each handler
def handle_yes_action_init(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    # 사용자의 응답을 저장 (True)
    user_responses[user_id] = True
    say(f"<@{user_id}> 님, OCR 프로그램을 시작합니다.")

    user_states[user_id] = 'ocr_1_or_2'
    ocr_transform_handler(message, say, user_states, client, user_responses, channel_id, user_id, '')
    
@app.action("no_button_init")
def handle_no_action_init(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    say(f"<@{user_id}> 님, OCR 프로그램을 종료합니다.")
    # 사용자의 응답을 저장 (False)
    user_responses[user_id] = False
    # 프로그램 종료 로직을 여기에 추가

    # 유저 상태에서 정보를 제거해야 함 
    if user_id in user_states:
        del user_states[user_id]

@app.action("yes_button_progress") # action_id - make each handler
def handle_yes_action_init(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    # 사용자의 응답을 저장 (True)
    user_responses[user_id] = True
    # 버튼 누르면 바로 나오는 문장은 바로 아래 코드
    say(f"<@{user_id}> 님, OCR 프로그램을 진행합니다.")

    user_states[user_id] = 'ocr_progress'
    ocr_transform_handler(message, say, user_states, client, user_responses, channel_id, user_id, '')
    
@app.action("no_button_progress")
def handle_no_action_init(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    say(f"<@{user_id}> 님, OCR 프로그램을 종료합니다.")
    # 사용자의 응답을 저장 (False)
    user_responses[user_id] = False
    # 프로그램 종료 로직을 여기에 추가
    if user_id in user_states:
        del user_states[user_id]

# ----------------------------
# _________ROSEBOT____________
@app.action("rosebot_1_id") # action_id - make each handler
def rosebot_1_ack(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    # 버튼 누르면 바로 나오는 문장은 바로 아래 코드
    say(f"<@{user_id}> 님, 휴가신청 시스템을 진행합니다.")

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

        # event와 유사한 구조의 데이터 생성
        # handle_message_events()에 전달할 가상 텍스트
        event = {
            "type": "message",
            "user": user_id,
            "text": "vacation", 
            "channel": channel_id
        }
        handle_message_events(event, say)
    else:
        msg = (f"<@{user_id}>님은 권한이 없습니다. 종료합니다")
        send_direct_message_to_user(user_id, msg)
        if user_id in user_states:
            del user_states[user_id]
    
@app.action("rosebot_2_id")
def rosebot_2_ack(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    if get_user_authority(user_id) < 3:
        msg = ("인사 총무 기능을 진행합니다. *아래의 링크를 확인하세요*\n"
                "https://forms.gle/xWeE1qWNCjLrrBob7"
                )
        send_direct_message_to_user(user_id, msg)
        if user_id in user_states:
            del user_states[user_id]
    else:
        msg = (f"<@{user_id}>님은 권한이 없습니다. 종료합니다")
        send_direct_message_to_user(user_id, msg)
        if user_id in user_states:
            del user_states[user_id]

@app.action("rosebot_3_id")
def rosebot_3_ack(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    if get_user_authority(user_id) < 3:
        msg = (f"문서 4종 생성을 진행합니다. 회사명을 입력해주세요 (종료를 원하시면 '종료'를 입력해주세요)")
        send_direct_message_to_user(user_id, msg)
        user_states[user_id] = 'docx_generating_waiting_company_name'
        
        # event와 유사한 구조의 데이터 생성
        # handle_message_events()에 전달할 가상 텍스트
        event = {
            "type": "message",
            "user": user_id,
            "text": "document4_creation", 
            "channel": channel_id
        }
        handle_message_events(event, say)

    else:
        msg = (f"<@{user_id}>님은 권한이 없습니다. 종료합니다")
        send_direct_message_to_user(user_id, msg)
        if user_id in user_states:
            del user_states[user_id]

@app.action("rosebot_4_id")
def rosebot_4_ack(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    if get_user_authority(user_id) < 2:
        msg = ("정기예금 회전 시스템을 작동합니다. 종료를 원한다면 \'종료\'를 입력해주세요\n"
            "1. 질문하기\n"
            # "2. 질문하기(상위모델)\n"
            # "3. 최종 만기일이 다가온 정기예금 상품조회\n"
            )
        send_direct_message_to_user(user_id, msg)
        user_states[user_id] = 'deposit_rotation_waiting_only_number'
        # msg = "공사중...종료합니다"
        # send_direct_message_to_user(user_id, msg)
        event = {
            "type": "message",
            "user": user_id,
            "text": "Deposit_Rotation", 
            "channel": channel_id
        }
        handle_message_events(event, say)
    else:
        msg = (f"<@{user_id}>님은 권한이 없습니다.")
        send_direct_message_to_user(user_id, msg)
        if user_id in user_states:
            del user_states[user_id]

@app.action("rosebot_5_id")
def rosebot_5_ack(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    msg = (f"공사중입니다. 종료합니다.\n")
    send_direct_message_to_user(user_id, msg)
    if user_id in user_states:
        del user_states[user_id]
        
@app.action("rosebot_6_id")
def rosebot_6_ack(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    msg = (f"공사중입니다. 종료합니다\n")
    send_direct_message_to_user(user_id, msg)
    if user_id in user_states:
        del user_states[user_id]

@app.action("rosebot_7_id")
def rosebot_7_ack(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    if get_user_authority(user_id) < 3:
        msg = (f"일대일매칭 기능을 진행합니다. 최신 매칭 대상을 조회합니다.\n")
        send_direct_message_to_user(user_id, msg)
        partner = find_oneByone(user_id)
        msg = (f"<@{user_id}>님의 매칭 대상은 : {partner}입니다. 일대일매칭 기능을 종료합니다\n")
        send_direct_message_to_user(user_id, msg)
        if user_id in user_states:
            del user_states[user_id]
    else:
        msg = (f"<@{user_id}>님은 권한이 없습니다.")
        send_direct_message_to_user(user_id, msg)
        if user_id in user_states:
            del user_states[user_id]

@app.action("rosebot_8_id")
def rosebot_8_ack(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    if get_user_authority(user_id) < 4:
        msg = (f"보안시스템을 작동합니다. 원하는 기능의 번호를 입력해주세요. (번호만 입력해주세요) \n"
            "1. 전체 사용자 권한 조회\n"
            "2. 신규 사용자 권한 배정\n"
            "3. 내 권한 조회\n"
            "4. 권한이 변경된 사용자 조회([임시]운영자 전용)\n"
            "5. 권한 업데이트([임시]운영자 전용)\n"
            "6. 임시 운영자 배정(운영자 전용)\n"
            "7. 임시 운영자 목록 조회(운영자 전용)\n"
            "8. 임시 운영자 회수(운영자 전용)\n(종료를 원하시면 '종료'를 입력해주세요)"
            )
        send_direct_message_to_user(user_id, msg)
        user_states[user_id] = 'security_system_waiting_function_number'

        event = {
            "type": "message",
            "user": user_id,
            "text": "Security_Sytem", 
            "channel": channel_id
        }

        handle_message_events(event, say)
    else:
        msg = (f"<@{user_id}>님은 권한이 없습니다. 종료합니다")
        send_direct_message_to_user(user_id, msg)
        if user_id in user_states:
            del user_states[user_id]

@app.action("rosebot_9_id")
def rosebot_9_ack(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    user_responses[user_id] = None  # 초기화
    msg = (f"*[주의] OCR program의 주의사항은 다음과 같습니다.*\n"
            "0. https://drive.google.com/drive/folders/1jO0EZViYdpuCgChcD_g1zwcTVYq-7321\n"
            "1. 현재 날짜를 기준으로 *위 링크*의 폴더를 탐색합니다. ex) 2024-10-03 -> 24년_3분기_등기부등본\n"
            "2. 파일명의 구성은 회사 이름을 시작으로 '_'로 구분되어야 합니다. ex) 라포랩스_재무제표.. \n"
            "3. 회사 이름에 오타가 없는지 다시 한번 확인해주세요. 약식명, 풀네임을 기준으로 회사를 검색합니다.\n"
            "4. 폴더에 파일을 올바르게 넣었는지 확인하세요. 링크의 구글 드라이브 내 문서 종류 맞게 넣어야 합니다.\n"
            "5. OCR 기능이 진행되는 동안 다른 기능을 추가로 실행할 수 없습니다. 실행 시 주의 사항을 확인하며 진행해주세요.\n"
            )
    send_direct_message_to_user(user_id, msg)
    check_yes_or_no_init(user_id, channel_id, client, content='OCR 프로그램을 시작하시겠습니까?')


# -----------------------
# _________OCR___________
@app.action("OCR_1_JUDY")
def ocr_1(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    user_states[user_id] = 'ocr_handler'
    user_responses[user_id] = 'OCR_1'
    say(f"<@{user_id}> 님, OCR 1을 실행합니다. 잠시만 기다려주세요...")

    ocr_transform_handler(message, say, user_states, client, user_responses, channel_id, user_id, '')

@app.action("OCR_2_BEN")
def ocr_2(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    user_states[user_id] = 'ocr_handler'
    user_responses[user_id] = 'OCR_2'
    say(f"<@{user_id}> 님, OCR 2를 실행합니다. 잠시만 기다려주세요...")

    ocr_transform_handler(message, say, user_states, client, user_responses, channel_id, user_id, '')

@app.action("OCR_1_1")
def ocr_1(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    user_states[user_id] = 'ocr_handler'
    user_responses[user_id] = 'OCR_1_1'
    say(f"<@{user_id}> 님, 주주명부와 등기부등본 텍스트 추출 기능을 실행합니다.")

    ocr_transform_handler(message, say, user_states, client, user_responses, channel_id, user_id, '')

@app.action("OCR_1_2")
def ocr_1(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    user_states[user_id] = 'ocr_handler'
    user_responses[user_id] = 'OCR_1_2'
    say(f"<@{user_id}> 님, 주주명부와 등기부등본 검토 및 DB 반영 기능을 실행합니다.")

    ocr_transform_handler(message, say, user_states, client, user_responses, channel_id, user_id, '')

@app.action("OCR_1_3")
def ocr_1(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    user_states[user_id] = 'ocr_handler'
    user_responses[user_id] = 'OCR_1_3'
    say(f"<@{user_id}> 님, 재무제표 텍스트 추출 기능을 실행합니다.")

    ocr_transform_handler(message, say, user_states, client, user_responses, channel_id, user_id, '')

@app.action("OCR_1_4")
def ocr_1(ack, body, say):
    ack()  # 응답 확인
    user_id = body["user"]["id"]
    message = body['message']
    channel_id = body['channel']['id']

    user_states[user_id] = 'ocr_handler'
    user_responses[user_id] = 'OCR_1_4'
    say(f"<@{user_id}> 님, 재무제표 검토 및 DB 반영 기능을 실행합니다.")

    ocr_transform_handler(message, say, user_states, client, user_responses, channel_id, user_id, '')


# ------------------------------------------------------------------------------

# 메인 핵심 로직
@app.event("message", middleware=[message_im_events])
@check_bot_active
def handle_message_events(event, say):
    global is_bot_active
    user_id = event['user']
    user_input = event['text']
    channel_id = event.get('channel')
    
    if process_user_input(user_input) == '비활성화' and user_id == 'U05R7FD8Y85': # 영무 유저 아이디(관리자)
        is_bot_active = False
        say(f"<@{user_id}> 님, 로제봇이 비활성화되었습니다.")
        return 

    if user_id not in user_states:
        user_purpose_handler(event, say) # 안내 문구 출력 - 알맞은 user_states[user_id] 배정하는 역할
    else: # 슬랙봇을 실행한 상황에 user_states[user_id]를 부여받은 상황일 때 진행
        #########################   재시작(로제봇)    ########################################
        if user_input == '재시작':
            msg = ("슬랙봇 시스템을 작동합니다. 무엇을 도와드릴까요? 종료를 원한다면 \'종료\'를 입력해주세요\n"
                "1. 휴가 신청\n"
                "2. 인사 총무\n"
                "3. 문서 작성\n"
                "4. 정기예금 회전 시스템\n"
                "5. 회수 상황판\n"
                "6. 검색\n"
                "7. 1on1\n"
                "8. 보안 시스템\n"
                "9. OCR\n"
            )
            send_direct_message_to_user(user_id, msg)
            user_states[user_id] = 'rosebot_waiting_only_number'
        #########################   문서4종시스템    ########################################
        elif user_states[user_id] == 'docx_generating_waiting_company_name': 
            docx_generating_company_name_handler(event, say, user_states, inv_list_info, inv_info)
        elif user_states[user_id] == 'docx_generating_waiting_inv_choice':
            docx_generating_inv_choice_handler(event, say, user_states, inv_list_info, inv_info)
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
            rose_bot_handler(event, say, user_states, client, user_responses)
        ######################### 정기예금 회전 시스템 ###################################
        elif user_states[user_id] == 'deposit_rotation_waiting_only_number':
            deposit_rotation_system_handler(event, say, user_states)
        elif user_states[user_id] == 'deposit_rotation_waiting_low_chatgpt_input':
            deposit_rotation_system_low_model_handler(event, say, user_states)
        ######################## OCR system #######################################
        elif user_states[user_id] == 'ocr_handler':
            ocr_transform_handler(event, say, user_states, client, user_responses, channel_id, user_id, user_input)

# Function to handle channel messages with specific keywords
@app.event("message")
def handle_channel_messages(event, say, client):
    channel_type = event.get("channel_type")
    text = event.get("text")
    user_id = event.get("user")
    
    if channel_type != "im" and ("로제봇" in text or "도와줘" in text):
        # # Send the response in the DM
        # msg = 'DM으로 답변드리겠습니다'
        # send_direct_message_to_user(user_id, msg)        
        
        # # Handle the user purpose in DM
        # user_purpose_handler(event, say)
        pass

@app.event("app_mention")
def handle_message_events(event, say):
    user_id = event['user']
    user_input = event['text']
    ### 사용자 명령어 인식 프로세스
    user_input = process_user_input(user_input)
    # send_direct_message_to_user(user_id, user_input)

# Direct Function except ROSEBOT
def user_purpose_handler(message, say):
    user_id = message['user']
    user_input = message['text']
    channel_id = message['channel']

    user_input = process_user_input(user_input)
    purpose = check_the_user_purpose(user_input,user_id)

    if purpose == "문서4종":
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
                "4. 권한이 변경된 사용자 조회([임시]운영자 전용)\n"
                "5. 권한 업데이트([임시]운영자 전용)\n"
                "6. 임시 운영자 배정(운영자 전용)\n"
                "7. 임시 운영자 목록 조회(운영자 전용)\n"
                "8. 임시 운영자 회수(운영자 전용)\n(종료를 원하시면 '종료'를 입력해주세요)"
                )
            send_direct_message_to_user(user_id, msg)
            user_states[user_id] = 'security_system_waiting_function_number'
        else:
            msg = (f"<@{user_id}> 권한이 없습니다. 종료합니다")
            send_direct_message_to_user(user_id, msg)
    elif purpose == "휴가신청시스템":
        if get_user_authority(user_id) < 4:
            msg = (f"휴가시스템을 작동합니다. 원하는 기능의 번호를 입력해주세요. (번호만 입력해주세요) \n"
                "1. 예정된 휴가 조회\n"
                "2. 신규 휴가 신청\n"
                "3. 신청 휴가 취소\n"
                "4. 남은 휴가 일수 조회\n"
                "(종료를 원하시면 '종료'를 입력해주세요)"
                )
            send_direct_message_to_user(user_id, msg)
            user_states[user_id] = 'vacation_purpose_handler'
        else:
            msg = (f"<@{user_id}>님은 권한이 없습니다. 종료합니다")
            send_direct_message_to_user(user_id, msg)
    elif purpose == "로제봇": # 로제봇으로 번호를 입력해서 기능을 실행하는 경우 
        execute_rosebot_by_button(user_id, channel_id, client, '로제봇 기능을 실행합니다.')
    elif purpose == "정기예금회전시스템":
        if get_user_authority(user_id) < 2:
            msg = ("정기예금 회전 시스템을 작동합니다. 종료를 원한다면 \'종료\'를 입력해주세요\n"
                    "1. 질문하기\n"
                    # "2. 질문하기(상위모델)\n"
                    # "3. 최종 만기일이 다가온 정기예금 상품조회\n"
                )
            send_direct_message_to_user(user_id, msg)
            user_states[user_id] = 'deposit_rotation_waiting_only_number'
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
    elif purpose == "인사총무시스템":
        if get_user_authority(user_id) < 3:
            msg = ("인사 총무 기능을 진행합니다. *아래의 링크를 확인하세요*\n"
                    "https://forms.gle/xWeE1qWNCjLrrBob7"
            )
            send_direct_message_to_user(user_id, msg)
        else:
            msg = (f"<@{user_id}>님은 권한이 없습니다. 종료합니다")
            send_direct_message_to_user(user_id, msg)
    elif purpose == "ocr":
        if get_user_authority(user_id) < 3: # 나중에 권한 1로 수정해야 함 
            user_responses[user_id] = None  # 초기화
            msg = (f"*[주의] OCR program의 주의사항은 다음과 같습니다.*\n"
                        "0. https://drive.google.com/drive/folders/1jO0EZViYdpuCgChcD_g1zwcTVYq-7321\n"
                        "1. 현재 날짜를 기준으로 *위 링크*의 폴더를 탐색합니다. ex) 2024-10-03 -> 24년_3분기_등기부등본\n"
                        "2. 파일명의 구성은 회사 이름을 시작으로 '_'로 구분되어야 합니다. ex) 라포랩스_재무제표.. \n"
                        "3. 회사 이름에 오타가 없는지 다시 한번 확인해주세요. 약식명, 풀네임을 기준으로 회사를 검색합니다.\n"
                        "4. 폴더에 파일을 올바르게 넣었는지 확인하세요. 링크의 구글 드라이브 내 문서 종류에 맞게 넣어주세요.\n"
                        "5. OCR 기능이 진행되는 동안 다른 기능을 추가로 실행할 수 없습니다. 실행 시 주의 사항을 확인하며 진행해주세요.\n"
                        )
            send_direct_message_to_user(user_id, msg)
            check_yes_or_no_init(user_id, channel_id, client, 'OCR 프로그램을 진행시키겠습니까?')
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
    