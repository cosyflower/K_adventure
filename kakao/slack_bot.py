import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import googleapi
import chatgpt
import re
import time
from user_commend import docx_generate, full_rest, half_rest, search_db, one_and_one, authority_update, view_all_user_authority_list, view_updated_user_authority_list, view_my_authority, authority_change, vacation_request_list, VACATION_SEQUENCE_TO_TPYE, \
VACATION_SEQUENCE_TO_REASON, vacation_cancel_list # 사용자 명령어 DB
import get_slack_user_info
import json
import config

# Testing for vacation
from googleVacationApi import append_data, get_real_name_by_user_id, find_data_by_userId
from validator import is_valid_date, is_valid_vacation_sequence, is_valid_vacation_reason_sequence, \
is_valid_email, is_valid_confirm_sequence, is_valid_cancel_sequence
from translator import to_specific_date, format_vacation_info

# testing for validating on generating docx
import gspread
import datetime

# 원하는 기능명을 반환해야 한다
def check_the_user_purpose(user_input):
    if user_input in docx_generate:
        return docx_generate[0]
    elif user_input in full_rest:
        return full_rest[0]
    elif user_input in half_rest:
        return half_rest[0]
    elif user_input in search_db:
        return search_db[0]
    elif user_input in one_and_one:
        return one_and_one[0]
    elif user_input in authority_update:
        return authority_update[0]
    elif user_input in view_all_user_authority_list:
        return view_all_user_authority_list[0]
    elif user_input in view_updated_user_authority_list:
        return view_updated_user_authority_list[0]
    elif user_input in view_my_authority:
        return view_my_authority[0]
    elif user_input in authority_change:
        return authority_change[0]
    elif user_input in vacation_request_list: # 휴가 신청 키워드 포함 - 휴가 신청할래로 반환
        return vacation_request_list[0]
    elif user_input in vacation_cancel_list: # 휴가 취소 키워드 포함 - 휴가 취소할래로 반환
        return vacation_cancel_list[0]
    else:
        print("chatgpt 사용 + 3원")
        return chatgpt.analyze_user_purpose(user_input)

def process_user_input(user_input):
    return re.split(r'>\s*', user_input, maxsplit=1)[-1].strip()

app = App(token=config.app_token_id)

user_states = {}
inv_list_info = {}
inv_info = {}
user_input_info = {}

# 연차 프로세스를 실행한 적 없을 때
# 연차 프로세스를 실행중일 때 
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
    user_input = process_user_input(user_input)
    ### 사용자 명령어 인식 프로세스
    if user_id not in user_states:
        user_purpose_handler(event, say) # 0. Mention하고 명령어를 입력하면 
        user_input_info[user_id] = user_input
    else: # state 확인 - 케이스에 맞는 함수를 실행하는 구간이 되겠다
        if user_states[user_id] == 'docx_generating_waiting_company_name': 
            docx_generating_company_name_handler(event, say)
        elif user_states[user_id] == 'docx_generating_waiting_inv_choice':
            docx_generating_inv_choice_handler(event, say)
        elif user_states[user_id] == 'docx_generating_waiting_docx_category':
            docx_generating_docx_category_handler(event, say)
        elif user_states[user_id] == 'authority_update_waiting_person_number':
            authority_update_person_number_handler(event, say)
        elif user_states[user_id] == 'authority_update_waiting_authority_category':
            authority_update_authority_category(event, say)
        elif user_states[user_id] == 'authority_update_json_file':
             authority_update_authority_update_json_file(event, say)
        elif user_states[user_id] == 'request_vacation':
            request_vacation(event, say)
        elif user_states[user_id] == 'cancel_vacation':
            cancel_vacation(event, say)
        
        
