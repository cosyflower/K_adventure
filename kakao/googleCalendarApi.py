from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import json
import config
import pytz

# 구글 캘린더 API 인증 정보 설정
SCOPES = ['https://www.googleapis.com/auth/calendar']
credentials = service_account.Credentials.from_service_account_file(
        config.kakao_json_key_path, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)

def string_to_strptime(date_string):
    return datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M")

# def set_out_of_office_event(user_id, start_date, end_date, summary='Out of Office', email=''):

#     # 구글 캘린더 API 인증 정보 설정
#     SCOPES = ['https://www.googleapis.com/auth/calendar']
#     credentials = service_account.Credentials.from_service_account_file(
#             config.kakao_json_key_path, scopes=SCOPES)
#     service = build('calendar', 'v3', credentials=credentials)

#     # 날짜 문자열을 datetime 객체로 변환
#     start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M')
#     end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d %H:%M')

#     # datetime 객체를 ISO 8601 형식으로 변환
#     start_datetime = start_date.isoformat() + 'Z'
#     end_datetime = end_date.isoformat() + 'Z'

#     # 캘린더 이벤트 생성
#     event = {
#         'summary': summary,
#         'description': f'User {user_id} is out of office. Email: {email}',
#         'start': {
#             'dateTime': start_datetime,
#             'timeZone': 'UTC',
#         },
#         'end': {
#             'dateTime': end_datetime,
#             'timeZone': 'UTC',
#         },
#         'transparency': 'transparent',
#         'visibility': 'private'
#     }

#     event_result = service.events().insert(calendarId=config.google_calendar_id, body=event).execute()
#     print(f'Event created: {event_result.get("htmlLink")}')


def list_calendar_ids():
    # 캘린더 목록 가져오기
    calendar_list = service.calendarList().list().execute()
    calendar_ids = []
    
    for calendar_list_entry in calendar_list['items']:
        print(f"Calendar Summary: {calendar_list_entry['summary']}, Calendar ID: {calendar_list_entry['id']}")
        calendar_ids.append(calendar_list_entry['id'])
    
    return calendar_ids


def set_out_of_office_event(user_id, start_date, end_date, summary='Out of Office', email=''):
    # 날짜 문자열을 datetime 객체로 변환
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M')
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d %H:%M')

    # 한국 시간대로 변환
    seoul_tz = pytz.timezone('Asia/Seoul')
    start_date = seoul_tz.localize(start_date)
    end_date = seoul_tz.localize(end_date)

    # datetime 객체를 ISO 8601 형식으로 변환
    start_datetime = start_date.isoformat()
    end_datetime = end_date.isoformat()

    # 캘린더 이벤트 생성
    event = {
        'summary': summary,
        'description': f'User {user_id} is out of office. Email: {email}',
        'start': {
            'dateTime': start_datetime,
            'timeZone': 'Asia/Seoul',
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': 'Asia/Seoul',
        },
        'transparency': 'transparent',
        'visibility': 'private'
    }

    # 캘린더 ID 출력 (디버깅용)
    print(f"Calendar ID: {config.google_calendar_id}")

    # 이벤트 삽입
    try:
        event_result = service.events().insert(calendarId=config.google_calendar_id, body=event).execute()
        print(f'Event created: {event_result.get("htmlLink")}')
    except Exception as e:
        print(f"An error occurred: {e}")

# 예시 사용법
set_out_of_office_event("U05R7FD8Y85", '2024-07-13 09:00', '2024-07-13 19:00')

# # 시작 날짜와 끝나는 날짜 설정
# start_date_formatted = to_specific_date(user_vacation_info[user_id][0]).lstrip("'")
# end_date_formatted = to_specific_date(user_vacation_info[user_id][1]).lstrip("'")
# vacation_type = user_vacation_info[user_id][2]
# reason = user_vacation_info[user_id][3]
# specific_reason = user_vacation_info[user_id][4]
# email = get_display_name(user_id, 'users_info.json') + '@kakaventures.com'

# new_row_data = [
#     datetime.datetime.now().isoformat(),
#     get_real_name_by_user_id(user_id, 'users_info.json'),
#     start_date_formatted,
#     end_date_formatted,
#     vacation_type,
#     reason,
#     specific_reason,
#     email
# ]

# # 구글 캘린더에 부재중 알림 설정
# set_out_of_office_event(user_id, start_date_formatted, end_date_formatted, 'Out of Office', email)