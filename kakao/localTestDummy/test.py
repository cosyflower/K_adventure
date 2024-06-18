import re
from datetime import datetime

def is_valid_email(email):
    # 이메일 형식을 검증하기 위한 정규식 패턴
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    
    # 정규식 패턴과 일치하는지 확인
    if re.match(pattern, email):
        return True
    else:
        return False

#print(is_valid_email("nokdonwithkj@naver.com"))

def is_valid_date(date_str, comparison_date_str=None):
    # 먼저 길이를 체크합니다.
    if len(date_str) != 10:
        return False
    # 정규식을 사용하여 형식이 올바른지 체크합니다.
    if not re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        return False
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return False
    
    if comparison_date_str:
        print(date_str, comparison_date_str)
        # 비교 날짜의 형식도 체크합니다.
        # end_date >= start_date 인지를 확인합니다
        if len(comparison_date_str) != 10:
            return False
        if not re.match(r'\d{4}-\d{2}-\d{2}', comparison_date_str):
            return False
        try:
            comparison_date = datetime.strptime(comparison_date_str, '%Y-%m-%d')
        except ValueError:
            return False
        
        # 날짜 비교를 수행합니다.
        # 한번 더 확인하기 (수정해야 함)
        if datetime.strptime(comparison_date_str, '%Y-%m-%d') >= datetime.strptime(date_str, '%Y-%m-%d'):
            print("문제없음")
            return True
        else:
            return False
    
    return True

is_valid_date('2024-01-01', '2024-01-01')

"""
"############# 다음은 형식입니다 #############"
"\n이름 - 휴가 시작일 - 휴가 종료일 - 휴가 종류 - 휴가 사유 - 휴가 상세 사유 - 이메일 주소\n\n"
"############# 다음은 유의 사항입니다 #############\n"
"[유의] 각각에 들어갈 내용들을 '-'로 구분합니다.\n"
"[유의] 휴가 시작일과 휴가 종료일은 YYYYMMDD로 작성하세요\n"
"[유의] 휴가 종류에 연차, 반차, 반반차오전, 반반차오후 중 하나를 택하세요\n"
"[유의] 휴가 사유에 개인, 경조, 특별, 예비군(민방위), 보건, 안식, 출산 중 하나를 택하세요\n"
"[유의] 경조, 특별, 출산휴가의 경우 휴가 상세 사유를 필수 작성하세요. (이외의 휴가는 휴가 상세 사유를 공백으로 제출해주세요)\n\n"
"############# 다음은 예시입니다 #############\n"
"[예시] *경조, 특별, 출산휴가를 선택한 경우 : 성훈 - 20240501 - 20240501 - 반반차(오후) - 결혼식 준비 - sunghun@naver.com\n"
"[예시] *이외의 경우 : 성훈 - 20240301 - 20240301 - 연차 - 개인휴가 - - sunghun@gmail.com\n"
"""