"""
형식 선언 관련 .py 파일
"""

# 휴가 연도 파악 - Basic_Template을 복사하고 난 이후 파일명은 다음과 같음
# "연차/반차_" + 추출된 연도 형태로 추출

def create_leave_string(year):
    return f"연차/반차_{year}"