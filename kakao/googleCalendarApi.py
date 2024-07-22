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

# 2024-01-01 10:00
def string_to_strptime(date_string):
    return datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M")

# 2024.01.01 10:00:00
def string_to_strptime_on_row_data(row_date_string):
    return datetime.datetime.strptime(row_date_string, "%Y.%m.%d %H:%M:%S")

def set_out_of_office_event(user_id, start_date, end_date, summary='Out of Office', email=''):
    # 날짜 문자열을 datetime 객체로 변환
    # start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M')
    # end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d %H:%M')

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
        'start': {
            'dateTime': start_datetime,
            'timeZone': 'Asia/Seoul',
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': 'Asia/Seoul',
        },
        'transparency': 'opaque',
        'visibility': 'private',
        'eventType': 'outOfOffice'
    }

    # 캘린더 ID 출력 (디버깅용)
    print(f"Calendar ID: {config.google_calendar_id}")

    # 이벤트 삽입
    try:
        event_result = service.events().insert(calendarId=config.google_calendar_id, body=event).execute()
        print(f'Event created: {event_result.get("htmlLink")}')
    except Exception as e:
        print(f"An error occurred: {e}")

def delete_out_of_office_event(user_id, start_date, end_date):
    # 날짜 문자열을 datetime 객체로 변환
    start_date = start_date.replace('오전', 'AM').replace('오후', 'PM')
    end_date = end_date.replace('오전', 'AM').replace('오후', 'PM')

    start_date = datetime.datetime.strptime(start_date, '%Y. %m. %d %p %I:%M:%S')
    end_date = datetime.datetime.strptime(end_date, '%Y. %m. %d %p %I:%M:%S')

    # 한국 시간대로 변환
    seoul_tz = pytz.timezone('Asia/Seoul')
    start_date = seoul_tz.localize(start_date)
    end_date = seoul_tz.localize(end_date)

    # datetime 객체를 ISO 8601 형식으로 변환
    start_datetime = start_date.isoformat()
    end_datetime = end_date.isoformat()

    # 이벤트 검색
    try:
        events_result = service.events().list(
            calendarId=config.google_calendar_id,
            timeMin=start_datetime,
            timeMax=end_datetime,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        for event in events:
            if event.get('eventType') == 'outOfOffice':
                # 이벤트 삭제
                try:
                    service.events().delete(calendarId=config.google_calendar_id, eventId=event['id']).execute()
                    print(f"Out of Office event deleted: {event['summary']}")
                except Exception as e:
                    print(f"An error occurred while deleting the event: {e}")
    except Exception as e:
        print(f"An error occurred while retrieving events: {e}")

# 예시 사용법
# 자신의 user_id가 들어간다고 생각하기
# set_out_of_office_event("U05R7FD8Y85", '2024-07-13 09:00', '2024-07-13 19:00')
# delete_out_of_office_event("U05R7FD8Y85", '2024-07-13 09:00', '2024-07-13 19:00')
# print(string_to_strptime_on_row_data('2024.05.05 10:00:00'))