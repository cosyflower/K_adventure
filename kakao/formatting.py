from datetime import datetime
import re

"""
형식 선언 관련 .py 파일
"""
def process_user_input(user_input):
    # 이메일 입력했을 때 mailto: 가 앞에 붙여나가는 현상제거해야 함
    return re.split(r'>\s*', user_input, maxsplit=1)[-1].strip()

# 휴가 연도 파악 - Basic_Template을 복사하고 난 이후 파일명은 다음과 같음
# "연차/반차_" + 추출된 연도 형태로 추출
def create_leave_string(year):
    return f"연차/반차_{year}"

# 휴가 데이터가 들어오면 create_.. 활용해서 파일명
# 2024년 휴가 시작 - 연차/반차_2024
# 2025년 휴가 시작 - 연차/반차_2025
def get_proper_file_name(new_vacation_data):
    # 2024. 10. 19 오전 10:00:00
    start_date = new_vacation_data[2]
    year = start_date[:4]
    return create_leave_string(year)



def get_current_year():
    # 현재 날짜와 시간 가져오기
    now = datetime.now()
    # 현재 연도 추출
    current_year = now.year
    return current_year

def process_and_extract_email(input_string):
    # '<'와 '>'를 제거
    if input_string.startswith('<') and input_string.endswith('>'):
        input_string = input_string[1:-1]
    else:
        return None
    
    # '|'를 기준으로 문자열을 분할
    parts = input_string.split('|')
    
    # 분할된 문자열 중 두 번째 부분을 반환
    if len(parts) > 1:
        return parts[1]
    return None