import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import googleapi
import chatgpt
import re
import time
import get_slack_user_info
import json
import config
import schedule
import time
import threading
from user_commend import docx_generate, full_rest, half_rest, search_db, one_and_one, authority_update, view_all_user_authority_list, view_updated_user_authority_list, view_my_authority, authority_change, vacation_request_list,  \
security_system, vacation_system_list # 사용자 명령어 DB

# Testing for vacation
from notification import notify_today_vacation_info
from formatting import process_user_input
from googleVacationApi import request_vacation, cancel_vacation, vacation_purpose_handler, get_remained_vacation, \
get_today_vacation_info

# testing for validating on generating docx
import gspread
import datetime

"""
사용자로부터 입력을 받았을 때 처음으로 입력에 대한 분석이 진행되는 함수

"""
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
    elif user_input in vacation_system_list:
        return vacation_system_list[0]
    elif user_input in security_system:
        return security_system[0]
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

user_states = {}
inv_list_info = {}
inv_info = {}
user_input_info = {}

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
    
    ## 입력 초기 
    if user_id not in user_states:
        user_purpose_handler(event, say)
        user_input_info[user_id] = user_input
    else: # 입력 초기가 아닌 경우
        if user_states[user_id] == 'docx_generating_waiting_company_name': 
            docx_generating_company_name_handler(event, say)
        elif user_states[user_id] == 'docx_generating_waiting_inv_choice':
            docx_generating_inv_choice_handler(event, say)
        elif user_states[user_id] == 'docx_generating_waiting_docx_category':
            docx_generating_docx_category_handler(event, say)

        elif user_states[user_id] == 'security_system_waiting_function_number':
            security_system_user_function_handler(event, say)
        elif user_states[user_id] == 'authority_update_waiting_person_number':
            authority_update_person_number_handler(event, say)
        elif user_states[user_id] == 'authority_update_waiting_authority_category':
            authority_update_authority_category(event, say)
        elif user_states[user_id] == 'authority_update_json_file':
             authority_update_authority_update_json_file(event, say)
        
        elif user_states[user_id] == 'vacation_purpose_handler':
            vacation_purpose_handler(event, say, user_states, cancel_vacation_status, user_vacation_info, user_vacation_status)
        elif user_states[user_id] == 'request_vacation':
            request_vacation(event, say, user_states, user_vacation_status, user_vacation_info)
        elif user_states[user_id] == 'cancel_vacation':
            cancel_vacation(event, say, user_states, cancel_vacation_status)    
       