def user_purpose_handler(message, say): ### 1번 - 명령어를 인식하고 user_states[] 변경해야 한다 
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input) ### 명령어 입력을 token으로 구분하고 
    purpose = check_the_user_purpose(user_input) ### 구분된 토큰을 활용해서 원하는 목적을 진행한다 - return 원하는 기능명

    if purpose == "문서 4종 생성해줘":
        say(f"<@{user_id}> 문서 4종 생성을 진행합니다. 회사명을 입력해주세요 (종료를 원하시면 '종료'를 입력해주세요)")
        user_states[user_id] = 'docx_generating_waiting_company_name'
    elif purpose == "권한 변경해줘":
        with open('users_info.json', 'r', encoding='utf-8') as json_file:
            users_info = json.load(json_file)
        user_details = []
        for key, user_data in users_info.items():
            user_details.append({'real_name': user_data['real_name'], 'id': user_data['id'], 'authority': user_data['authority']})
        choice = ""
        for i,data in enumerate(user_details):
            choice = choice + f"\n{i+1}. {data}"
        say(f"<@{user_id}> 권한을 변경할 사람의 번호를 입력해주세요(번호만 입력해주세요){choice}\n(종료를 원하시면 '종료'를 입력해주세요)")
        user_states[user_id] = 'authority_update_waiting_authority_category'
        inv_list_info[user_id] = user_details
    elif purpose == "전체 사용자 권한 조회해줘":
        say(f"<@{user_id}> 전체 사용자 권한을 조회합니다")
        comment = ""
        with open("users_info.json", 'r', encoding='utf-8') as file:
            user_info_list = json.load(file)
        for i, (id, info) in enumerate(user_info_list.items()):
            comment = comment + f"{i}. id: {info['id']}, name: {info['name']}, authority: {info['authority']}\n"
        say(f"<@{user_id}> {comment} 전체 사용자 권한 조회가 끝났습니다")
    elif purpose == "권한 변경된 사용자 권한 조회해줘":
        say(f"<@{user_id}> 권한 변경된 사용자 권한을 조회합니다")
        comment = ""
        with open("authority_change_list.json", 'r', encoding='utf-8') as file:
            authority_change_list = json.load(file)
        with open("users_info.json", 'r', encoding='utf-8') as file:
            user_info_list = json.load(file)
        for i, (id, authority) in enumerate(authority_change_list.items()):
            comment = comment + f"{i}. id: {id}, name: {user_info_list[id]['name']}, authority: {authority}\n"
        say(f"{comment}<@{user_id}> 권한 변경된 사용자 권한 조회가 끝났습니다")
    elif purpose == "내 권한 알려줘":
        with open("users_info.json", 'r', encoding='utf-8') as file:
            user_info_list = json.load(file)
        if user_info_list[user_id]['authority'] == 1:
            authority_name = "관리자"
        elif user_info_list[user_id]['authority'] == 2:
            authority_name = "임직원"
        elif user_info_list[user_id]['authority'] == 3:
            authority_name = "인턴"
        else:
            authority_name = "미정"
        say(f"<@{user_id}>님의 권한은 {authority_name} 입니다")
    elif purpose == "권한 업데이트해줘":
        get_slack_user_info.update_authority()
        say(f"<@{user_id}> 권한 업데이트가 끝났습니다")
    elif purpose == "휴가 신청할래": # 휴가 신청 관련 -> 추후 휴가 신청할래로 변경
        say(f"<@{user_id}>님의 휴가 신청 프로세스를 진행합니다. 휴가 시작 날짜와 시간을 입력해주세요\n"
            "날짜는 YYYY-MM-DD 형태로 작성해주세요. 시간은 HH:MM 형태로 작성해주세요.\n"
            "[예시 1] 2024-04-04 09:00\n"
            "[예시 2] 2024-04-04 09:00\n"
            )
        user_states[user_id] = 'request_vacation'
    elif purpose == "휴가 취소할래": # 휴가 취소 관련
        say(f"<@{user_id}>님의 휴가 취소 프로세스를 진행합니다. <@{user_id}>님의 휴가 리스트를 출력합니다\n")
        user_states[user_id] = 'cancel_vacation'
        cancel_vacation(message, say)
    else:
        say(f"<@{user_id}> 없는 기능입니다. 다시 입력해주세요")

######### 휴가 / 연차 시스템 #############
#########

def input_cancel_sequence(message, say):
    user_id = message['user']
    user_input = message['text']
    # mention을 제외한 내가 전달하고자 하는 문자열만 추출하는 함수 
    cleaned_user_input = re.sub(r'<@[^>]+>\s*', '', user_input)
    cancel_sequeunce = cleaned_user_input

    found_data_list = find_data_by_userId(config.dummy_vacation_db_id, user_id)
    if is_valid_cancel_sequence(cancel_sequeunce, len(found_data_list)):
        cancel_vacation_status[user_id] = 'waiting_deleting'
        cancel_vacation(message, say) # 입력한 수를 넘겨야 한다
    else:
        say(f"잘못된 번호입니다. 다시 입력해주세요.")

