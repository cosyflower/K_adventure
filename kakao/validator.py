def validate_name(name):
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