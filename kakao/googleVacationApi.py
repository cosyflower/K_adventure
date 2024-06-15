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