#### 휴가 최소 --- 진행중
def cancel_vacation(message, say):
    user_id = message['user']
    user_input = message['text']
    # mention을 제외한 내가 전달하고자 하는 문자열만 추출하는 함수 
    cleaned_user_input = re.sub(r'<@[^>]+>\s*', '', user_input)
    vacation_sequence = cleaned_user_input

    # 먼저 휴가를 리스트업 한다 
    # spreadsheet 에서 user_id를 활용해서 관련된 휴가 정보를 가지고 와야 한다 
    # 출력시 1. 2. ... 형태로 출력한다 
    found_data_list = find_data_by_userId(config.dummy_vacation_db_id, user_id)

    if user_id not in cancel_vacation_status:
        seq = 1 
        say(f"<@{user_id}>의 휴가 삭제를 진행중입니다. 취소할 휴가 번호를 입력하세요.")
        for result in found_data_list:
            say(f"{seq}. {format_vacation_info(result)}")
            seq += 1
        cancel_vacation_status[user_id] = 'waiting_cancel_sequence'
    
    if cancel_vacation_status[user_id] == 'waiting_cancel_sequence':
        input_cancel_sequence(message, say)
    
    if cancel_vacation_status[user_id] == 'waiting_deleting':
        # user_input - 삭제할 레코드 번호를 받은 상황이다
        # 각각의 레코드 번호를 전달하면서 해당되는 스프레드 시트 정보를 제거해야 한다
        # 1 / 1, 2 / 1,2 -> [] 리스트 형태로 변환해주고
        ready_for_delete_list = cleaned_user_input
        
        # 리스트 내부를 순회하면서 순서를 얻는다
        # 해당 순서의 레코드를 스프레드 시트에서 제거해야 한다
        
    
    # 리스트된 휴가의 번호를 입력하면 해당 휴가를 삭제한다 - cancel_vacation_status
    # 삭제 완료 안내문을 발송하고 휴가 추가는 1, 취소는 2를 누르도록 진행한다

##### 휴가 종류를 입력받는다
def input_vacation_type(message, say):
    user_id = message['user']
    user_input = message['text']
    # mention을 제외한 내가 전달하고자 하는 문자열만 추출하는 함수 
    cleaned_user_input = re.sub(r'<@[^>]+>\s*', '', user_input)
    vacation_sequence = cleaned_user_input

    if is_valid_vacation_sequence(vacation_sequence):
        vacation_type = VACATION_SEQUENCE_TO_TPYE[int(vacation_sequence)]
        user_vacation_info[user_id].append(vacation_type) # 변환 모듈
        say(f"<@{user_id}>님 휴가 신청 진행중입니다. {vacation_type}을 신청했습니다.\n\n")
        user_vacation_status[user_id] = "waiting_vacation_reason"
    else:
        say(f"<@{user_id}>님 휴가 신청 진행중입니다. 잘못된 휴가 종류입니다. 1 - 5번 사이의 번호를 입력하세요\n\n")

#### 휴가 사유를 입력받는다
def input_vacation_reason(message, say):
    user_id = message['user']
    user_input = message['text']
    # mention을 제외한 내가 전달하고자 하는 문자열만 추출하는 함수 
    cleaned_user_input = re.sub(r'<@[^>]+>\s*', '', user_input)
    vacation_reason_sequence = cleaned_user_input

    # 예외 처리 관련
    if is_valid_vacation_reason_sequence(vacation_reason_sequence):
        vacation_reason_type = VACATION_SEQUENCE_TO_REASON[int(vacation_reason_sequence)]
        user_vacation_info[user_id].append(vacation_reason_type)
        say(f"<@{user_id}>님 휴가 신청 진행중입니다. {vacation_reason_type}를 신청했습니다.\n\n")
        if vacation_reason_type in ["경조휴가", "특별휴가", "출산휴가"]:
            user_vacation_status[user_id] = "waiting_vacation_specific_reason"
        else:
            user_vacation_info[user_id].append("") # 휴가 상세 자유를 공백으로 추가해둔다
            user_vacation_status[user_id] = "waiting_vacation_email"
    else:
        say(f"<@{user_id}>님 휴가 신청 진행중입니다. 잘못된 휴가 사유입니다. 1 - 8번 사이의 번호를 입력하세요\n\n")

#### 휴가 상세 사유 입력받기
def input_vacation_specific_reason(message, say):
    user_id = message['user']
    user_input = message['text']
    # mention을 제외한 내가 전달하고자 하는 문자열만 추출하는 함수 
    cleaned_user_input = re.sub(r'<@[^>]+>\s*', '', user_input)
    vacation_specific_reason = cleaned_user_input

    user_vacation_info[user_id].append(vacation_specific_reason)
    user_vacation_status[user_id] = "waiting_vacation_email"

