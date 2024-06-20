import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from datetime import datetime, timedelta
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

from translator import parse_date

def get_spreadsheet(spreadsheet_id, json_keyfile_path):
    # 구글 스프레드시트 API 인증 및 클라이언트 생성
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
    client = gspread.authorize(creds)
    
    # 스프레드시트 객체 반환
    return client.open_by_key(spreadsheet_id)

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

def append_data(spreadsheet_id, sheet_number, row_data):
    add_row_to_sheet(get_spreadsheet(spreadsheet_id, config.kakao_json_key_path), sheet_number, row_data)
    print("Data appended")

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
            print(f"Row {idx + 1} has been deleted.")

def delete_data(spreadsheet_id, sheet_number, row_data):
    delete_row_to_sheet(get_spreadsheet(spreadsheet_id, config.kakao_json_key_path), sheet_number, row_data)

def get_real_name_by_user_id(user_id, json_path='users_info.json'):
    with open(json_path, 'r', encoding='utf-8') as file:
        users_info = json.load(file)
    
    for key, user_data in users_info.items():
        if user_data['id'] == user_id:
            return user_data['real_name']
    return None

def get_data_by_real_name(sheet, real_name, attribute_sequence):
    data = sheet.get_all_values()
    matched_data = []

    if real_name is None:
        return matched_data

    for row in data:
        if len(row) > attribute_sequence and row[attribute_sequence] == real_name:
            matched_data.append(row)
    
    return matched_data

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

    real_name = get_real_name_by_user_id(user_id)
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
    all_data = sheet.get_all_values()
    # 오늘 날짜 구하기 (YYYY-MM-DD 형식)
    today = datetime.today()
    today_str = today.strftime('%Y. %-m. %-d')
    print(f"today is {today_str}\n")

    # 오늘의 날짜와 휴가 시작 날짜가 같은 데이터 필터링
    today_vacation_data = []
    
    for data in all_data:
        start_date = data[2].strip("' ")
        extracted_date = start_date.split()[0:3]
        extracted_date = ' '.join(extracted_date).strip()

        if extracted_date == today_str:
            print("추가!")
            today_vacation_data.append(data)

    return today_vacation_data