from datetime import datetime

# google spreadsheet에 저장되는 형태로 문자열을 변환
# input: 2024-05-05 10:00 <-> output: 2024. 05. 05 오전 10:00:00
def to_specific_date(date_str):
    # 문자열을 datetime 객체로 변환
    date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
    # 원하는 형식으로 변환
    date_formatted = date_obj.strftime('%Y. %m. %d %p %I:%M:%S')
    # 오전/오후 형식 변환
    date_formatted = date_formatted.replace('AM', '오전').replace('PM', '오후')
    return date_formatted

def format_vacation_info(data):
    start_date_str, end_date_str, vacation_type = data[2], data[3], data[4]
    # 날짜 문자열을 datetime 객체로 변환
    # '오전'과 '오후'를 'AM'과 'PM'으로 변경
    start_date_str = start_date_str.replace('오전', 'AM').replace('오후', 'PM')
    end_date_str = end_date_str.replace('오전', 'AM').replace('오후', 'PM')
    start_date = datetime.strptime(start_date_str, '%Y. %m. %d %p %I:%M:%S')
    end_date = datetime.strptime(end_date_str, '%Y. %m. %d %p %I:%M:%S')
    
    current_date = datetime.now()
    # 날짜 비교를 위해 시간 정보를 제외한 날짜 부분만 추출
    start_date_without_time = start_date.date()
    end_date_without_time = end_date.date()

    # 날짜 형식 결정
    if start_date_without_time == end_date_without_time:
        if start_date.year > current_date.year or end_date.year > current_date.year:
            date_format = start_date.strftime('%Y/%m/%d')
        else:
            date_format = start_date.strftime('%m/%d')
    else:
        if start_date.year > current_date.year or end_date.year > current_date.year:
            date_format = f"{start_date.strftime('%Y/%m/%d')} - {end_date.strftime('%Y/%m/%d')}"
        else:
            date_format = f"{start_date.strftime('%m/%d')} - {end_date.strftime('%m/%d')}"
    
    # 휴가 종류가 반반차인 경우 시간 범위 설정
    if vacation_type == '반반차(오전)':
        time_format = f"{start_date.strftime('%H:%M')}~{end_date.strftime('%H:%M')}"
        vacation_type = f"반반차({time_format})"
    elif vacation_type == '반반차(오후)':
        time_format = f"{start_date.strftime('%H:%M')}~{end_date.strftime('%H:%M')}"
        vacation_type = f"반반차({time_format})"
    
    # 결과 문자열 생성
    result = f"{date_format}, {vacation_type}"
    return result

# # 예제 데이터
# data = ['2024. 06. 18 오후 08:47:05', '황성훈', '2024. 6. 17 오후 02:00:00', '2024. 6. 17 오후 07:00:00', '반차(오후)', '예비군,민방위휴가', '', 'nokdon@naver.com']

# # 함수 호출 및 결과 출력
# print(format_vacation_info(data))
def to_cancel_sequence_list(input_string):
    # 문자열에서 공백을 제거하고 ','로 구분하여 리스트로 변환
    split_items = [int(i.strip()) for i in input_string.split(',')]
    return split_items

def convert_type_value(type_value):
    """
    주어진 type_value에 따라 값을 변환하는 함수
    1. type의 값이 "연차"인 경우 1로 변경
    2. type의 값이 "반차"로 시작하는 경우 0.5로 변경
    3. type의 값이 "반반차"로 시작하는 경우 0.25로 변경
    """
    if type_value == '연차':
        return 1
    elif type_value.startswith('반차'):
        return 0.5
    elif type_value.startswith('반반차'):
        return 0.25
    
def parse_date(date_str):
    date_str = date_str.strip("' ")
    # 날짜 문자열을 datetime 객체로 변환
    return datetime.strptime(date_str, '%Y. %m. %d %p %I:%M:%S')

def format_vacation_data(vacation_data):
    formatted_data = []
    for data in vacation_data:
        applicant = data[1]
        start_date = parse_date(data[2].replace('오전', 'AM').replace('오후', 'PM'))
        end_date = parse_date(data[3].replace('오전', 'AM').replace('오후', 'PM'))
        vacation_type = data[4]
        vacation_reason = data[5]

        # 휴가 날짜 형식 변환
        if start_date.date() == end_date.date():
            date_str = f"{start_date.strftime('%Y-%m-%d')} {start_date.strftime('%H:%M')} - {end_date.strftime('%H:%M')}"
        else:
            date_str = f"{start_date.strftime('%Y-%m-%d %H:%M')} - {end_date.strftime('%Y-%m-%d %H:%M')}"
        
        formatted_str = f"\n신청자: {applicant}\n시간: {date_str}\n휴가 종류: {vacation_type} - {vacation_reason}\n"
        formatted_data.append(formatted_str)
    
    return formatted_data