#### 휴가 개인 이메일 입력받기
def input_vacation_email(message, say):
    user_id = message['user']
    user_input = message['text']
    # mention을 제외한 내가 전달하고자 하는 문자열만 추출하는 함수 
    cleaned_user_input = re.sub(r'<@[^>]+>\s*', '', user_input)
    email = cleaned_user_input
    # 이메일에 '!' 문자가 있는지 확인
    if '!' not in email:
        email = email.split('|')[1]
        # 만약 꺾쇠 괄호(<, >)도 제거하고 싶다면 strip 메서드를 사용할 수 있습니다.
        email = email.strip('>')

    if is_valid_email(email):
        user_vacation_info[user_id].append(email) # 변환 모듈
        say(f"<@{user_id}>님 휴가 신청 진행중입니다. <@{user_id}>님의 휴가 신청 이메일은 {email} 입니다.\n\n")
        user_vacation_status[user_id] = "pre-confirmed"
    else:
        say(f"<@{user_id}>님 휴가 신청 진행중입니다. <{email}>올바르지 않은 이메일 형식입니다. 다시 입력하세요\n\n")

def is_confirmed(confirm_sequence):
    if(confirm_sequence == '0'):
        return True
    
    return False

def checking_final_confirm(message, say):
    user_id = message['user']
    user_input = message['text']
    # mention을 제외한 내가 전달하고자 하는 문자열만 추출하는 함수 
    cleaned_user_input = re.sub(r'<@[^>]+>\s*', '', user_input)
    confirm_sequence = cleaned_user_input

    # 유요한 입력인지 확인
    if is_valid_confirm_sequence(confirm_sequence):
        if is_confirmed(confirm_sequence):
            user_vacation_status[user_id] = 'confirmed'
        else:
            say(f"<@{user_id}>님 휴가 신청 진행중입니다. 휴가 신청 정보를 재입력합니다. 휴가 시작 날짜를 알려주세요. 입력 형식은 YYYY-MM-DD 입니다.\n\n")
            del user_vacation_status[user_id]
            del user_vacation_info[user_id]
    else:
        say(f"<@{user_id}>님 휴가 신청 진행중입니다. <{confirm_sequence}> 잘못된 입력입니다. 0 혹은 1을 입력하세요(0: 저장, 1: 수정)\n\n")
    # 0번이면 DB 반영하는 단계로 이어지도록 (상태 변경해야 한다) + info 정보 wrapping 해서 DB에 반영해야 한다
    # 1번이면 user_vacation_info, user_vacation_status 해당 인덱스 정보 삭제하기

