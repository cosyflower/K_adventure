import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
import locale
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import pytz
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
import shutil
import re
import copy

from translator import to_specific_date, format_vacation_info, to_cancel_sequence_list, convert_type_value, \
    format_vacation_data
from validator import is_valid_date, is_valid_vacation_sequence, is_valid_vacation_reason_sequence, \
is_valid_email, is_valid_confirm_sequence, is_valid_cancel_sequence, is_valid_vacation_purpose, is_valid_date_only_day, count_holidays
from user_commend import VACATION_SEQUENCE_TO_TYPE, VACATION_SEQUENCE_TO_REASON
from formatting import process_user_input, get_proper_file_name, create_leave_string, get_current_year, process_and_extract_email
from directMessageApi import send_direct_message_to_user
from googleCalendarApi import string_to_strptime, set_out_of_office_event, delete_out_of_office_event


"""
API 설명
"""
# JSON 파일을 확인하여 user_id에 맞는 데이터를 탐색하고 display_name을 반환한다
def get_display_name(user_id, file_path='users_info.json'):
    # JSON 파일을 열고 데이터를 읽음
    with open(file_path, 'r', encoding='utf-8') as file:
        users_data = json.load(file)
    
    # user_id에 해당하는 사용자 데이터 찾기
    if user_id in users_data:
        return users_data[user_id].get('name')
    else:
        print(f"User ID {user_id} not found in data")
    


def get_spreadsheet(spreadsheet_id, json_keyfile_path):
    # 구글 스프레드시트 API 인증 및 클라이언트 생성
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
    client = gspread.authorize(creds)
    
    # 스프레드시트 객체 반환
    return client.open_by_key(spreadsheet_id)

def get_spreadsheet_id_in_folder(file_name, folder_id):
    """
    Google 공유 Drive에서 특정 스프레드시트 파일의 ID를 가져옵니다.

    :param file_name: 찾고자 하는 스프레드시트 파일의 이름
    :param credentials_json: OAuth 2.0 클라이언트 ID가 포함된 인증 정보 파일 경로
    :return: 파일 ID 또는 None
    """
    # 서비스 계정 인증 정보 로드
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(config.kakao_json_key_path, scope)
    
    # Google Drive API 클라이언트 생성
    service = build('drive', 'v3', credentials=credentials)
    # 파일 검색 쿼리
    query = f"'{folder_id}' in parents and name = '{file_name}' and mimeType = 'application/vnd.google-apps.spreadsheet'"
    results = service.files().list(q=query, fields="files(id, name)", supportsAllDrives=True,
                                   includeItemsFromAllDrives=True).execute()
    items = results.get('files', [])
    
    if not items:
        print(f"No files found with name: {file_name} in folder: {folder_id}")
        return None
    else:
        for item in items:
            # print(f"Found file: {item['name']} (ID: {item['id']})")
            return item['id']
        
def add_row_to_sheet(spreadsheet, sheet_number, row_data): ## spreadsheet에 row_data를 append 한다
    # 전체 시트 개수를 파악
    sheet_list = spreadsheet.worksheets()
    total_sheets = len(sheet_list)
    
    # 유효하지 않은 시트 번호 예외 처리
    if sheet_number < 1 or sheet_number > total_sheets:
        raise ValueError(f"유효하지 않은 시트 번호입니다. 시트 번호는 1부터 {total_sheets} 사이여야 합니다.")
    
    # 시트 번호에 따라 해당 시트를 접근
    sheet = sheet_list[sheet_number - 1]
    sheet.append_row(row_data)

def append_data_past(spreadsheet_id, sheet_number, row_data):
    add_row_to_sheet(get_spreadsheet(spreadsheet_id, config.kakao_json_key_path), sheet_number, row_data)

