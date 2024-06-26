"""
개발 과정 중 정의했지만, 추후에 사용하지 않는 코드들을 모아둔 .py 파일
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