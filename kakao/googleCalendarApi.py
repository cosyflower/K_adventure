from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import json
import config

# 구글 캘린더 API 인증 정보 설정
SCOPES = ['https://www.googleapis.com/auth/calendar']
credentials = service_account.Credentials.from_service_account_file(
        config.kakao_json_key_path, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)

def string_to_strptime(date_string):
    return datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M")

def set_out_of_office_event(user_id, start_date, end_date, summary='Out of Office', email=''):
    # 날짜 및 시간 포맷 설정
    start_datetime = datetime.datetime.combine(start_date, datetime.time.min).isoformat() + 'Z'
    end_datetime = datetime.datetime.combine(end_date, datetime.time.max).isoformat() + 'Z'

    # 캘린더 이벤트 생성
    event = {
        'summary': summary,
        'description': f'User {user_id} is out of office. Email: {email}',
        'start': {
            'dateTime': start_datetime,
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': 'UTC',
        },
        'transparency': 'transparent',
        'visibility': 'private'
    }

    event_result = service.events().insert(calendarId='primary', body=event).execute()
    print(f'Event created: {event_result.get("htmlLink")}')


def list_calendar_ids():
    # 캘린더 목록 가져오기
    calendar_list = service.calendarList().list().execute()
    
    calendar_ids = []
    
    for calendar_list_entry in calendar_list['items']:
        print(f"Calendar Summary: {calendar_list_entry['summary']}, Calendar ID: {calendar_list_entry['id']}")
        calendar_ids.append(calendar_list_entry['id'])
    
    return calendar_ids

list_calendar_ids()

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