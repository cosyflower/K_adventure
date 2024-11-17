class GlobalState:
    #slack_bot에 사용되는 변수
    user_states = {}
    user_input_info = {}

    #문서 4종 생성에 사용되는 변수
    inv_list_info = {}
    inv_info = {}

    # 보안 시스템에 사용되는 변수
    security_system_user_info_list = {}
    security_system_advisor_user_info_list = {}

    # 연차 프로세스를 실행한 적 없을 때 딕셔너리 내 값 생성
    user_vacation_status = {}
    user_vacation_info = {}
    # 휴가 취소 프로세스
    cancel_vacation_status = {}
    # 사용자의 응답을 저장할 딕셔너리
    user_responses = {}