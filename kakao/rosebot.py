from formatting import process_user_input, get_proper_file_name
import googleapi
import gspread
import chatgpt
import json
from security_system import get_user_authority
from directMessageApi import send_direct_message_to_user
from onebyone import find_oneByone

def rose_bot_handler(message, say, user_states):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)

    if user_input == '종료':
        msg = (f"로제봇 시스템을 종료합니다.\n")
        send_direct_message_to_user(user_id, msg)
        del user_states[user_id]
        return
    else:
        if user_input.isdigit():
            if user_input == "1": ## 휴가신청시스템
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
                    del user_states[user_id]
            elif user_input == "2": ## 인사 총무
                msg = (f"공사중입니다. 종료합니다.\n")
                send_direct_message_to_user(user_id, msg)
                del user_states[user_id]
            elif user_input == "3": ## 문서 4종 생성
                if get_user_authority(user_id) < 3:
                    msg = (f"문서 4종 생성을 진행합니다. 회사명을 입력해주세요 (종료를 원하시면 '종료'를 입력해주세요)")
                    send_direct_message_to_user(user_id, msg)
                    user_states[user_id] = 'docx_generating_waiting_company_name'
                else:
                    msg = (f"<@{user_id}>님은 권한이 없습니다. 종료합니다")
                    send_direct_message_to_user(user_id, msg)
                    del user_states[user_id]
            elif user_input == "4": ## 정기예금 회전 시스템
                if get_user_authority(user_id) < 3:
                    msg = ("정기예금 회전 시스템을 작동합니다. 종료를 원한다면 \'종료\'를 입력해주세요\n"
                    "1. 질문하기\n"
                    # "2. 질문하기(상위모델)\n"
                    # "3. 최종 만기일이 다가온 정기예금 상품조회\n"
                        )
                    send_direct_message_to_user(user_id, msg)
                    user_states[user_id] = 'deposit_rotation_waiting_only_number'
                    # msg = "공사중...종료합니다"
                    # send_direct_message_to_user(user_id, msg)
                    # del user_states[user_id]
                else:
                    msg = (f"<@{user_id}>님은 권한이 없습니다.")
                    send_direct_message_to_user(user_id, msg)
                    del user_states[user_id]
            elif user_input == "5": ## 회수 상황판
                msg = (f"공사중입니다. 종료합니다.\n")
                send_direct_message_to_user(user_id, msg)
                del user_states[user_id]
            elif user_input == "6": ## 검색
                msg = (f"공사중입니다. 종료합니다\n")
                send_direct_message_to_user(user_id, msg)
                del user_states[user_id]
            elif user_input == "7": ## 1on1
                if get_user_authority(user_id) < 3:
                    msg = (f"일대일매칭 기능을 진행합니다. 최신 매칭 대상을 조회합니다.\n")
                    send_direct_message_to_user(user_id, msg)
                    partner = find_oneByone(user_id)
                    # # 삭제 예정
                    # print(f"partner : {partner}")
                    msg = (f"<@{user_id}>님의 매칭 대상은 : {partner}입니다. 일대일매칭 기능을 종료합니다\n")
                    send_direct_message_to_user(user_id, msg)
                    del user_states[user_id]
                else:
                    msg = (f"<@{user_id}>님은 권한이 없습니다.")
                    send_direct_message_to_user(user_id, msg)
                    del user_states[user_id]
            elif user_input == "8": ## 보안시스템
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
                    msg = (f"<@{user_id}>님은 권한이 없습니다. 종료합니다")
                    send_direct_message_to_user(user_id, msg)
                    del user_states[user_id]
            else:
                msg = (f"잘못된 숫자를 입력했습니다. 다시 입력해주세요.\n")
                send_direct_message_to_user(user_id, msg)
                user_states[user_id] = 'rosebot_waiting_only_number'
        else:
            msg = (f"숫자만 입력해주세요. 다시 입력해주세요.")
            send_direct_message_to_user(user_id, msg)
            user_states[user_id] = 'rosebot_waiting_only_number'
            return