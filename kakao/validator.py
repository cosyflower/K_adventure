import re
from datetime import datetime

###### 새로 추가된 validator.py 파일
##### 해당 파일에서는 검증 관련 함수만 넣을 예정

"""
* 예외 처리 관련 함수들을 모아둔 Module
* Process for validating inputs depending on proper format such as Date or name

"""

def is_validate_name(name):
    """
    이름을 검증하는 함수.
    
    :param name: str, 입력받은 이름
    :return: bool, 이름이 유효한 경우 True, 그렇지 않은 경우 False
    :raises ValueError: 이름이 유효하지 않은 경우 예외 발생
    """
    if not name:
        raise ValueError("이름이 비어 있습니다. 유효한 이름을 입력해주세요.")
    
    if any(char.isdigit() for char in name):
        raise ValueError("이름에 숫자가 포함되어 있습니다. 유효한 이름을 입력해주세요.")
    
    # 다른 검증 조건을 추가할 수 있습니다.
    
    return True

def is_valid_date(date_str, comparison_date_str=None):
    # 정규식 패턴 정의 (YYYY-MM-DD HH:MM)
    date_pattern = r'^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]) ([01]\d|2[0-3]):[0-5]\d$'
    # date_str 형식 검증
    if not re.match(date_pattern, date_str):
        return False
    # 날짜 및 시간 유효성 검사
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
    except ValueError:
        return False
    # comparison_date_str이 주어졌을 때의 처리
    if comparison_date_str:
        if not re.match(date_pattern, comparison_date_str):
            return False
        try:
            comparison_date_obj = datetime.strptime(comparison_date_str, '%Y-%m-%d %H:%M')
        except ValueError:
            return False
        # date_str이 comparison_date_str 이상인지 비교
        return date_obj >= comparison_date_obj
    # comparison_date_str이 없는 경우 형식이 올바른지 여부 반환
    return True
    

def is_valid_vacation_sequence(vacation_seqence):
    # 정규식 - 수 입력했는지 확인하기
    if re.fullmatch(r'\d+', vacation_seqence):
        reason_sequence = int(vacation_seqence)
        if 1 <= reason_sequence <= 5:
            return True
    
    return False

def is_valid_vacation_reason_sequence(vacation_reason_sequence):
    # 정규식 - 수 입력되었는지 확인하기
    if re.fullmatch(r'\d+', vacation_reason_sequence):
        reason_sequence = int(vacation_reason_sequence)
        if 1 <= reason_sequence <= 8:
            return True
    
    return False

def is_valid_email(email):
    # 이메일 형식을 검증하기 위한 정규식 패턴
    # 추후 삭제 - 입력을 확인하기 위해서 임시 print
    print(email)
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

    # 정규식 패턴과 일치하는지 확인
    if re.match(pattern, email):
        return True
    else:
        return False
    
def is_valid_confirm_sequence(confirm_sequence):
    if re.fullmatch(r'\d+', confirm_sequence):
        reason_sequence = int(confirm_sequence)
        if reason_sequence <= 1:
            return True
    
    return False