def append_data(spreadsheet_id, new_row_data):
    """
    구글 스프레드시트의 첫 번째 시트에 데이터를 추가합니다.
    시트에 데이터가 없는 경우 5번째 행부터 데이터를 추가하고, 데이터가 존재하는 경우 이어서 데이터를 추가합니다.

    :param spreadsheet_id: 스프레드시트 ID
    :param new_row_data: 추가할 데이터 행
    :param credentials_json: OAuth 2.0 클라이언트 ID가 포함된 인증 정보 파일 경로
    """
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(config.kakao_json_key_path, scope)
    
    # Google Sheets API 클라이언트 생성
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    
    # 첫 번째 시트의 이름을 가져옴
    sheet_metadata = sheet.get(spreadsheetId=spreadsheet_id).execute()
    sheet_name = sheet_metadata['sheets'][0]['properties']['title']
    
    # 시트 데이터 읽기
    range_name = f'{sheet_name}!A1:Z'
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])

    if len(values) == 1:
        # 데이터가 없는 경우 5번째 행부터 추가
        range_to_append = f'{sheet_name}!A5'
    else:
        # 데이터가 있는 경우 마지막 행에 이어서 추가
        range_to_append = f'{sheet_name}!A{len(values) + 1}'
    # 데이터 추가 요청
    body = {
        'values': [new_row_data]
    }
    sheet.values().append(
        spreadsheetId=spreadsheet_id,
        range=range_to_append,
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()

def delete_row_to_sheet(spreadsheet, sheet_number, row_data):
    # row_data는 단일 레코드가 들어온다고 생각하기
    sheet_list = spreadsheet.worksheets()
    total_sheets = len(sheet_list)
    
    if sheet_number < 1 or sheet_number > total_sheets:
        raise ValueError(f"유효하지 않은 시트 번호입니다. 시트 번호는 1부터 {total_sheets} 사이여야 합니다.")
    
    sheet = sheet_list[sheet_number - 1]
    all_rows = sheet.get_all_values()
    
    for idx, row in enumerate(all_rows):
        if row == row_data:
            sheet.delete_rows(idx + 1)

def delete_data(spreadsheet_id, sheet_number, row_data):
    delete_row_to_sheet(get_spreadsheet(spreadsheet_id, config.kakao_json_key_path), sheet_number, row_data)

def get_real_name_by_user_id(user_id, json_path='users_info.json'):
    with open(json_path, 'r', encoding='utf-8') as file:
        users_info = json.load(file)
    
    for key, user_data in users_info.items():
        if user_data['id'] == user_id:
            return user_data['real_name']
    return None

def get_display_name_by_user_id(user_id, json_path='users_info.json'):
    with open(json_path, 'r', encoding='utf-8') as file:
        users_info = json.load(file)
    
    for key, user_data in users_info.items():
        if user_data['id'] == user_id:
            return user_data['display_name']
    return None

def get_data_by_real_name(sheet, real_name, attribute_sequence):
    data = sheet.get_all_values()
    matched_data = []

    if real_name is None:
        return matched_data

    # lower case comparison
    for row in data:
        if len(row) > attribute_sequence and row[attribute_sequence].lower() == real_name.lower():
            matched_data.append(row)
    
    return matched_data

def extract_before_dot_or_space(s):
    # 문자열에서 '.' 또는 ' '의 위치를 찾습니다.
    dot_index = s.find('.')
    space_index = s.find(' ')

    # '.'와 ' '의 위치 중 가장 먼저 나타나는 위치를 찾습니다.
    if dot_index == -1 and space_index == -1:
        return s  # '.'나 ' '가 없다면 전체 문자열 반환
    elif dot_index == -1:
        return s[:space_index]
    elif space_index == -1:
        return s[:dot_index]
    else:
        return s[:min(dot_index, space_index)]


def find_data_by_userId(spreadsheet_id, sheet_number, user_id, attribute_sequence):
    spreadsheet = get_spreadsheet(spreadsheet_id, config.kakao_json_key_path)
    # 전체 시트 개수를 파악
    sheet_list = spreadsheet.worksheets()
    total_sheets = len(sheet_list)
    
    # 유효하지 않은 시트 번호 예외 처리
    if sheet_number < 1 or sheet_number > total_sheets:
        raise ValueError(f"유효하지 않은 시트 번호입니다. 시트 번호는 1부터 {total_sheets} 사이여야 합니다.")
    
    # 시트 번호에 따라 해당 시트를 접근
    sheet = sheet_list[sheet_number - 1]

    # display_name으로 수정해야 하고
    # 인자로 문자열을 전달하면 인자의 '.' or ' ' 앞까지의 문자열을 추출하기
    display_name = get_display_name_by_user_id(user_id)
    real_name = extract_before_dot_or_space(display_name)

    # lower case comparison
    data = get_data_by_real_name(sheet, real_name, attribute_sequence)
    return data

# [연차 휴가의 잔여일수, 안식 휴가의 잔여 일수] 를 반환한다
# uer_id를 활용해서 해당 user의 휴가를 조회합니다
def get_remained_vacation_by_userId(spreadsheet_id, user_id):
    found_data = find_data_by_userId(spreadsheet_id, 3, user_id, 0)
    # 리스트로 구성 - 10(연차 휴가 잔여일수), 14(안식 휴가 잔여 일수)
    remained_vacation = []

    remained_vacation.append(found_data[0][9])
    remained_vacation.append(found_data[0][13])
    
    return remained_vacation

def get_today_vacation_data(spreadsheet_id, json_keyfile_path):
    # 스프레드시트 객체 얻기
    spreadsheet = get_spreadsheet(spreadsheet_id, json_keyfile_path)
    sheet = spreadsheet.worksheets()[0]
    
    # 모든 데이터 얻기
    # 각각의 데이터는 '2024. 08. 05 오전 8:31:24' 'Claire' '2024. 08. 05 오전 10:00:00' '2024. 08. 05 오후 12:00:00' '반반차(오전)' '개인휴가'
    all_data = sheet.get_all_values()
    today = datetime.today()

    # 연도, 월, 일 추출 후 형식 지정
    formatted_today = today.strftime("%Y. %m. %d")

    # 오늘의 날짜와 휴가 기간(시작 날짜 <= 오늘 <= 종료 날짜)이 겹치는 데이터 필터링
    today_vacation_data = []

    # 5번째 데이터부터 참조
    for data in all_data[4:]:
        start_date_str = data[2].strip("' ")
        end_date_str = data[3].strip("' ")

        # 날짜 부분만 추출하여 datetime 객체로 변환
        start_date_part = ' '.join(start_date_str.split()[:3])
        end_date_part = ' '.join(end_date_str.split()[:3])

        # strptime으로 datetime 객체로 변환
        start_date = datetime.strptime(start_date_part, '%Y. %m. %d')
        end_date = datetime.strptime(end_date_part, '%Y. %m. %d')

        # 오늘 날짜도 datetime 객체로 변환
        formatted_today_date = datetime.strptime(formatted_today, '%Y. %m. %d')

        # Debug - print
        # print(f"{start_date} || {formatted_today_date} || {end_date}")
        
        # 오늘 날짜가 휴가 기간에 포함되는지 확인
        if start_date <= formatted_today_date <= end_date:
            today_vacation_data.append(data)

    return today_vacation_data

"""
기능 : 휴가 데이터 정보 중 시작 연도를 확인 - 시작 연도의 파일이 존재하는지 확인 - 존재하지 않으면 해당 파일을 형성하는 함수
전달 인자: 신청한 휴가 데이터 [신청자 . . . . ]
반환 : 추가하는데 문제가 없다면 True, 예외가 있다면 예외 사항을 출력하고 False 반환하기 
"""


# 특정 디렉토리 내 파일명이 file_name에 일치하는 파일이 존재하는지 확인한다
# is_file_exists_in_directory(config.dummy_directory_id, file_name)
def is_file_exists_in_directory(directory_id, file_name):
    # Drive API 클라이언트 생성
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    drive_service = build('drive', 'v3', credentials=ServiceAccountCredentials.from_json_keyfile_name(config.kakao_json_key_path, scope))

    try:
        # Google Drive API를 사용하여 특정 디렉토리의 파일 목록을 가져옵니다.
        query = f"'{directory_id}' in parents and name = '{file_name}' and trashed = false"
        response = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)',supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        files = response.get('files', [])

        
        if files:
            return True
        else:
            return False
    
    except HttpError as error:
        print(f"An error occurred: {error}")
        return False

