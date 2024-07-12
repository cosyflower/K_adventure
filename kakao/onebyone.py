import json
import config
from googleapiclient.discovery import build
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from datetime import datetime
import random

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from get_slack_user_info import update_authority
from googleVacationApi import is_file_exists_in_directory, copy_gdrive_spreadsheet
from formatting import process_user_input
from directMessageApi import send_direct_message_to_user

# Example usage
template_file_id = config.oneByone_id

# 전역 변수로 used_pairs 선언
used_pairs = set()

# users_info에 등록된 사람들의 이름을 가지고 리스트를 반환하는 함수
def get_name_list_from_json(file_path='users_info.json'):
    # 권한 정보 업데이트 하기, 추가된 경우 
    # update_authority()
    # JSON 파일을 열고 데이터를 읽음
    with open(file_path, 'r', encoding='utf-8') as file:
        users_data = json.load(file)

    # bot 이 반영되어 있지 않은 애들만 append()
    names = []
    for id in users_data:
        name = users_data[id].get('name')
        if users_data[id].get('authority') <= 3 and 'bot' not in name:
            names.append(users_data[id].get('name'))
    return names

# 이름 문자열을 전달하면 id 값을 반환하는 함수
def get_slack_id_from_json(name_str, file_path='users_info.json'):
    # 권한 정보 업데이트 하기
    # update_authority()

    # JSON 파일을 열고 데이터를 읽음
    with open(file_path, 'r', encoding='utf-8') as file:
        users_data = json.load(file)

    # bot 이 반영되어 있지 않은 애들만
    for id in users_data:
        name = users_data[id].get('name')
        if users_data[id].get('authority') <= 3 and name_str == name:
            return users_data[id].get('id')
    return None

# 특정 이름을 가진 스프레드 시트 파일을 먼저 만든다. 이 때 특정 스프레드 시트 파일을 복사하되 이름은 '현재 시간의 연도' + '1on1'로 구성한다
# 현재 시간을 확인하고 '연도' +'1on1' 의 이름을 가진 파일이 존재하지 않으면 새롭게 파일을 형성한다 

# 함수를 호출할 때마다 새로운 sheet를 구성하는 함수이다 
# 새로운 sheet는 다음의 규칙을 따라야 한다
# 1. 기존에 존재하는 시트 중 가장 마지막 시트의 이름을 확인한다 - 1주차 (n주차로 구성)
# 2. 해당 시트의 이름은 n주차로 구성되야 하며 기존의 마지막 시트의 다음주차로 구성된다 -  만약 마지막 시트가 '1주차'인 경우 새롭게 형성되는 시트의 이름은 '2주차'
# 3. 해당 시트의 첫번째 행은 '이름', '슬랙ID', '금주의 매칭 대상'으로 작성해야 한다
def get_spreadsheet_service():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(config.kakao_json_key_path, scopes=scope)
    sheets_service = build('sheets', 'v4', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)
    return sheets_service, drive_service

def copy_spreadsheet(drive_service, template_file_id, new_title):
    file_metadata = {
        'name': new_title,
        'mimeType': 'application/vnd.google-apps.spreadsheet'
    }
    copied_file = drive_service.files().copy(fileId=template_file_id, body=file_metadata, supportsAllDrives=True).execute()
    return copied_file.get('id')

def find_spreadsheet(drive_service, title):
    query = f"name='{title}' and mimeType='application/vnd.google-apps.spreadsheet'"
    result = drive_service.files().list(q=query).execute()
    files = result.get('files', [])
    return files[0].get('id') if files else None

def find_spreadsheet_in_shared_drive(drive_service, title, shared_drive_id):
    query = f"name='{title}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
    result = drive_service.files().list(q=query, driveId=shared_drive_id, corpora='drive', includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
    files = result.get('files', [])
    return files[0].get('id') if files else None

def add_new_sheet(sheets_service, spreadsheet_id):
    # Get the list of sheets in the spreadsheet
    spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = spreadsheet.get('sheets', [])
    
    # Find the name of the last sheet and determine the new sheet's name
    last_sheet_title = sheets[-1]['properties']['title']
    if '주차' in last_sheet_title:
        last_week_number = int(last_sheet_title.replace('주차', ''))
        new_sheet_title = f"{last_week_number + 1}주차"
    else:
        new_sheet_title = "1주차"
    
    # Add a new sheet to the spreadsheet
    requests = [{
        'addSheet': {
            'properties': {
                'title': new_sheet_title
            }
        }
    }]
    body = {
        'requests': requests
    }
    sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    
    # Update the first row of the new sheet
    values = [
        ["이름", "슬랙ID", "금주의 매칭 대상"]
    ]
    body = {
        'values': values
    }
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{new_sheet_title}!A1:C1",
        valueInputOption="RAW",
        body=body
    ).execute()
    
