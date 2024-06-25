from formatting import process_user_input, get_proper_file_name
import googleapi
import gspread
import chatgpt
import json
import get_slack_user_info

def security_system_user_function_handler(message, say, user_states, security_system_user_info_list, security_system_advisor_user_info_list):
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
            elif user_input==4: # 권한 변경된 사용자 조회
                if is_fake_advisor(user_id) or is_real_advisor(user_id):
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
                else:
                    say(f"<@{user_id}> 권한이 없습니다.")
                    del user_states[user_id]
            elif user_input==5: # 권한 변경
                if is_fake_advisor(user_id) or is_real_advisor(user_id):
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
                    user_states[user_id] = 'security_system_waiting_authority_category'
                    security_system_user_info_list[user_id] = user_details
                else:
                    say(f"<@{user_id}> 권한이 없습니다.")
                    del user_states[user_id]
            elif user_input==2: # 신규 사용자 권한 배정
                get_slack_user_info.update_authority()
                say(f"<@{user_id}> 신규 사용자 권한 배정이 끝났습니다. 종료합니다.")
                del user_states[user_id]
            elif user_input==3: # 사용자 권환 조회
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
            elif user_input==6: # 임시 관리자 배정
                if is_real_advisor(user_id):
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
                    say(f"<@{user_id}> 관리자 권한을 부여할 사용자의 번호를 입력해주세요(번호만 입력해주세요){choice}\n(종료를 원하시면 '종료'를 입력해주세요)")
                    user_states[user_id] = 'security_system_advisor_authority_make'
                    security_system_advisor_user_info_list[user_id] = user_details
                else:
                    say(f"<@{user_id}> 권한이 없습니다.")
                    del user_states[user_id]
            elif user_input==7: # 임시 관리자 목록 조회
                if is_real_advisor(user_id):
                    comment = ""
                    with open("advisor_list.json", 'r', encoding='utf-8') as file:
                        advisor_list = json.load(file)
                    for i,(id, name) in enumerate(advisor_list.items()):
                        comment = comment + f"{i+1}. {name}({id})\n"
                    say(f"<@{user_id}> 현재 임시 관리자 목록은 다음과 같습니다\n{comment}\n목록 조회가 끝났습니다")
                    del user_states[user_id]
                else:
                    say(f"<@{user_id}> 권한이 없습니다.")
                    del user_states[user_id]
            elif user_input==8: # 임시 관리자 회수
                if is_real_advisor(user_id):
                    comment = ""
                    with open("advisor_list.json", 'r', encoding='utf-8') as file:
                        advisor_list = json.load(file)
                    user_details = []
                    for i,(id, name) in enumerate(advisor_list.items()):
                        comment = comment + f"{i+1}. {name}({id})\n"
                        user_details.append({'name': name, 'id': id})
                    say(f"<@{user_id}> 임시 관리자 권한을 회수할 사용자의 번호를 입력해주세요(번호만 입력해주세요)\n{comment}(종료를 원하시면 '종료'를 입력해주세요)")
                    user_states[user_id] = 'security_system_advisor_authority_delete'
                    security_system_advisor_user_info_list[user_id] = user_details
                else:
                    say(f"<@{user_id}> 권한이 없습니다.")
                    del user_states[user_id]
            else:
                say(f"<@{user_id}> 정확한 숫자를 입력해주세요")
                user_states[user_id] = 'security_system_waiting_function_number'
        else:
            say(f"<@{user_id}> 숫자만 입력해주세요")
            user_states[user_id] = 'security_system_waiting_function_number'

def security_system_authority_category_handler(message, say, user_states, security_system_user_info_list, security_system_advisor_user_info_list):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        say(f"<@{user_id}> 종료합니다.")
        del user_states[user_id]
    else:
        user_details = security_system_user_info_list[user_id]
        user_num = len(user_details)
        if user_input.isdigit():
            user_input = int(user_input)
            if (user_input > user_num) or (user_input < 0):
                say(f"<@{user_id}> 보기에 있는 숫자만 입력해주세요")
                user_states[user_id] = 'security_system_waiting_authority_category'
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
                user_states[user_id] = 'security_system_json_file'
                security_system_user_info_list[user_id] = data
        else:
            say(f"<@{user_id}> 숫자만 입력해주세요")
            user_states[user_id] = 'security_system_waiting_authority_category'