def user_purpose_handler(message, say): ### 1번 - 명령어를 인식하고 user_states[] 변경해야 한다 
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input) ### 명령어 입력을 token으로 구분하고 
    purpose = check_the_user_purpose(user_input) ### 구분된 토큰을 활용해서 원하는 목적을 진행한다 - return 원하는 기능명

    if purpose == "문서 4종 생성해줘":
        say(f"<@{user_id}> 문서 4종 생성을 진행합니다. 회사명을 입력해주세요 (종료를 원하시면 '종료'를 입력해주세요)")
        user_states[user_id] = 'docx_generating_waiting_company_name'
    elif purpose == "보안시스템 작동해줘":
        say(f"<@{user_id}> 보안시스템을 작동합니다. 원하는 기능의 번호를 입력해주세요. (번호만 입력해주세요) \n"
            "1. 전체 사용자 권한 조회(관리자 전용)\n"
            "2. 권한이 변경된 사용자 조회(관리자 전용)\n"
            "3. 권한 업데이트(관리자 전용)\n"
            "4. 신규 사용자 권한 배정\n"
            "5. 내 권한 조회\n(종료를 원하시면 '종료'를 입력해주세요)"
            )
        user_states[user_id] = 'security_system_waiting_function_number'
    elif purpose == "휴가시스템 작동해줘":
        say(f"<@{user_id}> 휴가시스템을 작동합니다. 원하는 기능의 번호를 입력해주세요. (번호만 입력해주세요) \n"
            "1. 신청된 휴가 조회\n"
            "2. 신규 휴가 신청\n"
            "3. 기존 휴가 삭제\n"
            "4. 남은 휴가 일수 조회\n"
            "(종료를 원하시면 '종료'를 입력해주세요)"
            )
        user_states[user_id] = 'vacation_purpose_handler'
    else:
        say(f"<@{user_id}> 없는 기능입니다. 다시 입력해주세요")

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
def security_system_user_function_handler(message, say):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        say(f"<@{user_id}> 종료합니다.")
        del user_states[user_id]
    else:
        if user_input.isdigit():
            user_input = int(user_input)
            if user_input==1: # 전체 사용자 권한 조회
                say(f"<@{user_id}> 전체 사용자 권한을 조회합니다")
                comment = ""
                with open("users_info.json", 'r', encoding='utf-8') as file:
                    user_info_list = json.load(file)
                for i, (id, info) in enumerate(user_info_list.items()):
                    authority_name = ""
                    if info['authority'] == 1:
                        authority_name = "투자팀"
                    elif info['authority'] == 2:
                        authority_name = "임직원"
                    elif info['authority'] == 3:
                        authority_name = "인턴"
                    else:
                        authority_name = "미정"
                    comment = comment + f"{i}. id: {info['id']}, name: {info['name']}, authority: {authority_name}\n"
                say(f"<@{user_id}> {comment} 전체 사용자 권한 조회가 끝났습니다")
                del user_states[user_id]
            elif user_input==2: # 권한 변경된 사용자 조회
                say(f"<@{user_id}> 권한 변경된 사용자를 조회합니다")
                comment = ""
                with open("authority_change_list.json", 'r', encoding='utf-8') as file:
                    authority_change_list = json.load(file)
                with open("users_info.json", 'r', encoding='utf-8') as file:
                    user_info_list = json.load(file)
                for i, (id, authority) in enumerate(authority_change_list.items()):
                    authority_name = ""
                    if authority == 1:
                        authority_name = "투자팀"
                    elif authority == 2:
                        authority_name = "임직원"
                    elif authority == 3:
                        authority_name = "인턴"
                    else:
                        authority_name = "미정"
                    comment = comment + f"{i}. id: {id}, name: {user_info_list[id]['name']}, authority: {authority_name}\n"
                say(f"{comment}<@{user_id}> 권한 변경된 사용자 조회가 끝났습니다")
                del user_states[user_id]
            elif user_input==3: # 권한 변경
                with open('users_info.json', 'r', encoding='utf-8') as json_file:
                    users_info = json.load(json_file)
                user_details = []
                for key, user_data in users_info.items():
                    authority_name = ""
                    if user_data['authority'] == 1:
                        authority_name = "투자팀"
                    elif user_data['authority'] == 2:
                        authority_name = "임직원"
                    elif user_data['authority'] == 3:
                        authority_name = "인턴"
                    else:
                        authority_name = "미정"
                    user_details.append({'real_name': user_data['real_name'], 'id': user_data['id'], 'authority_name': authority_name, 'authority': user_data['authority']})
                choice = ""
                for i,data in enumerate(user_details):
                    choice = choice + f"\n{i+1}. {data}"
                say(f"<@{user_id}> 권한을 변경할 사람의 번호를 입력해주세요(번호만 입력해주세요){choice}\n(종료를 원하시면 '종료'를 입력해주세요)")
                user_states[user_id] = 'authority_update_waiting_authority_category'
                inv_list_info[user_id] = user_details
            elif user_input==4: # 신규 사용자 권한 배정
                get_slack_user_info.update_authority()
                say(f"<@{user_id}> 신규 사용자 권한 배정이 끝났습니다. 종료합니다.")
                del user_states[user_id]
            elif user_input==5: # 사용자 권환 조회
                with open("users_info.json", 'r', encoding='utf-8') as file:
                    user_info_list = json.load(file)
                if user_info_list[user_id]['authority'] == 1:
                    authority_name = "투자팀"
                elif user_info_list[user_id]['authority'] == 2:
                    authority_name = "임직원"
                elif user_info_list[user_id]['authority'] == 3:
                    authority_name = "인턴"
                else:
                    authority_name = "미정"
                say(f"<@{user_id}>님의 권한은 {authority_name} 입니다. 종료합니다.")
                del user_states[user_id]
            else:
                say(f"<@{user_id}> 정확한 숫자를 입력해주세요")
                user_states[user_id] = 'security_system_waiting_function_number'
        else:
            say(f"<@{user_id}> 숫자만 입력해주세요")
            user_states[user_id] = 'security_system_waiting_function_number'

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
                authority_name = data['authority_name']
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
            if (user_input == authority) or (user_input < 0 or (user_input > 4)):
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
            del user_states[user_id]
            
if __name__ == "__main__":
    # 스케줄러 실행을 위한 스레드 시작
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()
    # App 실행하기
    SocketModeHandler(app,config.app_token_id).start()
    