# 파일을 복사한다
def copy_gdrive_spreadsheet(template_file_id, new_filename, save_folder_id):
    """
    Google Drive의 특정 파일을 템플릿으로 사용하여 복제본을 만들고, 원하는 이름의 파일명으로 변경
    """

    # Google Drive API 클라이언트 생성
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials=ServiceAccountCredentials.from_json_keyfile_name(config.kakao_json_key_path, scope)
    drive_service = build('drive', 'v3', credentials=credentials)

    # 새 파일 메타데이터 설정
    file_metadata = {
        'name': new_filename,
        'parents': [save_folder_id]
    }

    # 파일 복사
    new_file = drive_service.files().copy(fileId=template_file_id, body=file_metadata,supportsAllDrives=True).execute()
# ---------------------------- #
# ---------------------------- #


# 남은 휴가 조회하기
def get_remained_vacation(message, say, user_states,  user_vacation_info, user_vacation_status):
    user_id = message['user']
    user_input = message['text']
    
    search_file_name = create_leave_string(get_current_year())
    spreadsheet_id = get_spreadsheet_id_in_folder(search_file_name, config.dummy_vacation_directory_id)
    
    if spreadsheet_id == None:
        msg = ("현재 연도를 기준으로 신청한 휴가 내역이 없습니다.\n")
        send_direct_message_to_user(user_id, msg)
        msg = (f"잔여 휴가 조회를 종료합니다.\n\n")
        send_direct_message_to_user(user_id, msg)
        return
    
    remained_vacation = get_remained_vacation_by_userId(spreadsheet_id, user_id)

    msg = (f"잔여 휴가 정보입니다\n"
        f"연차 휴가 잔여 일수 : {float(remained_vacation[0])}\n"
        f"안식 휴가 잔여 일수 : {float(remained_vacation[1])}\n"
        )
    send_direct_message_to_user(user_id, msg)
    
    msg = (f"잔여 휴가 조회를 종료합니다.\n\n")
    send_direct_message_to_user(user_id, msg)

    if user_id in user_states:
        del user_states[user_id]
    if user_id in user_vacation_info:
        del user_vacation_info[user_id]
    if user_id in user_vacation_status:
        del user_vacation_status[user_id]
    return

