from formatting import process_user_input, get_proper_file_name
import googleapi
import gspread
import chatgpt
import json

def docx_generating_company_name_handler(message, say, user_states, inv_list_info, inv_info):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)

    if user_input == '종료':
        say(f"<@{user_id}> 종료합니다.")
        del user_states[user_id]
        return

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

def docx_generating_inv_choice_handler(message, say, user_states, inv_list_info, inv_info):
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

def docx_generating_docx_category_handler(message, say, user_states, inv_list_info, inv_info):
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
            del inv_info[user_id]