######### 휴가/연차 #######
def request_vacation(message, say):
    user_id = message['user']
    user_input = message['text']
    # mention을 제외한 내가 전달하고자 하는 문자열만 추출하는 함수 
    cleaned_user_input = re.sub(r'<@[^>]+>\s*', '', user_input)

    if cleaned_user_input == '종료':
        say(f"<@{user_id}>님 휴가 신청 프로세스를 종료합니다.\n\n")
        if user_id in user_states:
            del user_states[user_id]
        if user_id in user_vacation_info:
            del user_vacation_info[user_id]
        if user_id in user_vacation_status:
            del user_vacation_status[user_id]
        return # 슬랙 봇은 각 이벤트 별로 독립적으로 작동하기 떄문에 return을 작성해도 다른 이벤트 함수에 영향이 없음.. 이거 알고 있었냐?? 

    # 첫 입력 - Date 관련만 request_vacation() 내부에 로직을 넣음
    # 이외의 입력 받는 애들은 따로 함수화 함
    # waiting_ : 값 입력을 기다리는 상황
    # checking_ : 입력받는 것에 오류가 있는지 확인하는 상황이라고 생각하면 될 듯!
    if user_id not in user_vacation_status and cleaned_user_input != "종료":
        user_vacation_info[user_id] = []
        user_vacation_status[user_id] = 'requesting'
        start_date = process_user_input(cleaned_user_input)
        if is_valid_date(start_date):
            user_vacation_info[user_id].append(start_date)
            say(f"<@{user_id}>님 휴가 신청 진행중입니다. 휴가 종료 날짜와 시간을 입력해주세요.\n"
                "날짜는 YYYY-MM-DD 형태로, 시간은 HH:MM 형태로 입력하세요\n"
                "[예시] 2024-04-04 18:00\n"
                )
        else:
            say("잘못된 형식입니다. 휴가 시작 날짜와 시간을 YYYY-MM-DD HH:MM 형태로 다시 입력해주세요.")
            user_vacation_status[user_id] = 'pending'
    elif user_vacation_status[user_id] == 'pending': # 다시 시작 날짜부터 받는다 
        start_date = process_user_input(cleaned_user_input)
        if is_valid_date(start_date):
            user_vacation_info[user_id].append(start_date)
            say(f"<@{user_id}>님 휴가 신청 진행중입니다. 휴가 종료 날짜와 시간을 입력해주세요.\n"
                "날짜는 YYYY-MM-DD 형태로, 시간은 HH:MM 형태로 작성해주세요\n"
                "[예시] 2024-01-01 19:00\n"
                )
            user_vacation_status[user_id] = 'requesting'
        else:
            say(f"<@{user_id}>님 휴가 시작 날짜와 시간을 다시 입력해주세요 YYYY-MM-DD HH:MM 형태로 입력하세요 \n\n")
    elif user_vacation_status[user_id] == 'requesting': # 시작 날짜 문제가 없는 상황 - 종료 날짜를 입력받는다
        end_date = process_user_input(cleaned_user_input)
        if is_valid_date(end_date, comparison_date_str=user_vacation_info[user_id][0]):
            user_vacation_info[user_id].append(end_date)
            start_date = user_vacation_info[user_id][0]
            end_date = user_vacation_info[user_id][1]
            say(f"<@{user_id}>님 휴가 신청 진행중입니다. 휴가 종류를 선택하세요\n\n")
            user_vacation_status[user_id] = 'waiting_vacation_type'
        else:
            say("잘못된 형식입니다. 휴가 시작 날짜와 시간을 YYYY-MM-DD HH:MM 형태로 다시 입력해주세요.")
            user_vacation_info[user_id] = []
            user_vacation_status[user_id] = 'pending'

    # 휴가 종류 선택하기
    if user_vacation_status[user_id] == 'checking_vacation_type':
        input_vacation_type(message, say)
    
    if user_vacation_status[user_id] == 'waiting_vacation_type':
        say("휴가 종류에는 5가지로 숫자로 1 - 5번 사이의 수를 입력해주세요\n"
            "1. 연차\n"
            "2. 반차(오전)\n"
            "3. 반차(오후)\n"
            "4. 반반차(오전)\n"
            "5. 반반차(오후)\n"
            )
        user_vacation_status[user_id] = 'checking_vacation_type'

    # 휴가 사유 선택하기
    if user_vacation_status[user_id] == 'checking_vacation_reason':
        input_vacation_reason(message, say)

    if user_vacation_status[user_id] == "waiting_vacation_reason":
        # 휴가 이유 선택하기
        say("휴가 사유에는 8가지로 숫자로 1 - 8번 사이의 수를 입력해주세요\n"
            "1. 개인휴가\n"
            "2. 경조휴가\n"
            "3. 특별휴가\n"
            "4. 예비군,민방위휴가\n"
            "5. 보건휴가\n"
            "6. 안식휴가\n"
            "7. 출산휴가\n"
            "8. 기타휴가\n"
            )
        user_vacation_status[user_id] = 'checking_vacation_reason'


    ### 상세사유 입력하는 경우 그리고 입력하지 않는 경우 구분해서 입력해야 한다
    if user_vacation_status[user_id] == "checking_vacation_specific_reason":
        input_vacation_specific_reason(message, say)

    if user_vacation_status[user_id] == "waiting_vacation_specific_reason":
        # 상세 사유 입력받기
        say(f"<@{user_id}>님 휴가 신청 진행중입니다. 선택하신 {user_vacation_info[user_id][-1]}의 휴가 상세 사유를 작성해주세요")
        user_vacation_status[user_id] = "checking_vacation_specific_reason"

    # 이메일 입력 
    if user_vacation_status[user_id] == "checking_vacation_email":
        input_vacation_email(message, say)
    if user_vacation_status[user_id] == "waiting_vacation_email":
        # email 입력받기
        say(f"<@{user_id}>님 휴가 신청 진행중입니다. <@{user_id}>의 개인 이메일을 작성해주세요.\n"
            "* 유의 * 이메일 아이디 내 느낌표(!)가 존재해서는 안 됩니다."
            )
        user_vacation_status[user_id] = "checking_vacation_email"
    
    if user_vacation_status[user_id] == "waiting_final_confirm":
        checking_final_confirm(message, say)
    
    if user_id in user_vacation_info and user_vacation_status[user_id] == "pre-confirmed":
        say(f"<@{user_id}>의 휴가 신청 정보입니다.")
        for a, value in enumerate(user_vacation_info[user_id]):
            # 저장된 정보 출력 
            # user_states, user_vacation_info, user_vacation_status 로 상태를 지속적으로 확인하는 중으로 생각하기
            say(f"{value}\n")
        say(f"<@{user_id}>의 휴가 신청을 완료하려면 0을, 수정을 원하면 1을 입력하세요.")
        user_vacation_status[user_id] = "waiting_final_confirm"

    if user_id in user_vacation_info and user_vacation_status[user_id] == "confirmed":
        # DB에 저장한다
        # user_vacation_info[user_id] 안에 모두 담겨져있는 상황 : 시작 - 종료 - 종류 - 사유 - 상세 사유 - 이메일 
        new_row_data = []
        current_time = datetime.datetime.now().strftime('%Y. %m. %d %p %I:%M:%S').replace('AM', '오전').replace('PM', '오후')
        # 시간을 넣어야 한다
        start_date_formatted = to_specific_date(user_vacation_info[user_id][0])
        end_date_formatted = to_specific_date(user_vacation_info[user_id][1])
        type = user_vacation_info[user_id][2]
        reason = user_vacation_info[user_id][3]
        specific_reason = user_vacation_info[user_id][4]
        email = user_vacation_info[user_id][5]

        new_row_data.extend([
            current_time,
            get_real_name_by_user_id(user_id), # 저장시 ID로 저장 - uesrs_info에서 찾아서 대신 넣어야 한다 (있는 경우 없는 경우 생각하기)
            start_date_formatted,
            end_date_formatted,
            type,
            reason,
            specific_reason,
            email
        ])

        is_stored = False
        while is_stored is False:
            try:
                say(f"<@{user_id}>의 휴가 신청을 처리중입니다.")
                append_data(config.dummy_vacation_db_id, new_row_data)
                is_stored =True
            except gspread.exceptions.APIError as e:
                say(f"APIError occurred: {e}")
            except gspread.exceptions.GSpreadException as e:
                say(f"GSpreadException occurred: {e}")
            except FileNotFoundError as e:
                say(f"File not found: {e}")
            except Exception as e:
                say(f"An unexpected error occurred: {e}")
        
        say(f"<@{user_id}>의 휴가 신청을 완료합니다. 휴가 / 연차 서비스를 종료합니다.\n")
        del user_states[user_id]
        del user_vacation_info[user_id]
        del user_vacation_status[user_id]
        return
    