# 조회는 1번, 추가는 2번, 삭제는 3번을, 종료를 원하시면 \"종료\"를 입력하세요 (1, 2, 3, 종료)
def vacation_purpose_handler(message, say, user_states, cancel_vacation_status, user_vacation_info, user_vacation_status):
    user_id = message['user']
    user_input = message['text']
    # 1 / 2 / 3 / 종료가 들어가 있는 상황
    cleaned_user_input = re.sub(r'<@[^>]+>\s*', '', user_input)

    if cleaned_user_input == '종료':
        msg = (f"휴가 시스템을 종료합니다.\n\n")
        send_direct_message_to_user(user_id, msg)
        del user_states[user_id]
        return

    if is_valid_vacation_purpose(cleaned_user_input):
        if cleaned_user_input == '1': # 조회하기 - user_states 변경
            msg = (f"휴가 조회 기능을 실행합니다. 휴가 리스트를 출력합니다\n\n")
            send_direct_message_to_user(user_id, msg)
            try:
                search_file_name = create_leave_string(get_current_year())
                spreadsheet_id = get_spreadsheet_id_in_folder(search_file_name, config.dummy_vacation_directory_id)
                
                if spreadsheet_id == None:
                    msg = ("현재 연도를 기준으로 신청한 휴가 내역이 없습니다.\n")
                    send_direct_message_to_user(user_id, msg)
                    msg = (f"잔여 휴가 조회를 종료합니다.\n\n")
                    send_direct_message_to_user(user_id, msg)
                    if user_id in user_states:
                        del user_states[user_id]    
                    if user_id in cancel_vacation_status:
                        del cancel_vacation_status[user_id]
                    return
                
                found_data_list = find_data_by_userId(spreadsheet_id, 1, user_id, 1)
            except ValueError as e:
                msg = (f"Unvalid sheet_number: {e}")
                send_direct_message_to_user(user_id, msg)
    
            seq = 1
            for result in found_data_list:
                start_date = result[2]
                # 현재 날짜 이후 휴가만 조회 가능
                start_date = start_date.replace("오전", "AM")
                start_date = start_date.replace("오후", "PM")

                start_date = datetime.strptime(start_date, '%Y. %m. %d %p %I:%M:%S')
                now = datetime.now()

                if start_date <= now:
                    continue
                else:
                    msg = (f"{seq}. {format_vacation_info(result)}")
                    send_direct_message_to_user(user_id, msg)
                    seq += 1

                # msg = (f"{seq}. {format_vacation_info(result)}")
                # send_direct_message_to_user(user_id, msg)
                # seq += 1
            
            msg = (f"휴가 관련 프로그램을 종료합니다.\n\n")
            send_direct_message_to_user(user_id, msg)
            if user_id in user_states:
                del user_states[user_id]
            if user_id in cancel_vacation_status:
                del cancel_vacation_status[user_id]
            return 
        elif cleaned_user_input == '2': # 추가하기 - user_states 변경 / request_vacation_info, request_vacation_status
            if user_id in user_vacation_info:
                del user_vacation_info[user_id]
            if user_id in user_vacation_status:
                del user_vacation_status[user_id]

            user_states[user_id] = 'request_vacation'
            user_vacation_info[user_id] = []
            user_vacation_status[user_id] = 'checking_vacation_type'

            msg = (f"휴가 신청 진행중입니다. 휴가 종류를 선택하세요\n"
               "1. 연차\n"
               "2. 반차(오전)\n"
               "3. 반차(오후)\n"
               "4. 반반차(오전)\n"
               "5. 반반차(오후)\n")
            send_direct_message_to_user(user_id, msg)
        elif cleaned_user_input == '3': # 삭제하기 - user_states 변경 / cancel_vacation_status
            if user_id in cancel_vacation_status:
                del cancel_vacation_status[user_id]
            user_states[user_id] = 'cancel_vacation'
            msg = (f"휴가 삭제를 시작합니다.") 
            send_direct_message_to_user(user_id, msg)
            cancel_vacation_handler(message, say, user_states, cancel_vacation_status)
        elif cleaned_user_input == '4': # 남은 휴가 조회해줘
            msg = (f"잔여 휴가를 조회합니다. 잠시만 기다려주세요.\n")
            send_direct_message_to_user(user_id, msg)
            get_remained_vacation(message, say, user_states, user_vacation_info, user_vacation_status)
    else:
        msg = (f"휴가 프로그램 실행중입니다. 잘못된 입력입니다. 1,2,3,4 중 하나를 입력하세요")
        send_direct_message_to_user(user_id, msg)

#### 휴가 취소 ####
def cancel_vacation_handler(message, say, user_states, cancel_vacation_status):
    user_id = message['user']
    user_input = message['text']
    # mention을 제외한 내가 전달하고자 하는 문자열만 추출하는 함수 
    cleaned_user_input = re.sub(r'<@[^>]+>\s*', '', user_input)

    search_file_name = create_leave_string(get_current_year())
    spreadsheet_id = get_spreadsheet_id_in_folder(search_file_name, config.dummy_vacation_directory_id)

    if spreadsheet_id == None:
        msg = ("현재 연도를 기준으로 신청한 휴가 내역이 없습니다.\n")
        send_direct_message_to_user(user_id, msg)
        msg = (f"잔여 휴가 조회를 종료합니다.\n\n")
        send_direct_message_to_user(user_id, msg)
        if user_id in user_states:
            del user_states[user_id]
        if user_id in cancel_vacation_status:
            del cancel_vacation_status[user_id]
        return

    if cleaned_user_input == '종료':
        msg = (f"휴가 신청 프로세스를 종료합니다.\n\n")
        send_direct_message_to_user(user_id, msg)
        if user_id in user_states:
            del user_states[user_id]
        if user_id in cancel_vacation_status:
            del cancel_vacation_status[user_id]
        return 
    
    # 먼저 휴가를 리스트업 한다 
    # 시트 번호가 적절하지 않은 경우 예외 처리를 진행한다
    try:
        found_data_list = find_data_by_userId(spreadsheet_id, 1, user_id, 1)
    except ValueError as e:
        msg = (f"Unvalid sheet_number: {e}")
        send_direct_message_to_user(user_id, msg)
        return

    if user_id not in cancel_vacation_status:
        seq = 1 
        msg = (f"휴가 삭제를 진행중입니다. 아래의 휴가 신청 내역 중 취소할 휴가 번호를 입력하세요.\n"
            "종료를 원하시면 \'종료\'를 입력해주세요"
            ) # 문구 추가
        send_direct_message_to_user(user_id, msg)

        for result in found_data_list:
            start_date = result[2]
            # 현재 날짜 이후 휴가만 삭제 가능
            start_date = start_date.replace("오전", "AM")
            start_date = start_date.replace("오후", "PM")

            start_date = datetime.strptime(start_date, '%Y. %m. %d %p %I:%M:%S')
            now = datetime.now()

            if start_date <= now:
                continue
            else:
                msg = (f"{seq}. {format_vacation_info(result)}")
                send_direct_message_to_user(user_id, msg)
                seq += 1
                
        cancel_vacation_status[user_id] = 'waiting_cancel_sequence'
    
    elif cancel_vacation_status[user_id] == 'waiting_cancel_sequence':
        input_cancel_sequence(message, say, cancel_vacation_status, spreadsheet_id)

    
        if cancel_vacation_status[user_id] == 'waiting_deleting':
            # 1 / 1, 2 / 1,2 -> [] 리스트 형태로 변환해주고 - 변환하면서 예외처리 진행 - 선택한 휴가 맞는지 한번 더 출력
            ready_for_delete_list = cleaned_user_input
            cancel_sequence_list = to_cancel_sequence_list(ready_for_delete_list)
            msg = (f"휴가 삭제를 진행중입니다. 잠시만 기다려주세요.")
            send_direct_message_to_user(user_id, msg)


            valid_data_list = []

            for result in found_data_list:
                start_date = result[2]
                # 현재 날짜 이후 휴가만 삭제 가능
                start_date = start_date.replace("오전", "AM")
                start_date = start_date.replace("오후", "PM")

                start_date = datetime.strptime(start_date, '%Y. %m. %d %p %I:%M:%S')
                now = datetime.now()

                if start_date <= now:
                    continue
                else:
                    valid_data_list.append(result)

            found_data_list = valid_data_list

            for num in cancel_sequence_list:
                delete_data(spreadsheet_id, 1, found_data_list[num-1])
                delete_out_of_office_event(user_id, found_data_list[num-1][2], found_data_list[num-1][3])

            msg = (f"휴가 삭제를 진행중입니다. 휴가 삭제를 완료했습니다.")
            # send_direct_message_to_user(user_id, msg)
            # 구글 캘린더에 떠 있는 부재중 알림을 해제해야 함

            del cancel_vacation_status[user_id]
            del user_states[user_id]
            # user_states[user_id] = 'vacation_tracker'
            # msg = (f"<@{user_id}>님의 휴가 프로그램 실행중입니다. 조회는 1번, 추가는 2번, 삭제는 3번을, 종료를 원하시면 \"종료\"를 입력하세요\n")
            send_direct_message_to_user(user_id, msg)
            # 휴가 추가는 1, 취소는 2를 누르도록 진행한다

