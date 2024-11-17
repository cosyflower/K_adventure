from formatting import process_user_input
from directMessageApi import send_direct_message_to_user

from ocr_controller import compare_prefix_lists, ocr_handler, compare_controller
from ocr_view import show_comparison_results, show_not_found_results, show_found_and_not_found_results, check_yes_or_no_progress , \
choice_multiple_ocr_selection, choice_multiple_selection_in_ocr_1

import config
import time

from OCR_financialstatements import list_files_in_folder, normalize_text, process_files

# global variables
# ocr_parent_id = config.ocr_parent_id ### 실제 배포하는 폴더 
ocr_parent_id = config.ocr_test_parent_id ### 테스트 폴더 

global_property_registry_id = '' # 등기부등본 폴더 
global_financial_statement_id = '' # 재무제표 폴더
global_shareholder_list_id = '' # 주주명부 폴더 
global_common_names_pr_and_sh = [] # 등기부 & 주주명부 공통 기업명

def remove_duplicates(input_list):
    return list(set(input_list))

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

    elif user_responses[user_id] == 'OCR_1_2':
        msg = (f'공사중입니다')
        send_direct_message_to_user(user_id, msg)

        pass

    elif user_responses[user_id] == 'OCR_1_3':
        # msg = (f'기능을 실행합니다')
        # send_direct_message_to_user(user_id, msg)

        for i in range(2):  # 2번 반복
            send_direct_message_to_user(user_id, f"진행중입니다... ")
            time.sleep(3)  # 3초마다 메시지 출력

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

        # 주주명부 등기부등본의 공통된 기업명 | 등기부등본 올바른 기업명 | 주주명부 올바른 기업명
        # msg = show_comparison_results(common_names_pr_and_sh, pr_existing_names, sh_existing_names)
        # send_direct_message_to_user(user_id, msg)

        # 등기부등본의 잘못된 이름 | 주주명부의 잘못된 이름
        # msg = show_not_found_results(pr_not_found_names, sh_not_found_names)
        # send_direct_message_to_user(user_id, msg)
        
        # 재무제표의 올바른 이름 | 재무제표의 잘못된 이름
        msg = show_found_and_not_found_results(fs_existing_names, fs_not_found_names)
        send_direct_message_to_user(user_id, msg)

        # 안내 멘트 - 소요 시간 멘트 띄우기
        msg = (f'처리할 기업명의 수는 {len(fs_existing_names)}개입니다. 1개의 문서 당 소요 시간은 4-5분입니다.\n'
               f'예상소요 시간은 {len(fs_existing_names) * 4}에서 {len(fs_existing_names) * 5}분입니다.'
               '진행이 완료될 때까지 대기해주세요....')
        send_direct_message_to_user(user_id, msg)
        
        # Test 끝나면 주석해제 - 테스트 코드는 주석처리
        normalized_company_name_list = [normalize_text(name) for name in fs_existing_names]
        files_financialstatements = list_files_in_folder(financial_statement_id)
        process_files(normalized_company_name_list, files_financialstatements)

        #DEBUG
        print(normalized_company_name_list)

        # 안내 멘트 - 링크 띄우기 
        msg = (f'https://docs.google.com/spreadsheets/d/1T0Hh-8cttX7KXAPGUGkDOrWyCsrI_u9zrR461dmq52k'
               '\n'
               '재무재표의 텍스트 추출이 완료되었습니다. 위의 링크를 확인해주세요!')
        send_direct_message_to_user(user_id, msg)

        # DEBUGGING
        # print(fs_existing_names)
        # print(financial_statement_id)

        ###### 테스트 코드 - 상호 코드 ########
        # financialstatements_company_name_list = ["하이로컬"] ## 기업명
        # financialstatements_folder_id = '1DSlMhSMAskZGtS1t4eNeFHlAeW7AsaLy' ## 재무제표 폴더

        # 안내 멘트 - 소요 시간 멘트 띄우기
        # msg = (f'처리할 기업명의 수는 {len(financialstatements_company_name_list)}개입니다. 1개의 문서 당 소요 시간은 4-5분입니다.\n'
        #        f'예상소요 시간은 {len(financialstatements_company_name_list) * 4}에서 {len(financialstatements_company_name_list) * 5}분입니다.'
        #        '진행이 완료될 때까지 대기해주세요....')
        # send_direct_message_to_user(user_id, msg)
        
        # 상호 코드
        # normalized_company_name_list = [normalize_text(name) for name in financialstatements_company_name_list]
        # files_financialstatements = list_files_in_folder(financialstatements_folder_id)
        # process_files(normalized_company_name_list, files_financialstatements)

        # 안내 멘트 - 링크 띄우기 
        # msg = (f'https://docs.google.com/spreadsheets/d/1T0Hh-8cttX7KXAPGUGkDOrWyCsrI_u9zrR461dmq52k'
        #        '\n'
        #        '제무재표의 텍스트 추출이 완료되었습니다. 위의 링크를 확인해주세요!')
        # send_direct_message_to_user(user_id, msg)
        ###########

    elif user_responses[user_id] == 'OCR_1_4':
        msg = (f'공사중입니다')
        send_direct_message_to_user(user_id, msg)
        pass

    elif user_responses[user_id] == 'OCR_1':
        msg = (f'<@{user_id}> 님  OCR_1번 기능을 실행합니다')
        send_direct_message_to_user(user_id, msg)
        choice_multiple_selection_in_ocr_1(user_id, channel_id, client, content='OCR 1 - 4 중 하나를 선택해주세요')
        
    elif user_responses[user_id] == 'OCR_2':
        send_direct_message_to_user(user_id, f"아직 작업중인 기능입니다. **종료해주세요('종료'를 입력해주세요)**")

    # 나중에 미리 처리하는 방식도 생각해보기


    # ocr 시작하시겠습니까? - 1번 혹은 2번을 선택해주세요
    if user_states[user_id] == 'ocr_1_or_2':
        choice_multiple_ocr_selection(user_id, channel_id, client, content='OCR 1 또는 2 중 하나를 선택해주세요')

    # 예전 아카이브 코드 (참고용 코드로 실제로 적용되지 않는 코드를 말함)
    if user_states[user_id] == 'ocr_start':
        for i in range(2):  # 2번 반복
            send_direct_message_to_user(user_id, f"진행 중입니다... ")
            time.sleep(3)  # 3초마다 메시지 출력

        # msg = (f"*출력 순서는 다음과 같습니다.*\n"
        #        "등기부등본 내 올바른 기업명 정보\n"
        #        "|\n"
        #        "주주명부에 내 올바른 기업명 정보\n"
        #        "|\n"
        #        "등기부등본과 주주명부의 올바른 기업명 중 공통된 기업명 정보\n"
        #        "|\n"
        #        "재무제표의 내 올바른 기업명 정보\n"
        #        "|\n"
        #        "재무제표의 내 올바르지 않은 기업명 정보\n"
        #        "|\n"
        #        )
        # send_direct_message_to_user(user_id, msg)
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

    

