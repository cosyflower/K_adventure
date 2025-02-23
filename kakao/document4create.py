import googleapi
import gspread
import chatgpt
import json
import investmentTable

from formatting import process_user_input, get_proper_file_name
from directMessageApi import send_direct_message_to_user
from datetime import datetime, timedelta
import time

def docx_generating_company_name_handler(message, say, user_states, inv_list_info, inv_info):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)

    if user_input == '종료':
        msg = (f"종료합니다.")
        send_direct_message_to_user(user_id, msg)
        del user_states[user_id]
        return

    all_company_names, all_company_names_full = googleapi.get_all_company_names()
    
    if user_input in (all_company_names + all_company_names_full):
        company_name = user_input
    else:
        company_name = chatgpt.analyze_company_name(all_company_names,user_input)
    if company_name in (all_company_names + all_company_names_full):
        inv_list = googleapi.get_inv_list_and_date(company_name)
        choice = ""
        for i,data in enumerate(inv_list):
            choice = choice + f"\n{i+1}. {data}"
        choice = f"\n0. '{company_name}' 회사를 입력하신게 아닌가요?" + choice
        msg = (f"<{company_name}>의 INV ID를 선택해주세요(번호만 입력해주세요){choice}\n(종료를 원하시면 '종료'를 입력해주세요)")
        send_direct_message_to_user(user_id, msg)
        user_states[user_id] = 'docx_generating_waiting_inv_choice'
        inv_list_info[user_id] = inv_list
    else:
        msg = (f"회사명을 입력해주세요. (종료를 원하시면 '종료'를 입력해주세요)")
        send_direct_message_to_user(user_id, msg)
        user_states[user_id] = 'docx_generating_waiting_company_name'

def docx_generating_inv_choice_handler(message, say, user_states, inv_list_info, inv_info):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        msg = (f"종료합니다.")
        send_direct_message_to_user(user_id, msg)
        del user_states[user_id]
    else:
        inv_list = inv_list_info[user_id]
        inv_num = len(inv_list)
        if user_input.isdigit():
            user_input = int(user_input)
            if (user_input > inv_num) or (user_input < 0):
                msg = (f"보기에 있는 숫자만 입력해주세요")
                send_direct_message_to_user(user_id, msg)
                user_states[user_id] = 'docx_generating_waiting_inv_choice'
            elif user_input == 0:
                msg = (f"회사이름이 잘못되었군요. 회사명을 다시 입력해주세요 (종료를 원하시면 '종료'를 입력해주세요)")
                send_direct_message_to_user(user_id, msg)
                user_states[user_id] = 'docx_generating_waiting_company_name'
            else:
                msg = (f"회사 정보를 불러오는 중입니다...")
                send_direct_message_to_user(user_id, msg)
                data = inv_list[user_input-1]
                inv_id = data['inv_id']
                kv_id = googleapi.get_kv_id_from_inv_id(inv_id)

                db_1 = googleapi.get_db1_info_from_kv_id(kv_id)
                db_4 = googleapi.get_db4_info_from_inv_id(inv_id)
                fund_num = db_4['투자한 조합'].iloc[-1]
                db_7 = googleapi.get_db7_info_from_fund_num(fund_num)

                # 투자재원현황표
                investmentTable.create_investmentTable(db_1, db_4, db_7, kv_id, inv_id) # - 투자재원현황표를 만드는 함수
                send_direct_message_to_user(user_id, '투자재원현황표 생성이 완료되었습니다. 다음 문서 생성을 진행합니다.')
                time.sleep(2)

                total_investment, total_investment_in = googleapi.get_extra_info_frome_inv_id(inv_id,fund_num)
                current_time = googleapi.get_time()

                msg = (f"운용지시서 문서 생성 중입니다.")
                send_direct_message_to_user(user_id, msg)
                googleapi.make_docx_fileA(db_1,db_4,db_7,current_time)
                msg = (f"운용지시서 서류 생성 완료.")
                send_direct_message_to_user(user_id, msg)

                msg = (f"투심위의사록 문서 생성 중입니다.")
                send_direct_message_to_user(user_id, msg)
                new_document_id = googleapi.make_docx_fileB(db_1,db_4,db_7,current_time)
                googleapi.update_tableB(db_7,new_document_id)
                googleapi.update_tableB_ver2(new_document_id)
                msg = (f"투심위의사록 서류 생성 완료.")

                send_direct_message_to_user(user_id, msg)
                msg = (f"준법사항 체크리스트 문서 생성 중입니다.")
                send_direct_message_to_user(user_id, msg)
                googleapi.make_docx_fileC(db_1, db_4, db_7, total_investment, total_investment_in,current_time)
                msg = (f"준법사항 체크리스트 서류 생성.")
                send_direct_message_to_user(user_id, msg)

                msg = (f"투자집행품의서 문서 생성 중입니다.")
                send_direct_message_to_user(user_id, msg)
                googleapi.make_docx_fileD(db_1,db_4,db_7,current_time)
                msg = (f"투자집행품의서 서류 생성 완료.")
                send_direct_message_to_user(user_id, msg)

                msg = (f"모든 서류 생성 완료. 이용해주셔서 감사합니다.")
                send_direct_message_to_user(user_id, msg)
                del user_states[user_id]
        else:
            msg = (f"숫자만 입력해주세요")
            send_direct_message_to_user(user_id, msg)
            user_states[user_id] = 'docx_generating_waiting_inv_choice'

