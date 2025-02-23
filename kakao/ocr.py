from formatting import process_user_input
from directMessageApi import send_direct_message_to_user

from ocr_controller import compare_prefix_lists, ocr_handler, compare_controller
from ocr_view import show_comparison_results, show_not_found_results, show_found_and_not_found_results, check_yes_or_no_progress , \
choice_multiple_ocr_selection, choice_multiple_selection_in_ocr_1, choice_multiple_selection_in_ocr_2

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from collections import OrderedDict

import config
import time

from OCR_financialstatements import list_files_in_folder, normalize_text, process_files, list_file_names_in_folder, \
get_info_equation_sheet, filtering_jsonlist, merge_and_deduplicate, chatgpt_output_to_json_form, chatgpt_output_to_json_form, \
ocr2_phase2_gpt, write_to_google_sheet, ocr2_phase1

from ocr_util import get_all_key_cells_per_cp, build_json_array_with_separation, save_json_array_to_file, convert_json_to_val_all_cells, restructure_json_array, check_missing_items_in_actual_items, \
remove_error_entries, extract_categories, second_check_missing_items, get_all_data_as_flat_list
from GlobalState import GlobalState

# global variables
# ocr_parent_id = config.ocr_parent_id ### 실제 배포하는 폴더 
ocr_parent_id = config.ocr_test_parent_id ### 테스트 폴더 

global_property_registry_id = '' # 등기부등본 폴더 
global_financial_statement_id = '' # 재무제표 폴더
global_shareholder_list_id = '' # 주주명부 폴더 
global_common_names_pr_and_sh = [] # 등기부 & 주주명부 공통 기업명

# Google Drive API 설정
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = config.kakao_json_key_path
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

def remove_duplicates(input_list):
    return list(set(input_list))

def get_fs_name(folder_id):
    """
    folder_id -> get strings before '_' in every file's name
    result is set() - prevent same names and return in list
    """
    try:
        # 폴더 안의 파일 목록 가져오기
        query = f"'{folder_id}' in parents and trashed = false"
        response = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(name)',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()

        files = response.get('files', [])
        company_names = set()

        for file in files:
            file_name = file['name']
            
            if '_' in file_name:
                company_name = file_name.split('_')[0]
                company_names.add(company_name)
            else:
                continue
        return list(company_names)

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

