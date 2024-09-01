from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import json
import config
import pytz
import re


# 구글 캘린더 API 인증 정보 설정
SCOPES = ['https://www.googleapis.com/auth/calendar']
credentials = service_account.Credentials.from_service_account_file(
        config.kakao_json_key_path, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)

def extract_name_before_number(name):
    # 정규식을 사용하여 숫자가 등장하기 전까지의 문자열을 추출
    result = re.match(r'^[^\d]*', name)
    return result.group(0) if result else name

# 2024-01-01 10:00
def string_to_strptime(date_string):
    return datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M")

# 2024.01.01 10:00:00
def string_to_strptime_on_row_data(row_date_string):
    return datetime.datetime.strptime(row_date_string, "%Y.%m.%d %H:%M:%S")

# JSON 파일을 확인하여 user_id에 맞는 데이터를 탐색하고 display_name을 반환한다
def get_display_name(user_id, file_path='users_info.json'):
    # JSON 파일을 열고 데이터를 읽음
    with open(file_path, 'r', encoding='utf-8') as file:
        users_data = json.load(file)
    
    # user_id에 해당하는 사용자 데이터 찾기
    if user_id in users_data:
        return extract_name_before_number(users_data[user_id].get('name'))
    else:
        print(f"User ID {user_id} not found in data")

def set_out_of_office_event(user_id, start_date, end_date, summary='Out of Office', email='', reason=''):
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

    # # 캘린더 이벤트 생성
    # event = {
    #     'summary': summary,
    #     'start': {
    #         'dateTime': start_datetime,
    #         'timeZone': 'Asia/Seoul',
    #     },
    #     'end': {
    #         'dateTime': end_datetime,
    #         'timeZone': 'Asia/Seoul',
    #     },
    #     'transparency': 'opaque',
    #     'visibility': 'private',
    #     'eventType': 'outOfOffice'
    # }
    

    #---------------------------------#
    # Should test this logic!!!!!!!!

    summary = reason
    if reason == '보건휴가':
        summary = '병결'

    # 병결 이벤트(슬롯) 생성
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
        'eventType': 'outOfOffice',
        'extendedProperties': {
            'private': {
                'declineNewInvites': 'true',  # 새로운 회의 거부 설정
            }
        }
    }

    # 이벤트 생성
    created_event = service.events().insert(calendarId=get_display_name(user_id, 'users_info.json') + '@kakaoventures.co.kr', body=event).execute()
    # print(f"Created out of office event: {created_event.get('htmlLink')}")

    # 해당 날짜의 기존 회의 상태 변경 (거부로 설정)
    events_result = service.events().list(
        calendarId= get_display_name(user_id, 'users_info.json') + '@kakaoventures.co.kr',
        timeMin=start_datetime,  # KST (Korea Standard Time)
        timeMax=end_datetime,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    for event in events:
        attendees = event.get('attendees', [])
        for attendee in attendees:
            if attendee.get('email').endswith('@kakaoventures.co.kr'):
                attendee['responseStatus'] = 'declined'
                try:
                    # 회의 상태 업데이트
                    service.events().patch(
                        calendarId=get_display_name(user_id, 'users_info.json') + '@kakaoventures.co.kr', 
                        eventId=event['id'], 
                        body={'attendees': attendees}
                    ).execute()
                    # print(f"Set declined status for meeting: {event.get('summary')}")
                except Exception as e:
                    pass
    # }
    #---------------------------------#

    # 이벤트 삽입
    # try:
    #     event_result = service.events().insert(calendarId=get_display_name(user_id, 'users_info.json') + '@kakaoventures.co.kr', body=event).execute()
    # except Exception as e:
    #     print(f"An error occurred: {e}")

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
    # try:
    #     events_result = service.events().list(
    #         calendarId=get_display_name(user_id, 'users_info.json') + '@kakaoventures.co.kr',
    #         timeMin=start_datetime,
    #         timeMax=end_datetime,
    #         singleEvents=True,
    #         orderBy='startTime'
    #     ).execute()

    #     events = events_result.get('items', [])
    #     for event in events:
    #         if event.get('eventType') == 'outOfOffice':
    #             try:
    #                 service.events().delete(calendarId=get_display_name(user_id, 'users_info.json') + '@kakaoventures.co.kr', eventId=event['id']).execute()
    #             except Exception as e:
    #                 print(f"An error occurred while deleting the event: {e}")
    # except Exception as e:
    #     print(f"An error occurred while retrieving events: {e}")
  
    # 병결 이벤트 삭제
    events_result = service.events().list(
        calendarId=get_display_name(user_id, 'users_info.json') + '@kakaoventures.co.kr',
        timeMin=start_datetime,  # KST (Korea Standard Time)
        timeMax=end_datetime,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    for event in events:
        # 병결 이벤트인 경우 삭제
        if event.get('eventType') == 'outOfOffice':
            try:
                service.events().delete(
                    calendarId=get_display_name(user_id, 'users_info.json') + '@kakaoventures.co.kr', 
                    eventId=event['id']
                ).execute()
                # print(f"Deleted out of office event: {event.get('summary')}")
            except Exception as e:
                # print(f"Failed to delete out of office event: {event.get('summary')}. Error: {e}")
                pass
        
        # 기존 회의 상태 복원
        attendees = event.get('attendees', [])
        for attendee in attendees:
            if attendee.get('email').endswith('@kakaoventures.co.kr') and attendee.get('responseStatus') == 'declined':
                attendee['responseStatus'] = 'accepted'
                try:
                    # 회의 상태 업데이트
                    service.events().patch(
                        calendarId=get_display_name(user_id, 'users_info.json') + '@kakaoventures.co.kr', 
                        eventId=event['id'], 
                        body={'attendees': attendees}
                    ).execute()
                    # print(f"Restored participation in meeting: {event.get('summary')}")
                except Exception as e:
                    # print(f"Failed to restore meeting: {event.get('summary')}. Error: {e}")
                    pass

# 예시 사용법
# 자신의 user_id가 들어간다고 생각하기
# set_out_of_office_event("U05R7FD8Y85", '2024-07-13 09:00', '2024-07-13 19:00')
# delete_out_of_office_event("U05R7FD8Y85", '2024-07-13 09:00', '2024-07-13 19:00')
# print(string_to_strptime_on_row_data('2024.05.05 10:00:00'))