#########################   문서 생성    ########################################
def docx_generating_company_name_handler(message, say):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    # 모든 기업 이름을 가지고 오는 구간
    try:
        say("스프레드시트에 등록된 기업명 정보를 로드중입니다.\n")
        all_company_names, all_company_names_full = googleapi.get_all_company_names()
        say("스프레드시트에 등록된 기업명 정보 로드 완료. 잠시만 기다려주세요...\n")
    except FileNotFoundError as e: # JSON 키 파일이 없는 경우
        say("등록된 키 파일의 정보를 찾을 수 없습니다. JSON 키 파일을 등록해주세요. 프로그램을 종료합니다.\n")
        # say(f"File not found error: {e}")
        # all_company_names, all_company_names_full = [], []
        del user_states[user_id]
        return
    except gspread.exceptions.SpreadsheetNotFound as e: # 스프레드시트를 찾지 못한 경우
        say("연결된 스프레트시트 정보를 찾을 수 없습니다. 파일을 확인해주세요. 프로그램을 종료합니다.\n")
        # say(f"Spreadsheet not found: {e}")
        # all_company_names, all_company_names_full = [], []
        del user_states[user_id]
        return
    except gspread.exceptions.APIError as e: # API 호출 중 에러가 발생한 경우
        say("gspread API 호출 중 에러가 발생했습니다. 다시 시도해주세요. 프로그램을 종료합니다.\n")
        # say(f"API error: {e}")
        # all_company_names, all_company_names_full = [], []
        del user_states[user_id]
        return
    except Exception as e: # 그 외의 기타 에러가 발생한 경우
        say("알 수 없는 에러가 발생했습니다. 에러를 확인해주세요. 프로그램을 종료합니다.\n")
        say(f"An unexpected error occurred: {e}") 
        # all_company_names, all_company_names_full = [], []
        del user_states[user_id]
        return

    if user_input == '종료':
        say(f"<@{user_id}> 종료합니다.")
        del user_states[user_id]
    else:
        if user_input in (all_company_names + all_company_names_full):
            company_name = user_input
        else:
            company_name = chatgpt.analyze_company_name(all_company_names,user_input)
            print("chatgpt 사용 + 10원")
        if company_name in (all_company_names + all_company_names_full):
            inv_list = googleapi.get_inv_list_and_date(company_name)
            choice = ""
            for i,data in enumerate(inv_list):
                choice = choice + f"\n{i+1}. {data}"
            choice = f"\n0. '{company_name}' 회사를 입력하신게 아닌가요?" + choice
            say(f"<@{user_id}> <{company_name}>의 INV ID를 선택해주세요(번호만 입력해주세요){choice}\n(종료를 원하시면 '종료'를 입력해주세요)")
            user_states[user_id] = 'docx_generating_waiting_inv_choice'
            inv_list_info[user_id] = inv_list
        else:
            say(f"<@{user_id}> 입력하신 회사명이 존재하지 않습니다. 회사명을 다시 입력해주세요.\n(종료를 원하시면 '종료'를 입력해주세요)")
            user_states[user_id] = 'docx_generating_waiting_company_name'