def security_system_authority_update_json_file_handler(message, say, user_states, security_system_user_info_list, security_system_advisor_user_info_list):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        say(f"<@{user_id}> 종료합니다.")
        del user_states[user_id]
    else:
        data = security_system_user_info_list[user_id]
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
                del user_states[user_id]
                del security_system_user_info_list[user_id]
        else:
            say(f"<@{user_id}> 숫자만 입력해주세요")
            user_states[user_id] = 'authority_update_json_file'
            
def security_system_advisor_authority_make_handler(message, say, user_states, security_system_user_info_list, security_system_advisor_user_info_list):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        say(f"<@{user_id}> 종료합니다.")
        del user_states[user_id]
    else:
        user_details = security_system_advisor_user_info_list[user_id]
        user_num = len(user_details)
        if user_input.isdigit():
            user_input = int(user_input)
            if (user_input > user_num) or (user_input < 0):
                say(f"<@{user_id}> 보기에 있는 숫자만 입력해주세요")
                user_states[user_id] = 'security_system_advisor_authority_make'
            else:
                data = user_details[user_input-1]
                real_name = data['real_name']
                id = data['id']
                with open("advisor_list.json", 'r') as file:
                    advisor_list = json.load(file)
                advisor_list[id] = real_name
                with open("advisor_list.json", 'w') as file:
                    json.dump(advisor_list, file, indent=4)
                say(f"<@{user_id}> {real_name}({id}) 님에게 관리자 권한을 부여했습니다.")
                comment = ""
                with open("advisor_list.json", 'r', encoding='utf-8') as file:
                    advisor_list = json.load(file)
                for i,(id, name) in enumerate(advisor_list.items()):
                    comment = comment + f"{i+1}. {name}({id})\n"
                say(f"<@{user_id}> 현재 임시 관리자 목록은 다음과 같습니다\n{comment}\n목록 조회가 끝났습니다")
                del user_states[user_id]
                del security_system_advisor_user_info_list[user_id]
        else:
            say(f"<@{user_id}> 숫자만 입력해주세요")
            user_states[user_id] = 'security_system_advisor_authority_make'

def security_system_advisor_authority_delete_handler(message, say, user_states, security_system_user_info_list, security_system_advisor_user_info_list):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        say(f"<@{user_id}> 종료합니다.")
        del user_states[user_id]
    else:
        user_details = security_system_advisor_user_info_list[user_id]
        user_num = len(user_details)
        if user_input.isdigit():
            user_input = int(user_input)
            if (user_input > user_num) or (user_input < 0):
                say(f"<@{user_id}> 보기에 있는 숫자만 입력해주세요")
                user_states[user_id] = 'security_system_advisor_authority_delete'
            else:
                data = user_details[user_input-1]
                name = data['name']
                id = data['id']
                with open("advisor_list.json", 'r', encoding='utf-8') as file:
                    advisor_list = json.load(file)
                del advisor_list[id]
                with open("advisor_list.json", 'w', encoding='utf-8') as file:
                    json.dump(advisor_list, file, indent=4)
                say(f"<@{user_id}> {name}({id}) 님에게 관리자 권한을 삭제합니다")
                comment = ""
                with open("advisor_list.json", 'r', encoding='utf-8') as file:
                    advisor_list = json.load(file)
                for i,(id, name) in enumerate(advisor_list.items()):
                    comment = comment + f"{i+1}. {name}({id})\n"
                say(f"<@{user_id}> 현재 임시 관리자 목록은 다음과 같습니다\n{comment}\n목록 조회가 끝났습니다")
                del user_states[user_id]
                del security_system_advisor_user_info_list[user_id]
        else:
            say(f"<@{user_id}> 숫자만 입력해주세요")
            user_states[user_id] = 'security_system_advisor_authority_delete'


def get_user_authority(user_id):
    with open("users_info.json", 'r', encoding='utf-8') as file:
        users_info_list = json.load(file)
    return users_info_list[user_id]['authority']

def is_fake_advisor(user_id):
    with open("advisor_list.json", 'r', encoding='utf-8') as file:
        advisor_list = json.load(file)
    return user_id in advisor_list

def is_real_advisor(user_id):
    return user_id == "U072MMSHFGR"


    