##### 휴가 종류를 입력받는다
def input_vacation_type(message, say, user_vacation_info, user_vacation_status):
    user_id = message['user']
    user_input = message['text']
    # mention을 제외한 내가 전달하고자 하는 문자열만 추출하는 함수 
    cleaned_user_input = re.sub(r'<@[^>]+>\s*', '', user_input)
    vacation_sequence = cleaned_user_input

    if is_valid_vacation_sequence(vacation_sequence):
        vacation_type = VACATION_SEQUENCE_TO_TYPE[int(vacation_sequence)]
        user_vacation_info[user_id].append(vacation_type) # 변환 모듈
        msg = (f"휴가 신청 진행중입니다. 신청한 휴가는 {vacation_type}입니다.\n\n")
        send_direct_message_to_user(user_id, msg)
        user_vacation_status[user_id] = "requesting_type"
    else:
        msg = (f"휴가 신청 진행중입니다. 잘못된 휴가 종류입니다. 1 - 5번 사이의 번호를 입력하세요\n\n")
        send_direct_message_to_user(user_id, msg)

#### 휴가 사유를 입력받는다
def input_vacation_reason(message, say, user_vacation_info, user_vacation_status):
    user_id = message['user']
    user_input = message['text']
    # mention을 제외한 내가 전달하고자 하는 문자열만 추출하는 함수 
    cleaned_user_input = re.sub(r'<@[^>]+>\s*', '', user_input)
    vacation_reason_sequence = cleaned_user_input

    # 예외 처리 관련
    if is_valid_vacation_reason_sequence(vacation_reason_sequence):
        vacation_reason_type = VACATION_SEQUENCE_TO_REASON[int(vacation_reason_sequence)]
        user_vacation_info[user_id].append(vacation_reason_type)
        msg = (f"휴가 신청 진행중입니다. {vacation_reason_type}를 신청했습니다.\n\n")
        send_direct_message_to_user(user_id, msg)
        if vacation_reason_type in ["경조휴가", "특별휴가", "출산휴가"]:
            user_vacation_status[user_id] = "waiting_vacation_specific_reason"
        else:
            user_vacation_info[user_id].append("") # 휴가 상세 자유를 공백으로 추가해둔다
            user_vacation_status[user_id] = "pre-confirmed"
    else:
        msg = (f"휴가 신청 진행중입니다. 잘못된 휴가 사유입니다. 1 - 8번 사이의 번호를 입력하세요\n\n")
        send_direct_message_to_user(user_id, msg)

#### 휴가 상세 사유 입력받기
def input_vacation_specific_reason(message, say, user_vacation_info, user_vacation_status):
    user_id = message['user']
    user_input = message['text']
    # mention을 제외한 내가 전달하고자 하는 문자열만 추출하는 함수 
    cleaned_user_input = re.sub(r'<@[^>]+>\s*', '', user_input)
    vacation_specific_reason = cleaned_user_input

    user_vacation_info[user_id].append(vacation_specific_reason)
    user_vacation_status[user_id] = "pre-confirmed"

