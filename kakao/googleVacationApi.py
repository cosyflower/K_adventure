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

def add_row_to_sheet(spreadsheet, row_data): ## spreadsheet에 row_data를 append 한다
    sheet = spreadsheet.sheet1
    sheet.append_row(row_data)

def append_data(spreadsheet_id, row_data):
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.kakao_json_key_path, scope)
    client = gspread.authorize(creds)
    # spreadsheet_id = config.dummy_vacation_db_id  # 스프레드시트 주소에 있는 아이디 가져오기
    spreadsheet = client.open_by_key(spreadsheet_id)

    add_row_to_sheet(spreadsheet, row_data)

def delete_data(spreadsheet_id, row_data):
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.kakao_json_key_path, scope)
    client = gspread.authorize(creds)
    # spreadsheet_id = config.dummy_vacation_db_id  # 스프레드시트 주소에 있는 아이디 가져오기
    spreadsheet = client.open_by_key(spreadsheet_id)

def get_real_name_by_user_id(user_id, json_path='users_info.json'):
    with open(json_path, 'r', encoding='utf-8') as file:
        users_info = json.load(file)
    
    for key, user_data in users_info.items():
        if user_data['id'] == user_id:
            return user_data['real_name']
    return None

def get_data_by_real_name(sheet, real_name=None):
    data = sheet.get_all_values()
    matched_data = []

    if real_name is None:
        return matched_data

    for row in data:
        if len(row) > 1 and row[1] == real_name:
            matched_data.append(row)
    
    return matched_data

def find_data_by_userId(spreadsheet_id, user_id):
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.kakao_json_key_path, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)
    sheet = spreadsheet.sheet1

    real_name = get_real_name_by_user_id(user_id)
    if real_name is None:
        return get_data_by_real_name(sheet)

    data = get_data_by_real_name(sheet, real_name)
    return data