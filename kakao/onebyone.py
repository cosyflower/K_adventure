import json
import config
from googleapiclient.discovery import build
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from datetime import datetime
import random
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from get_slack_user_info import update_authority
from googleVacationApi import is_file_exists_in_directory, copy_gdrive_spreadsheet
from formatting import process_user_input
from directMessageApi import send_direct_message_to_user


# Example usage
template_file_id = config.oneByone_id


# users_info에 등록된 사람들의 이름을 가지고 리스트를 반환하는 함수
def get_name_list_from_json(file_path='users_info.json'):
    # update_authority()
    with open(file_path, 'r', encoding='utf-8') as file:
        users_data = json.load(file)

    # bot admin이 반영되어 있지 않은 애들만 append()
    # 권한이 2이하인 사람들만 반영한다
    names = []
    for id in users_data:
        name = users_data[id].get('name')
        if users_data[id].get('authority') <= 2 and 'bot' not in name and 'admin' not in name:
            names.append(users_data[id].get('name'))
    return names

# 이름 문자열을 전달하면 id 값을 반환하는 함수
def get_slack_id_from_json(name_str, file_path='users_info.json'):
    # 권한 정보 업데이트 하기
    # update_authority()

    # JSON 파일을 열고 데이터를 읽음
    with open(file_path, 'r', encoding='utf-8') as file:
        users_data = json.load(file)

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
    
    # 현재 날짜를 MM-DD 형식으로 구함
    current_date = datetime.now().strftime('%m-%d')

    # Find the name of the last sheet and determine the new sheet's name
    last_sheet_title = sheets[-1]['properties']['title']
    if '주차' in last_sheet_title:
        # '주차' 앞의 숫자만 추출
        match = re.search(r'(\d+)', last_sheet_title)

        if match:
            last_week_number = int(match.group(1))
            new_sheet_title = f"{last_week_number + 1}주차({current_date})"
        else:
            new_sheet_title = f"1주차({current_date})"
    
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
            # print(f'Spreadsheet "{new_title}" created with ID: {spreadsheet_id}')
        # else:
        #     print(f'get_or_create_1on1() called - Spreadsheet "{new_title}" found with ID: {spreadsheet_id}')
        
        # Add a new sheet to the spreadsheet
        add_new_sheet(sheets_service, spreadsheet_id)
        return spreadsheet_id
    
    except HttpError as error:
        # print(f'An error occurred: {error}')
        return None

def match_people(people):
    if not people:
        return []

    already_matched = set()
    sheets_service, drive_service = get_spreadsheet_service()
    
    # Determine the title for the new spreadsheet
    current_year = datetime.now().year
    new_title = f"{current_year}1on1"
    
    # used_pairs()에 지난 매칭 기록을 저장합니다
    spreadsheet_id = find_spreadsheet_in_shared_drive(drive_service, new_title, config.shared_drive_id)
    
    if not spreadsheet_id:
        spreadsheet_id = copy_spreadsheet(drive_service, template_file_id, new_title)
        # print(f'Spreadsheet "{new_title}" created with ID: {spreadsheet_id}')
    # else:
    #     print(f'match people() called and Spreadsheet "{new_title}" found with ID: {spreadsheet_id}')

    sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = sheet_metadata.get('sheets', [])

    for sheet in sheets:
        sheet_name = sheet.get("properties", {}).get("title")
        range_name = f'{sheet_name}!A:Z'  # 필요한 범위 지정, 여기서는 A:Z까지
        result = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])

        # 첫 번째 행을 제외한 나머지 데이터 가져오기
        if values:
            data_without_header = values[1:]  # 첫 번째 행 제거
            for row in data_without_header:
                if len(row) >= 3:  # 행에 최소한 세 개의 열이 있는지 확인
                    already_matched.add((row[0], row[2]))  # 첫 번째 열과 세 번째 열 데이터 추가
    
    matches = []
    unmatched = set(people)
    
    while len(unmatched) > 1:
        person = unmatched.pop()
        potential_matches = list(unmatched - {p for p in unmatched if (person, p) in already_matched or (p, person) in already_matched})
        
        if not potential_matches:
            unmatched.add(person)
            break
        
        match = random.choice(potential_matches)
        unmatched.remove(match)
        matches.append((person, match))
        already_matched.add((person, match))
    
    if unmatched:
        remaining_person = unmatched.pop()
        if len(people) % 2 == 1:
            matches.append((remaining_person, remaining_person))
        else:
            possible_matches = list(set(people) - {remaining_person})
            for match in possible_matches:
                if (remaining_person, match) not in already_matched and (match, remaining_person) not in already_matched:
                    matches.append((remaining_person, match))
                    already_matched.add((remaining_person, match))
                    break
            else:
                # 중복을 허용하여 매칭
                random_match = random.choice(possible_matches)
                matches.append((remaining_person, random_match))
                already_matched.add((remaining_person, random_match))

    # 역방향 매칭 추가하기
    reverse_matches = [(y, x) for x, y in matches if x != y and (y, x) not in matches]
    matches.extend(reverse_matches)
    
    return matches

def is_valid_week_oneByone():
    sheet_service, drive_service = get_spreadsheet_service()
    
    current_year = datetime.now().year
    new_title = f"{current_year}1on1"

    # Check if the spreadsheet already exists
    spreadsheet_id = find_spreadsheet_in_shared_drive(drive_service, new_title, config.shared_drive_id)
    
    if not spreadsheet_id:
        # Copy the template spreadsheet to create a new one
        spreadsheet_id = copy_spreadsheet(drive_service, template_file_id, new_title)

    # spreadsheet 내 마지막 시트명을 조회합니다
    # 마지막 시트명의 문자열 내에 '(' ')' 로 묶인 내부 문자열을 조회합니다. 내부 문자열은 날짜 형태로 구성되어 있습니다(MM-DD)
    # 조회한 날짜와 오늘의 날짜를 비교합니다
    # 오늘의 날짜와 조회한 날짜 간의 일수 차이가 14일 이상이면 참, 아니면 거짓을 반환합니다
    # # Get metadata of the spreadsheet
    sheet_metadata = sheet_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = sheet_metadata.get('sheets', [])
    last_sheet = sheets[-1]
    last_sheet_name = last_sheet['properties']['title']

    # Extract date in MM-DD format within parentheses
    match = re.search(r'\((\d{2}-\d{2})\)', last_sheet_name)
    
    if match:
        last_date_str = match.group(1)
        # Add the current year to the extracted date string
        last_date = datetime.strptime(f"{current_year}-{last_date_str}", '%Y-%m-%d')
        
        # Get today's date
        today = datetime.now()
        
        # Calculate the difference in days
        days_difference = (today - last_date).days
        
        # Check if the difference is 14 days or more
        if days_difference >= 14:
            return True
        else:
            return False


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

    return spreadsheet_id

def find_oneByone_handler(message, say, user_states):
    user_id = message['user']
    user_input = message['text']

    partner = find_oneByone(user_id)

    # print(f"partner : {partner}")
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

# update_spreadsheet_on_oneByone(match_people(get_name_list_from_json()))