#### 휴가 개인 이메일 입력받기
def input_vacation_email(message, say, user_vacation_info, user_vacation_status):
    
    user_id = message['user']
    user_input = message['text']
    # mention을 제외한 내가 전달하고자 하는 문자열만 추출하는 함수 
    email = process_and_extract_email(user_input)

    if is_valid_email(email):
        user_vacation_info[user_id].append(email) # 변환 모듈
        msg = (f"휴가 신청 진행중입니다. 휴가 신청 이메일은 {email} 입니다.\n\n")
        send_direct_message_to_user(user_id, msg)

        user_vacation_status[user_id] = "pre-confirmed"
    else:
        msg = (f"휴가 신청 진행중입니다. <{email}>올바르지 않은 이메일 형식입니다. 다시 입력하세요\n\n")
        send_direct_message_to_user(user_id, msg)

def is_confirmed(confirm_sequence):
    if(confirm_sequence == '0'):
        return True
    return False

def checking_final_confirm(message, say, user_vacation_status, user_vacation_info):
    user_id = message['user']
    user_input = message['text']
    # mention을 제외한 내가 전달하고자 하는 문자열만 추출하는 함수 
    cleaned_user_input = re.sub(r'<@[^>]+>\s*', '', user_input)
    confirm_sequence = cleaned_user_input

    # 유요한 입력인지 확인
    if is_valid_confirm_sequence(confirm_sequence):
        if is_confirmed(confirm_sequence):
            user_vacation_status[user_id] = 'confirmed'
        else:
            msg = (f"휴가 신청 진행중입니다. 휴가 신청 정보를 재입력합니다. 휴가 시작 날짜를 알려주세요. 입력 형식은 YYYY-MM-DD 입니다.\n\n")
            send_direct_message_to_user(user_id, msg)
            del user_vacation_status[user_id]
            del user_vacation_info[user_id]
    else:
        msg = (f"휴가 신청 진행중입니다. <{confirm_sequence}> 잘못된 입력입니다. 0 혹은 1을 입력하세요(0: 저장, 1: 수정)\n\n")
        send_direct_message_to_user(user_id, msg)
    # 0번이면 DB 반영하는 단계로 이어지도록 (상태 변경해야 한다) + info 정보 wrapping 해서 DB에 반영해야 한다
    # 1번이면 user_vacation_info, user_vacation_status 해당 인덱스 정보 삭제하기

#### 취소할 휴가 순서 입력받기
def input_cancel_sequence(message, say, cancel_vacation_status, spreadsheet_id):
    user_id = message['user']
    user_input = message['text']
    # mention을 제외한 내가 전달하고자 하는 문자열만 추출하는 함수 
    cleaned_user_input = re.sub(r'<@[^>]+>\s*', '', user_input)
    cancel_sequeunce = cleaned_user_input

    # 수가 아닌 경우를 예외처리 해야 한다
    cancel_sequence_list = to_cancel_sequence_list(cancel_sequeunce) # [1] / [1,2]

    try:
        found_data_list = find_data_by_userId(spreadsheet_id, 1, user_id, 1)
    except ValueError as e:
        msg = (f"Unvalid sheet_number: {e}")
        send_direct_message_to_user(user_id, msg)

    if is_valid_cancel_sequence(cancel_sequence_list, len(found_data_list)):
        cancel_vacation_status[user_id] = 'waiting_deleting'
    else:
        msg = (f"휴가 취소 프로세스를 진행중입니다.. 잘못된 번호입니다. 다시 입력해주세요.")
        send_direct_message_to_user(user_id, msg)