def docx_generating_inv_choice_handler(message, say):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        say(f"<@{user_id}> 종료합니다.")
        del user_states[user_id]
    else:
        inv_list = inv_list_info[user_id]
        inv_num = len(inv_list)
        if user_input.isdigit():
            user_input = int(user_input)
            if (user_input > inv_num) or (user_input < 0):
                say(f"<@{user_id}> 보기에 있는 숫자만 입력해주세요")
                user_states[user_id] = 'docx_generating_waiting_inv_choice'
            elif user_input == 0:
                say(f"<@{user_id}> 회사이름이 잘못되었군요. 회사명을 다시 입력해주세요 (종료를 원하시면 '종료'를 입력해주세요)")
                user_states[user_id] = 'docx_generating_waiting_company_name'
            else:
                data = inv_list[user_input-1]
                inv_id = data['inv_id']
                inv_info[user_id] = inv_id
                say(f"<@{user_id}> {inv_id} 에 해당하는 서류를 생성합니다. 생성을 원하는 문서의 번호를 띄어쓰기 없이 입력해주세요\n 예시 : 1 , 12 , 123 , 1234 , 32 , 14\n 1: 운용지시서 2: 투심위의사록 3: 준법사항 체크리스트 4: 투자집행품의서\n(종료를 원하시면 '종료'를 입력해주세요)")
                user_states[user_id] = 'docx_generating_waiting_docx_category'
        else:
            say(f"<@{user_id}> 숫자만 입력해주세요")
            user_states[user_id] = 'docx_generating_waiting_inv_choice'

def docx_generating_docx_category_handler(message, say):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        say(f"<@{user_id}> 종료합니다.")
        del user_states[user_id]
    else:
        check = 0
        for i in user_input:
            if i not in {'1', '2', '3', '4'}:
                check = 1
        if check == 1:
            say(f"<@{user_id}> 1 2 3 4 중에서 띄어쓰기 없이 숫자만 입력해주세요")
            user_states[user_id] = 'docx_generating_waiting_docx_category'
        else:
            say(f"<@{user_id}> 문서 생성에 필요한 정보를 불러오는 중입니다.")
            inv_id = inv_info[user_id]
            kv_id = googleapi.get_kv_id_from_inv_id(inv_id)
            db_1 = googleapi.get_db1_info_from_kv_id(kv_id)
            db_4 = googleapi.get_db4_info_from_inv_id(inv_id)
            fund_num = db_4['투자한 조합'].iloc[-1]
            db_7 = googleapi.get_db7_info_from_fund_num(fund_num)
            total_investment, total_investment_in = googleapi.get_extra_info_frome_inv_id(inv_id,fund_num)
            current_time = googleapi.get_time()
            if '1' in user_input:
                say(f"<@{user_id}> 운용지시서 문서 생성 중입니다.")
                googleapi.make_docx_fileA(db_1,db_4,db_7,current_time)
                say(f"<@{user_id}> 운용지시서 서류 생성.")
            if '2' in user_input:
                say(f"<@{user_id}> 투심위의사록 문서 생성 중입니다.")
                new_document_id = googleapi.make_docx_fileB(db_1,db_4,db_7,current_time)
                googleapi.update_tableB(db_7,new_document_id)
                googleapi.update_tableB_ver2(new_document_id)
                say(f"<@{user_id}> 투심위의사록 서류 생성.")
            if '3' in user_input:
                say(f"<@{user_id}> 준법사항 체크리스트 문서 생성 중입니다.")
                googleapi.make_docx_fileC(db_1, db_4, db_7, total_investment, total_investment_in,current_time)
                say(f"<@{user_id}> 준법사항 체크리스트 서류 생성.")
            if '4' in user_input:
                say(f"<@{user_id}> 투자집행품의서 문서 생성 중입니다.")
                googleapi.make_docx_fileD(db_1,db_4,db_7,current_time)
                say(f"<@{user_id}> 투자집행품의서 서류 생성.")
            say(f"<@{user_id}> 모든 서류 생성 완료. 이용해주셔서 감사합니다.")
            del user_states[user_id]
