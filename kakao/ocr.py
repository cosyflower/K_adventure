from formatting import process_user_input
from directMessageApi import send_direct_message_to_user

from ocr_controller import compare_prefix_lists, ocr_handler, compare_controller
from ocr_view import show_comparison_results, show_not_found_results, show_found_and_not_found_results, check_yes_or_no_progress

import config
import time

import OCR_financialstatements 

# global variables
# ocr_parent_id = config.ocr_parent_id ### 실제 배포하는 폴더 
ocr_parent_id = config.ocr_test_parent_id ### 테스트 폴더 

global_property_registry_id = '' # 등기부등본 폴더 
global_financial_statement_id = '' # 재무제표 폴더
global_shareholder_list_id = '' # 주주명부 폴더 
global_common_names_pr_and_sh = [] # 등기부 & 주주명부 공통 기업명

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

    if user_responses[user_id] == 'ocr_selection':
        msg = (f'{user_input}번 기능을 실행합니다')
        send_direct_message_to_user(user_id, msg)

        if user_input == '1':
            # "1. 주주명부, 등기부등본 - 텍스트 추출\n"
            pass
        elif user_input == '2':
            # "2. 주주명부, 등기부등본 - 검토 및 DB 반영\n"
            pass
        elif user_input == '3':
            # "3. 재무제표 - 텍스트 추출\n"
            pass
        elif user_input == '4':
            # "4. 재무제표 - 검토 및 DB 반영\n"
            pass    
        pass

        # 수정하기 수정하기 
        
    elif user_responses[user_id] == '':
        pass

    # ocr 시작하시겠습니까? - 예 
    
    if user_states[user_id] == 'ocr_start':
        for i in range(2):  # 2번 반복
            send_direct_message_to_user(user_id, f"진행 중입니다... ")
            time.sleep(3)  # 3초마다 메시지 출력

        msg = (f"*출력 순서는 다음과 같습니다.*\n"
               "등기부등본 내 올바른 기업명 정보\n"
               "|\n"
               "주주명부에 내 올바른 기업명 정보\n"
               "|\n"
               "등기부등본과 주주명부의 올바른 기업명 중 공통된 기업명 정보\n"
               "|\n"
               "재무제표의 내 올바른 기업명 정보\n"
               "|\n"
               "재무제표의 내 올바르지 않은 기업명 정보\n"
               "|\n"
               )
        send_direct_message_to_user(user_id, msg)
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

    