######### 휴가/연차 신청하기 #######
def request_vacation_handler(message, say, user_states, user_vacation_status, user_vacation_info):
    # update
    user_id = message['user']
    user_input = message['text']
    cleaned_user_input = re.sub(r'<@[^>]+>\s*', '', user_input)

    if cleaned_user_input == '종료':
        msg = (f"휴가 신청 프로세스를 종료합니다.\n\n")
        send_direct_message_to_user(user_id, msg)
        if user_id in user_states:
            del user_states[user_id]
        if user_id in user_vacation_info:
            del user_vacation_info[user_id]
        if user_id in user_vacation_status:
            del user_vacation_status[user_id]
        return
    
    if user_vacation_status[user_id] == 'checking_vacation_type':
        input_vacation_type(message, say, user_vacation_info, user_vacation_status)

    if user_id not in user_vacation_status and cleaned_user_input != "종료":
        user_vacation_info[user_id] = []
        msg = (f"휴가 신청 진행중입니다. 휴가 종류를 선택하세요\n"
               "1. 연차\n"
               "2. 반차(오전)\n"
               "3. 반차(오후)\n"
               "4. 반반차(오전)\n"
               "5. 반반차(오후)\n")
        send_direct_message_to_user(user_id, msg)
        user_vacation_status[user_id] = 'checking_vacation_type'
    
    if user_vacation_status[user_id] == 'requesting_type':
        if user_vacation_info[user_id][0] == '연차':  # 연차 선택 시
            msg = (f"휴가 신청 진행중입니다. *휴가 시작 날짜*를 입력해주세요. *공휴일이 포함되어 있는 경우 구분해서 신청하세요*\n"
                "날짜는 YYYY-MM-DD 형태로 입력하세요\n"
                "[예시] 2024-04-04\n")
        else:  # 연차 이외의 경우
            msg = (f"휴가 신청 진행중입니다. *휴가 시작 날짜와 시간을* 입력해주세요. *공휴일이 포함되어 있는 경우 구분해서 신청하세요*\n"
                "날짜는 YYYY-MM-DD 형태로, 시간은 HH:MM 형태로 입력하세요\n"
                "[예시] 2024-04-04 18:00\n")
        send_direct_message_to_user(user_id, msg)
        user_vacation_status[user_id] = 'requesting_start_date'
        return

    elif user_vacation_status[user_id] == 'requesting_start_date':
        start_date = cleaned_user_input.strip()
        if user_vacation_info[user_id][0] == '연차':  # 연차 선택 시
            if is_valid_date_only_day(start_date):
                user_vacation_info[user_id].append(start_date)
                msg = (f"휴가 신청 진행중입니다. *휴가 종료 날짜*를 입력해주세요. *공휴일이 포함되어 있는 경우 구분해서 신청하세요*\n"
                       "날짜는 YYYY-MM-DD 형태로 입력하세요\n"
                       "[예시] 2024-04-05\n")
                send_direct_message_to_user(user_id, msg)
                user_vacation_status[user_id] = 'requesting_end_date'
            else:
                msg = (":x: 잘못된 형식입니다. *휴가 시작 날짜를 YYYY-MM-DD 형태로* 다시 입력해주세요. *공휴일이 포함되어 있는 경우 구분해서 신청하세요*\n")
                send_direct_message_to_user(user_id, msg)
        else:  # 연차 이외의 경우
            if is_valid_date(start_date):
                user_vacation_info[user_id].append(start_date)
                msg = (f"휴가 신청 진행중입니다. *휴가 종료 날짜와 시간을* 입력해주세요. *공휴일이 포함되어 있는 경우 구분해서 신청하세요*\n"
                       "날짜는 YYYY-MM-DD 형태로, 시간은 HH:MM 형태로 입력하세요\n"
                       "[예시] 2024-04-05 18:00\n")
                send_direct_message_to_user(user_id, msg)
                user_vacation_status[user_id] = 'requesting_end_date'
            else:
                msg = (":x: 잘못된 형식입니다. *휴가 시작 날짜와 시간을 YYYY-MM-DD HH:MM 형태로* 다시 입력해주세요. *공휴일이 포함되어 있는 경우 구분해서 신청하세요*\n")
                send_direct_message_to_user(user_id, msg)

    # 휴가 사유 선택하기
    elif user_vacation_status[user_id] == 'checking_vacation_reason':
        input_vacation_reason(message, say, user_vacation_info, user_vacation_status)
    
    elif user_vacation_status[user_id] == 'requesting_end_date':
        end_date = cleaned_user_input.strip()
        if user_vacation_info[user_id][0] == '연차':  # 연차 선택 시
            if is_valid_date_only_day(end_date, comparison_date_str=user_vacation_info[user_id][1]):
                user_vacation_info[user_id][1] += " 09:00"  # 시작 시간 저장
                user_vacation_info[user_id].append(end_date + " 20:00")  # 종료 시간 저장
                msg = (f"휴가 신청 진행중입니다. 휴가 사유를 선택하세요\n"
                       "1. 개인휴가\n"
                       "2. 경조휴가\n"
                       "3. 특별휴가\n"
                       "4. 예비군, 민방위휴가\n"
                       "5. 보건휴가\n"
                       "6. 안식휴가\n"
                       "7. 출산휴가\n"
                       "8. 기타휴가\n")
                send_direct_message_to_user(user_id, msg)
                user_vacation_status[user_id] = 'checking_vacation_reason'
            else:
                msg = (":x: 잘못된 형식입니다. *휴가 종료 날짜를 YYYY-MM-DD 형태로* 다시 입력해주세요. *공휴일이 포함되어 있는 경우 구분해서 신청하세요*\n")
                send_direct_message_to_user(user_id, msg)
        else:  # 연차 이외의 경우
            if is_valid_date(end_date, comparison_date_str=user_vacation_info[user_id][1]):
                user_vacation_info[user_id].append(end_date)
                msg = (f"휴가 신청 진행중입니다. 휴가 사유를 선택하세요\n"
                       "1. 개인휴가\n"
                       "2. 경조휴가\n"
                       "3. 특별휴가\n"
                       "4. 예비군, 민방위휴가\n"
                       "5. 보건휴가\n"
                       "6. 안식휴가\n"
                       "7. 출산휴가\n"
                       "8. 기타휴가\n")
                send_direct_message_to_user(user_id, msg)
                user_vacation_status[user_id] = 'checking_vacation_reason'
            else:
                msg = (":x: 잘못된 형식입니다. *휴가 종료 날짜와 시간을 YYYY-MM-DD HH:MM 형태로* 다시 입력해주세요. *공휴일이 포함되어 있는 경우 구분해서 신청하세요*\n")
                send_direct_message_to_user(user_id, msg)

    elif user_vacation_status[user_id] == "checking_vacation_specific_reason":
        input_vacation_specific_reason(message, say, user_vacation_info, user_vacation_status)

    elif user_vacation_status[user_id] == "waiting_vacation_specific_reason":
        # 상세 사유 입력받기
        msg = (f"휴가 신청 진행중입니다. 선택하신 {user_vacation_info[user_id][-1]}의 휴가 상세 사유를 작성해주세요")
        send_direct_message_to_user(user_id, msg)
        user_vacation_status[user_id] = "checking_vacation_specific_reason"

    """
    이메일 입력 (Depreceated)
    if user_vacation_status[user_id] == "checking_vacation_email":
        input_vacation_email(message, say, user_vacation_info, user_vacation_status)
    if user_vacation_status[user_id] == "waiting_vacation_email":
        # email 입력받기
        msg = (f"<@{user_id}>님 휴가 신청 진행중입니다. <@{user_id}>의 개인 이메일을 작성해주세요.\n"
            "* 유의 * 이메일 아이디 내 느낌표(!)가 존재해서는 안 됩니다."
            )
        send_direct_message_to_user(user_id, msg)
        user_vacation_status[user_id] = "checking_vacation_email"
    """
    
    if user_vacation_status[user_id] == "waiting_final_confirm":
        checking_final_confirm(message, say, user_vacation_status, user_vacation_info)
    
    if user_id in user_vacation_info and user_vacation_status[user_id] == "pre-confirmed":
        msg = (f"휴가 신청 정보입니다.")
        send_direct_message_to_user(user_id, msg)
        for a, value in enumerate(user_vacation_info[user_id]):
            # 저장된 정보 출력 
            # 상세 이유가 공백인 경우 출력하지 않음 (해결))
            if value == '':
                continue
            msg = (f"{value}\n")
            send_direct_message_to_user(user_id, msg)

        msg = (f"휴가 신청을 완료하려면 0을, 수정을 원하면 1을 입력하세요.")
        send_direct_message_to_user(user_id, msg)
        user_vacation_status[user_id] = "waiting_final_confirm"

    if user_id in user_vacation_info and user_vacation_status[user_id] == "confirmed":
        # DB에 저장한다
        # user_vacation_info[user_id] 안에 모두 담겨져있는 상황 : 시작 - 종료 - 종류 - 사유 - 상세 사유 - 이메일 
        new_row_data = []
        current_time = datetime.now().strftime('%Y. %m. %d %p %I:%M:%S').replace('AM', '오전').replace('PM', '오후').lstrip("'")
        # spreadsheet에 반영되는 경우 객체 변환
        start_date_formatted = to_specific_date(user_vacation_info[user_id][1]).lstrip("'")
        end_date_formatted = to_specific_date(user_vacation_info[user_id][2]).lstrip("'")
        type = user_vacation_info[user_id][0]
        reason = user_vacation_info[user_id][3]
        specific_reason = user_vacation_info[user_id][4]
        email = get_display_name(user_id, 'users_info.json') + '@kakaoventures.co.kr'

        new_row_data.extend([
            current_time,
            get_real_name_by_user_id(user_id), # 저장시 ID로 저장 - uesrs_info에서 찾아서 대신 넣어야 한다 (있는 경우 없는 경우 생각하기)
            start_date_formatted,
            end_date_formatted,
            type,
            reason,
            specific_reason,
            email
        ])
    
        search_file_name = get_proper_file_name(new_row_data)
        if is_file_exists_in_directory(config.dummy_vacation_directory_id, search_file_name) is False:
            copy_gdrive_spreadsheet(config.dummy_vacation_template_id, search_file_name, config.dummy_vacation_directory_id)
            

        spreadsheet_id = get_spreadsheet_id_in_folder(search_file_name, config.dummy_vacation_directory_id)

        remained_vacation = get_remained_vacation_by_userId(spreadsheet_id, user_id)
        # type -> 수로 변경해야 함
        converted_value = convert_type_value(type)
        if reason == "개인휴가" and float(remained_vacation[0]) < converted_value:
            msg = (f":x: 개인휴가 신청이 불가합니다. *개인휴가의 잔여 일수를 확인하세요.*\n")
            send_direct_message_to_user(user_id, msg)
            msg = (f"휴가 신청을 종료합니다.")
            send_direct_message_to_user(user_id, msg)

            del user_states[user_id]
            del user_vacation_info[user_id]
            del user_vacation_status[user_id]
            return
        
        if reason == "안식휴가" and float(remained_vacation[1]) < converted_value:
            msg = (f":x: 안식휴가 신청이 불가합니다. *안식휴가의 잔여 일수를 확인하세요.*\n")
            send_direct_message_to_user(user_id, msg)
            msg = (f"휴가 신청을 종료합니다.")
            send_direct_message_to_user(user_id, msg)

            del user_states[user_id]
            del user_vacation_info[user_id]
            del user_vacation_status[user_id]
            return
        
        # DB에 반영한다 
        msg = (f"휴가 신청을 처리중입니다.")
        send_direct_message_to_user(user_id, msg)
        
        try:
            append_data(spreadsheet_id, new_row_data)
        except gspread.exceptions.APIError as e:
            msg = (f"APIError occurred: {e}")
            send_direct_message_to_user(user_id, msg)
        except gspread.exceptions.GSpreadException as e:
            msg = (f"GSpreadException occurred: {e}")
            send_direct_message_to_user(user_id, msg)
        except FileNotFoundError as e:
            msg = (f"File not found: {e}")
            send_direct_message_to_user(user_id, msg)
        except ValueError as e:
            msg = (f"Unvalid sheet_number: {e}")
            send_direct_message_to_user(user_id, msg)
        except Exception as e:
            msg = (f"An unexpected error occurred: {e}")
            send_direct_message_to_user(user_id, msg)

        # 부재중 slot 반영
        set_out_of_office_event(user_id, 
                                string_to_strptime(user_vacation_info[user_id][1]),
                                string_to_strptime(user_vacation_info[user_id][2]),
                                summary= type,
                                email= email,
                                )
        
        msg = (f":white_check_mark: 휴가 신청을 완료합니다. 휴가 / 연차 서비스를 종료합니다.\n")
        send_direct_message_to_user(user_id, msg)

        # 신청을 마무리하면 관련 모든 정보를 삭제한다
        del user_states[user_id]
        del user_vacation_info[user_id]
        del user_vacation_status[user_id]
        return