#########################   권한 업데이트    ########################################
def authority_update_person_number_handler(message, say):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        say(f"<@{user_id}> 종료합니다.")
        del user_states[user_id]
    else:
        with open('users_info.json', 'r', encoding='utf-8') as json_file:
            users_info = json.load(json_file)
        user_details = []
        for key, user_data in users_info.items():
            user_details.append({'real_name': user_data['real_name'], 'id': user_data['id'], 'authority': user_data['authority']})
        choice = ""
        for i,data in enumerate(user_details):
            choice = choice + f"\n{i+1}. {data}"
        say(f"<@{user_id}> 권한을 변경할 사람의 번호를 입력해주세요(번호만 입력해주세요){choice}\n(종료를 원하시면 '종료'를 입력해주세요)")
        user_states[user_id] = 'authority_update_waiting_authority_category'
        inv_list_info[user_id] = user_details

def authority_update_authority_category(message, say):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        say(f"<@{user_id}> 종료합니다.")
        del user_states[user_id]
    else:
        user_details = inv_list_info[user_id]
        user_num = len(user_details)
        if user_input.isdigit():
            user_input = int(user_input)
            if (user_input > user_num) or (user_input < 0):
                say(f"<@{user_id}> 보기에 있는 숫자만 입력해주세요")
                user_states[user_id] = 'authority_update_waiting_authority_category'
            else:
                data = user_details[user_input-1]
                real_name = data['real_name']
                id = data['id']
                authority = data['authority']
                if authority == 1:
                    authority_name = "관리자"
                elif authority == 2:
                    authority_name = "임직원"
                elif authority == 3:
                    authority_name = "인턴"
                else:
                    authority_name = "미정"
                choice = ""
                if authority != 1:
                    choice = choice + "\n1. 관리자"
                if authority != 2:
                    choice = choice + "\n2. 임직원"
                if authority != 3:
                    choice = choice + "\n3. 인턴"
                if authority != 4:
                    choice = choice + "\n4. 미정"
                say(f"<@{user_id}> {real_name}님의 현재 권한은 {authority_name}입니다\n 업데이트할 권한의 번호를 입력해주세요(번호만 입력해주세요){choice}\n(종료를 원하시면 '종료'를 입력해주세요)")
                user_states[user_id] = 'authority_update_json_file'
                inv_list_info[user_id] = data
        else:
            say(f"<@{user_id}> 숫자만 입력해주세요")
            user_states[user_id] = 'authority_update_waiting_authority_category'

def authority_update_authority_update_json_file(message, say):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        say(f"<@{user_id}> 종료합니다.")
        del user_states[user_id]
    else:
        data = inv_list_info[user_id]
        real_name = data['real_name']
        id = data['id']
        authority = data['authority']
        if user_input.isdigit():
            user_input = int(user_input)
            if (user_input == authority) or (user_input < 0):
                say(f"<@{user_id}> 보기에 있는 숫자만 입력해주세요")
                user_states[user_id] = 'authority_update_json_file'
            else:
                with open('users_info.json', 'r', encoding='utf-8') as json_file:
                    users_info = json.load(json_file)
                for user_id, user_data in users_info.items():
                    if user_data['real_name'] == real_name:
                        user_data['authority'] = user_input
                        with open("authority_change_list.json", 'r') as file:
                            authority_change_list = json.load(file)
                        authority_change_list[id] = user_input
                        with open("authority_change_list.json", 'w') as file:
                            json.dump(authority_change_list, file, indent=4)
                with open('users_info.json', 'w', encoding='utf-8') as json_file:
                    json.dump(users_info, json_file, ensure_ascii=False, indent=4)
                say(f"<@{user_id}> {real_name}님의 권한이 변경되었습니다")
        else:
            say(f"<@{user_id}> 숫자만 입력해주세요")
            user_states[user_id] = 'authority_update_json_file'
            
if __name__ == "__main__":
    SocketModeHandler(app,config.user_token_id).start()
    