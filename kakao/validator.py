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
        # 추후 삭제 - 입력을 확인하기 위해서 임시 print
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
        if datetime.strptime(comparison_date_str, '%Y-%m-%d') <= datetime.strptime(date_str, '%Y-%m-%d'):
            return True
        else:
            return False
    
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