def get_or_create_1on1_spreadsheet(template_file_id = config.oneByone_id):
    try:
        sheets_service, drive_service = get_spreadsheet_service()
        
        # Determine the title for the new spreadsheet
        current_year = datetime.now().year
        new_title = f"{current_year}1on1"
        
        # Check if the spreadsheet already exists
        spreadsheet_id = find_spreadsheet_in_shared_drive(drive_service, new_title, config.shared_drive_id)
        
        if not spreadsheet_id:
            # Copy the template spreadsheet to create a new one
            spreadsheet_id = copy_spreadsheet(drive_service, template_file_id, new_title)
            print(f'Spreadsheet "{new_title}" created with ID: {spreadsheet_id}')
        else:
            print(f'Spreadsheet "{new_title}" found with ID: {spreadsheet_id}')
        
        # Add a new sheet to the spreadsheet
        add_new_sheet(sheets_service, spreadsheet_id)
        return spreadsheet_id
    
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def match_people(people):
    if not people:
        return []
    
    random.shuffle(people)
    
    matches = []
    already_matched = set()
    
    # 이미 매칭된 사람들을 기록
    for pair in used_pairs:
        already_matched.update(pair)
    
    n = len(people)
    unmatched = set(people)
    
    for i in range(n):
        person = people[i]
        if person in already_matched:
            continue  # 이미 매칭된 사람은 건너뜀
        for j in range(i + 1, n):
            if people[j] in already_matched:
                continue  # 이미 매칭된 사람은 건너뜀
            pair = tuple(sorted((person, people[j])))
            if pair not in used_pairs:
                used_pairs.add(pair)
                matches.append(pair)
                unmatched.discard(person)
                unmatched.discard(people[j])
                already_matched.add(person)
                already_matched.add(people[j])
                break
        else:
            # 매칭되지 않은 사람은 자신과 매칭
            if n % 2 != 0 and (person, person) not in used_pairs:
                used_pairs.add((person, person))
                matches.append((person, person))
                unmatched.discard(person)
                already_matched.add(person)
    
    # 매칭되지 않은 사람들이 있는지 확인하고 중복 허용하여 매칭
    if unmatched:
        unmatched_list = list(unmatched)
        for i in range(0, len(unmatched_list), 2):
            if i + 1 < len(unmatched_list):
                pair = tuple(sorted((unmatched_list[i], unmatched_list[i + 1])))
                used_pairs.add(pair)
                matches.append(pair)
            else:
                # 남은 사람이 홀수인 경우 자기 자신과 매칭
                pair = (unmatched_list[i], unmatched_list[i])
                used_pairs.add(pair)
                matches.append(pair)
    
    # 역방향 매칭 추가하기
    reverse_matches = [(y, x) for x, y in matches if x != y]
    matches.extend(reverse_matches)
    
    return matches

# Google Sheets에 데이터를 작성하는 함수
def update_spreadsheet_on_oneByone(match_data):
    # 파일 형성 및 시트 추가 + 초기 세팅 완료
    spreadsheet_id = get_or_create_1on1_spreadsheet()
    sheets_service, _ = get_spreadsheet_service()
    
    sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = sheet_metadata.get('sheets', [])
    last_sheet = sheets[-1]
    last_sheet_id = last_sheet['properties']['sheetId']
    last_sheet_name = last_sheet['properties']['title']
    
    # 데이터 작성
    data = []
    for match in match_data:
        person1, person2 = match
        slack_id1 = get_slack_id_from_json(person1)
        data.append([person1, slack_id1, person2])
    
    # 데이터 추가
    body = {
        'values': data
    }
    range_name = f"{last_sheet_name}!A1"  # 시트 이름과 범위를 지정
    
    sheets_service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()

    #삭제용
    print("1 on1 1 매칭 완료!!")


def find_oneByone_handler(message, say, user_states):
    user_id = message['user']
    user_input = message['text']


    # 1on1 파일 접속
    # 데이터 개수 확인 (가장 마지막 시트의 데이터 개수 확인)
    # 인원 상 변동이 있는지 확인
    # 인원 상 변동이 있는 경우


    ### 변동이 없는 경우 


    processed_input = process_user_input(user_input)

    partner = find_oneByone(user_id)

    print(f"partner : {partner}")
    msg = (f"<@{user_id}> 매칭 대상은 : {partner}입니다. 일대일매칭 기능을 종료합니다\n")
    send_direct_message_to_user(user_id, msg)
    del user_states[user_id]
    



def find_oneByone(user_id):
    # Determine the title for the new spreadsheet
    current_year = datetime.now().year
    new_title = f"{current_year}1on1"
    
    sheets_service, drive_service = get_spreadsheet_service()
    # Check if the spreadsheet already exists (무조건 존재해야 함)
    spreadsheet_id = find_spreadsheet_in_shared_drive(drive_service, new_title, config.shared_drive_id)

    sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = sheet_metadata.get('sheets', [])
    last_sheet = sheets[-1]
    last_sheet_id = last_sheet['properties']['sheetId']
    last_sheet_name = last_sheet['properties']['title']

    # Retrieve data from the last sheet
    range_name = f"{last_sheet_name}!A:C"  # Adjust the range as per your data layout
    result = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    
    # Remove the first row (header)
    if values:
        values = values[1:]
    
    for row in values:      
        if len(row) >= 2 and row[1] == user_id:
            if len(row) >= 3:
                return row[2]
            else:
                print("check code!!!")