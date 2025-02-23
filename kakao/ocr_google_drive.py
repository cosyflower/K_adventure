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

# Global variable
# If constant, should be upper-case(상수면 대문자)
JSON_KEY_FILE_PATH = config.kakao_json_key_path
SEARCH_FILE_NAME_PREFIX = ['_', '(별도)', '(연결)']

def get_authorized_service(json_path=JSON_KEY_FILE_PATH):
    # 서비스 계정 인증 정보 로드
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
    
    # Google Drive API 클라이언트 생성
    service = build('drive', 'v3', credentials=credentials)
    return service

# get children directories from parent_folder_id
def list_drive_folders(service, parent_folder_id):
    query = f"'{parent_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)', supportsAllDrives=True,
                                   includeItemsFromAllDrives=True).execute()
    items = results.get('files', [])
    return items

# 현재 시간을 기준으로 연도와 분기를 계산하는 함수
def get_current_year_and_quarter():
    now = datetime.now()
    year = now.year % 100  # 마지막 두 자리 연도를 사용 (예: 2024년 -> 24)
    
    # 분기 계산: 1-3월(1분기), 4-6월(2분기), 7-9월(3분기), 10-12월(4분기)
    quarter = (now.month - 1) // 3 + 1
    return f"{year}년_{quarter}분기"

# 주어진 폴더 이름과 일치하는 폴더 ID를 반환하는 함수
def get_folder_id_by_name(service, parent_folder_id, folder_name):
    # 현재 연도와 분기를 가져옴
    current_year_and_quarter = get_current_year_and_quarter()

    # 드라이브에서 폴더 목록 가져오기
    folders = list_drive_folders(service, parent_folder_id)
    
    for folder in folders:
        # 폴더 이름이 "24년_4분기_{folder_name}" 형태로 구성되었는지 확인
        expected_folder_name = f"{current_year_and_quarter}_{folder_name}"
        
        if expected_folder_name == folder['name']:
            return folder['id']
    
    return None


def list_files_in_folder(service, folder_id):
    """
    주어진 폴더 ID 내의 파일 목록을 조회하는 함수
    :param service: Google Drive API 서비스 객체
    :param folder_id: 파일을 조회할 폴더의 ID
    :return: 폴더 내 파일 목록 (리스트 형식)
    """
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)', 
                                   supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    items = results.get('files', [])
    
    if not items:
        print(f"No files found in folder: {folder_id}")
        return []

    return items

def get_spreadsheet_id_in_folder(file_name, folder_id):
    """
    Google 공유 Drive에서 특정 스프레드시트 파일의 ID를 가져옵니다.

    :param file_name: 찾고자 하는 스프레드시트 파일의 이름
    :folder_id: parent's id
    :return: 파일 ID 또는 None
    """

    # authentication first!
    service = get_authorized_service()
    # 파일 검색 쿼리
    query = f"'{folder_id}' in parents and name = '{file_name}' and mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false"
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

# extract string until prefix 
def extract_prefix_from_filename(filename, prefix_list=SEARCH_FILE_NAME_PREFIX):
    # 접두어 위치 찾기
    split_positions = [filename.find(prefix) for prefix in prefix_list if prefix in filename]

    if split_positions:
        # 가장 먼저 등장하는 접두어 위치 찾기
        min_position = min(split_positions)
        return filename[:min_position]

    # 접두어가 없으면 원래 문자열 반환
    return filename

def convert_excel_to_sheets(service, excel_file_id, sheet_name):
    # Google 스프레드시트로 변환
    file_metadata = {
        'name': sheet_name,
        'mimeType': 'application/vnd.google-apps.spreadsheet'
    }
    
    # 파일 ID를 사용하여 변환 작업 수행
    file = service.files().copy(fileId=excel_file_id, body=file_metadata).execute()
    print(f"Google 스프레드시트로 변환된 파일 ID: {file.get('id')}")
    return file.get('id')

# convert google spreadsheet to json
def sheet_to_json(service, spreadsheet_id, range_name):
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    return json.dumps(values)

def move_spreadsheet_to_folder(service, spreadsheet_id, folder_id):
    # 파일을 지정된 폴더로 이동하는 메서드
    # 부모 폴더 리스트 업데이트를 통해 파일을 이동
    file = service.files().get(fileId=spreadsheet_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents'))

    # 파일을 새로운 폴더로 이동
    updated_file = service.files().update(
        fileId=spreadsheet_id,
        addParents=folder_id,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()

    print(f"파일이 {folder_id} 폴더로 이동되었습니다.")
    return updated_file

def get_all_company_names():
    scope1 = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds1 = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEY_FILE_PATH, scope1)
    client1 = gspread.authorize(creds1)
    spreadsheet_id1 = config.db_1_id  # 스프레드시트 주소에 있는 아이디 가져오기
    spreadsheet1 = client1.open_by_key(spreadsheet_id1)
    worksheet1 = spreadsheet1.sheet1
    data1 = worksheet1.get_all_values()
    df1 = pd.DataFrame(data1)
    df1.columns = df1.iloc[0]
    df1 = df1[1:]
    all_company_names = df1['약식 회사명'].values.tolist()
    all_company_names_full = df1['회사명'].values.tolist()
    return all_company_names, all_company_names_full