def ocr_transform_handler(message, say, user_states, client, user_responses, channel_id, user_id, user_input):
    bot_id = message['user']
    bot_message = message['text']
    
    user_input = process_user_input(user_input)

    if user_input == '종료':
        msg = (f"OCR program을 종료합니다.\n")
        send_direct_message_to_user(user_id, msg)
        del user_states[user_id]
        return
    
    ######### 1, 2, 3, 4 Selection Logic ######
    # under user_states[user_id] = 'ocr_handler'
    # user_responses[user_id]만 수정하면서 진행 
    # user_states[user_id] 건들지 말기. 계속 ocr_transform_handler로 정보를 전달해야 함
    if user_responses[user_id] == 'OCR_1_1':
        msg = (f'공사중입니다')
        send_direct_message_to_user(user_id, msg)
        
        pass

    elif user_responses[user_id] == 'OCR_1_3':
        for i in range(2):
            time.sleep(2)

        # 순수 회사명만 가지고 있는 상황
        pr_existing_names, pr_not_found_names, fs_existing_names, fs_not_found_names, sh_existing_names, sh_not_found_names, \
            property_registry_id, financial_statement_id, sharedholder_list_id = compare_controller(parent_folder_id=ocr_parent_id)
        
        # Erase duplication
        pr_existing_names = remove_duplicates(pr_existing_names)
        pr_not_found_names = remove_duplicates(pr_not_found_names)
        fs_existing_names = remove_duplicates(fs_existing_names)
        fs_not_found_names = remove_duplicates(fs_not_found_names)
        sh_existing_names = remove_duplicates(sh_existing_names)
        sh_not_found_names = remove_duplicates(sh_not_found_names)
        
        global_property_registry_id = property_registry_id # 등기부등본 폴더 ***************************************
        global_financial_statement_id = financial_statement_id # 재무제표 폴더 *******************************
        global_sharedholder_list_id = sharedholder_list_id # 주주명부 폴더 *****************************

        # 주주명부 등기부등본 올바른 이름들 중에서 공통 기업명, 공통되지 않은 기업명
        # 올바른 기업명 내에서 공통되는 기업, 공통되지 않은 기업명 반환 (shareholder, property_registry)
        common_names_pr_and_sh, only_in_pr, only_in_sh = compare_prefix_lists(pr_existing_names, sh_existing_names)

        global_common_names_pr_and_sh = common_names_pr_and_sh # 등기부등본, 주주명부 공통 기업명 *******************************

        # 재무제표의 올바른 이름 | 재무제표의 잘못된 이름
        msg = show_found_and_not_found_results(fs_existing_names, fs_not_found_names)
        send_direct_message_to_user(user_id, msg)

        # 안내 멘트 - 소요 시간 멘트 띄우기
        msg = (f'처리할 기업명의 수는 {len(fs_existing_names)}개입니다. 1개의 문서 당 소요 시간은 4-5분입니다.\n'
               f'예상소요 시간은 {len(fs_existing_names) * 4}에서 {len(fs_existing_names) * 5}분입니다.'
               '진행이 완료될 때까지 대기해주세요....')
        send_direct_message_to_user(user_id, msg)
        
        # 순수 회사명만 가지고 있음 
        normalized_company_name_list = [normalize_text(name) for name in fs_existing_names]
        # print(f'normalized : {normalized_company_name_list}')
        
        # process_files 인자로 전달하기 위한 변수 선언
        additional_company_name_list = set()

        # 전체 파일명을 조회합니다
        # 파일명 중 '_' 앞의 문자열만 조회한다
        total_fs_names = list_file_names_in_folder(financial_statement_id)
        # print(f'total_fs_name : {total_fs_names}')

        for file_name in total_fs_names:
            # comparing_file_names 내의 각 요소 확인
            for base_name in normalized_company_name_list:
                # 파일명이 'base_name + "_"', 'base_name + "(별도)"', 'base_name + "(연결)"' 중 하나로 시작하는지 확인
                if (
                    file_name.startswith(f"{base_name}") or
                    file_name.startswith(f"{base_name}(별도)") or
                    file_name.startswith(f"{base_name}(연결)")
                ):
                    normalized_name = normalize_text(file_name)
                    additional_company_name_list.add(normalized_name)

        # print(f'additional_fs_names : {additional_company_name_list}')
        additional_company_name_list = list(additional_company_name_list)
        files_financialstatements = list_files_in_folder(financial_statement_id)
        process_files(additional_company_name_list, files_financialstatements)
        # 안내 멘트 - 링크 띄우기 
        msg = (f'https://docs.google.com/spreadsheets/d/1T0Hh-8cttX7KXAPGUGkDOrWyCsrI_u9zrR461dmq52k'
               '\n'
               '재무재표의 텍스트 추출이 완료되었습니다. 위의 링크를 확인해주세요!')
        send_direct_message_to_user(user_id, msg)
        return
    
    elif user_responses[user_id] == 'OCR_1_4':
        msg = (f'공사중입니다')
        send_direct_message_to_user(user_id, msg)

        if user_id in GlobalState.user_responses:
            del GlobalState.user_responses[user_id]
        if user_id in GlobalState.user_states:
            del GlobalState.user_states[user_id]
        
        pass
        return
    elif user_responses[user_id] == 'OCR_1':
        msg = (f'<@{user_id}> 님  OCR_1번 기능을 실행합니다')
        send_direct_message_to_user(user_id, msg)
        choice_multiple_selection_in_ocr_1(user_id, channel_id, client, content='OCR 1 - 4 중 하나를 선택해주세요')
        return
    elif user_responses[user_id] == 'OCR_2_1':
        '''
        OCR2_phase1 
        '''
        msg = (f'<@{user_id}> 님  OCR_2_1번 기능을 실행합니다.')
        send_direct_message_to_user(user_id, msg)

        # OCR2 Logic
        financialstatements_folder_id = config.financialstatements_folder_id ## 재무제표 폴더

        ## financialstatements_folder_id 안에 존재하는 모든 파일명을 확인한다.
        ## '_' 앞 문자열을 모두 가지고 온다
        financialstatements_company_name_list = get_fs_name(financialstatements_folder_id)
        normalized_company_name_list = [normalize_text(name) for name in financialstatements_company_name_list] # 확인해야 하는 리스트

        # normalized_company_name_list 검증하기
        # 요소 내 '(' 가 포함된 경우 이어서 '연결)' 혹은 '별도)'가 이어져있는지 확인
        # 조건을 만족하지 못한 경우 해당 요소를 제거
        for company_name in normalized_company_name_list:
            # '(' 가 포함된 경우
            if '(' in company_name:
                # ')' 가 포함되어 있고, 이어서 '연결)' 또는 '별도)'가 있는지 확인
                if not (company_name.endswith('연결)') or company_name.endswith('별도)')):
                    # 조건을 만족하지 못한 경우 해당 요소 제거
                    normalized_company_name_list.remove(company_name)

        files_financialstatements = list_files_in_folder(financialstatements_folder_id)

        # 검토용 자료 만들기
        phase1_output = ocr2_phase1(normalized_company_name_list, files_financialstatements)

        # ocr2_phase1는 딕셔너리입니다
        # ocr2_phase1의 Key나 value에 'error'가 존재하는 경우 해당 요소를 삭제합니다
        # 유지 보수 - 생각해야 함
        remove_error_entries(phase1_output)

        msg = 'OCR2_phase1이 끝났습니다. 다음 스프레드 시트의 결과를 확인해주세요. https://docs.google.com/spreadsheets/d/1sKbhatzVFQKABl2dh1xaRZwbzFYARiPJLZ2MYMtVG2Y/ \n. \
        다음 항목은 Mapping DB에 없는 실제항목입니다. 없는 항목이 존재하는 경우 경우 항목을 추가해주세요.\n'
        send_direct_message_to_user(user_id, msg)

        for company_name, missing_items in phase1_output.items():
            # 없는 항목을 문자열 형태로 만듦
            missing_items_str = ", ".join(missing_items) if missing_items else "없음"
            
            # 메시지 생성
            msg = f"회사명 : {company_name}\n없는 항목 : {missing_items_str}\n\n"
            send_direct_message_to_user(user_id, msg)
        
        # 기존의 상태는 해제해야 함
        if user_id in GlobalState.user_responses:
            del GlobalState.user_responses[user_id]
        if user_id in GlobalState.user_states:
            del GlobalState.user_states[user_id]
        return
    elif user_responses[user_id] == 'OCR_2_2':
        msg = (f'<@{user_id}> 님  OCR_2_2번 기능을 실행합니다')
        send_direct_message_to_user(user_id, msg)

        # OCR_2_2
        mapping_db_id = config.mapping_db_id # Mapping_DB
        validation_id = config.validation_id # 검토용 자료        

        # validation_id all cells
        val_all_cells_pd = get_all_key_cells_per_cp(validation_id)
        # 대분류, 중분류, 소분류, 실제항목값으로 구성된 배열을 먼저 생성합니다
        ocr2_2_json_array = build_json_array_with_separation(val_all_cells_pd, mapping_db_id)
        save_json_array_to_file(ocr2_2_json_array, file_name="ocr2_result.json")

        # 검토용 자료, 실제 항목 비교 (실제로 업데이트가 완전하게 되었는지 확인하기)
        missing_items_dict = check_missing_items_in_actual_items(val_all_cells_pd, mapping_db_id)
        # 없는 항목이 대분류, 중분류, 소분류에 존재하는지 확인합니다
        all_categories_set = extract_categories("ocr2_result.json")
        
        # mapping_db_id에서 '제외항목' 시트에 존재하는 모든 값을 리스트로 반환합니다
        flattened_list = get_all_data_as_flat_list(mapping_db_id)
        # print(f'flattened : {flattened_list}')

        final_missing_items_dict = second_check_missing_items(missing_items_dict, all_categories_set, flattened_list)
        # print(f'final_missing : {final_missing_items_dict}')

        # 그래도 일치하지 않는 값이 존재하는 경우에는 프로그램 종료
        if final_missing_items_dict:
            msg = (f"검토용 자료와 실제항목이 일치하지 않습니다.아래의 항목을 확인해주세요.\n")
            send_direct_message_to_user(user_id, msg)

            for company, missing_items in final_missing_items_dict.items():
                msg = (f"회사명: {company}\n누락된 항목: {', '.join(missing_items)}")
                send_direct_message_to_user(user_id, msg)

            if user_id in GlobalState.user_responses:
                del GlobalState.user_responses[user_id]
            if user_id in GlobalState.user_states:
                del GlobalState.user_states[user_id]
            return
        # ocr2_2_json_array = build_json_array_with_separation(val_all_cells_pd, mapping_db_id)
        # save_json_array_to_file(ocr2_2_json_array, file_name="ocr2_result.json")
        processed_ocr2_2_json_array = restructure_json_array(ocr2_2_json_array)
        save_json_array_to_file(processed_ocr2_2_json_array, file_name="ocr2_processed_result.json")

        # Test
        # test_cells_pd = convert_json_to_val_all_cells('test_ocr2.json')
        # test_json_array = build_json_array_with_separation(test_cells_pd, mapping_db_id)
        # save_json_array_to_file(test_json_array, file_name="ocr2_test_result.json")

        # 수식상 필요한 값이 없는지 확인
        result_json, equation_prompt, using_item = get_info_equation_sheet()
        result_json = dict(OrderedDict({'회사명': "", **result_json}))
        n, ft_json_list = filtering_jsonlist(processed_ocr2_2_json_array, using_item)
        print(n)

        if n == 0 :
            result = merge_and_deduplicate(ft_json_list)
            msg = '수식을 계산하기 위해 필요한 항목 중 다음 항목이 없습니다 :'
            send_direct_message_to_user(user_id, msg)

            for company_name, missing_operator in result.items():
                # 없는 항목을 문자열 형태로 만듦
                missing_operators_str = ", ".join(missing_operator) if missing_operator else "없음"
                
                # 메시지 생성
                msg = f"회사명 : {company_name}\n없는 항목 : {missing_operators_str}\n\n"
                send_direct_message_to_user(user_id, msg)

            if user_id in GlobalState.user_responses:
                del GlobalState.user_responses[user_id]
            if user_id in GlobalState.user_states:
                del GlobalState.user_states[user_id]  
            
            return          
        else:
            print(ft_json_list)
            final_output = []
            for ft_js in ft_json_list:
                output = ocr2_phase2_gpt(result_json, equation_prompt,ft_js)
                final_output.append(output)
            print(final_output)
            write_to_google_sheet(final_output)

            msg = 'OCR2가 완료되었습니다. 결과를 확인해주세요.\n https://docs.google.com/spreadsheets/d/1_jeDPUEAIhmUqwKEzGliuojkJ2UqRe8JvZCd9C2I4U8/ '
            send_direct_message_to_user(user_id, msg)
            
            if user_id in GlobalState.user_responses:
                del GlobalState.user_responses[user_id]
            if user_id in GlobalState.user_states:
                del GlobalState.user_states[user_id]
            return

    elif user_responses[user_id] == 'OCR_2':
        msg = (f'<@{user_id}> 님  OCR_2번 기능을 실행합니다')
        send_direct_message_to_user(user_id, msg)
        choice_multiple_selection_in_ocr_2(user_id, channel_id, client, content='OCR 1 - 2 중 하나를 선택해주세요')
        return

    
    # ocr 시작하시겠습니까? - 1번 혹은 2번을 선택해주세요
    if user_states[user_id] == 'ocr_1_or_2':
        choice_multiple_ocr_selection(user_id, channel_id, client, content='OCR 1 또는 2 중 하나를 선택해주세요')

    # 예전 아카이브 코드 (참고용 코드로 실제로 적용되지 않는 코드를 말함)
    ####### ARCHIVE ######
    if user_states[user_id] == 'ocr_start':
        for i in range(2): 
            time.sleep(2)  

        pr_existing_names, pr_not_found_names, fs_existing_names, fs_not_found_names, sh_existing_names, sh_not_found_names, \
            property_registry_id, financial_statement_id, sharedholder_list_id = compare_controller(parent_folder_id=ocr_parent_id)
        
        global_property_registry_id = property_registry_id # 등기부등본 폴더 ***************************************
        global_financial_statement_id = financial_statement_id # 재무제표 폴더 *******************************
        global_sharedholder_list_id = sharedholder_list_id # 주주명부 폴더 *****************************

        # 주주명부 등기부등본 올바른 이름들 중에서 공통 기업명, 공통되지 않은 기업명
        # 올바른 기업명 내에서 공통되는 기업, 공통되지 않은 기업명 반환 (shareholder, property_registry)
        common_names_pr_and_sh, only_in_pr, only_in_sh = compare_prefix_lists(pr_existing_names, sh_existing_names)

        global_common_names_pr_and_sh = common_names_pr_and_sh # 등기부등본, 주주명부 공통 기업명 *******************************

        # 주주명부 등기부등본의 공통된 기업명 | 등기부등본 올바른 기업명 | 주주명부 올바른 기업명
        msg = show_comparison_results(common_names_pr_and_sh, pr_existing_names, sh_existing_names)
        send_direct_message_to_user(user_id, msg)

        # 등기부등본의 잘못된 이름 | 주주명부의 잘못된 이름
        msg = show_not_found_results(pr_not_found_names, sh_not_found_names)
        send_direct_message_to_user(user_id, msg)
        
        # 재무제표의 올바른 이름 | 재무제표의 잘못된 이름
        msg = show_found_and_not_found_results(fs_existing_names, fs_not_found_names)
        send_direct_message_to_user(user_id, msg)
        
        # On progress?
        check_yes_or_no_progress(user_id, channel_id, client, content='OCR 프로그램을 진행하시겠습니까?')

    elif user_states[user_id] == 'ocr_progress': # Make Selection ( 1 - 4)
        # 진행하시겠습니까? - 예 
        msg = (f"다음의 선택지 중 하나를 입력해주세요.\n"
               "1. 주주명부, 등기부등본 - 텍스트 추출\n"
               "2. 주주명부, 등기부등본 - 검토 및 DB 반영\n"
               "3. 재무제표 - 텍스트 추출\n"
               "4. 재무제표 - 검토 및 DB 반영\n"
               )
        send_direct_message_to_user(user_id, msg)
        user_states[user_id] = 'ocr_handler' # Now it will be not changed. Only user_responses
        user_responses[user_id] = 'ocr_selection'

    

