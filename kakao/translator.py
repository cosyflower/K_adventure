from datetime import datetime

def to_specific_date(date_str):
    # 문자열을 datetime 객체로 변환
    date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
    # 원하는 형식으로 변환
    date_formatted = date_obj.strftime('%Y. %-m. %-d %p %I:%M:%S')
    # 오전/오후 형식 변환
    date_formatted = date_formatted.replace('AM', '오전').replace('PM', '오후')
    return date_formatted
