import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from gspread_formatting import *

import config
import googleapi
import pytz
import locale
import time

from googleVacationApi import is_file_exists_in_directory

# Google Drive API 설정
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = config.kakao_json_key_path
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# 폴더 ID 및 오늘 날짜 파일명
folder_id = config.fileABCD_parent_folder_id

# 파일 ID 조회 함수
def get_file_id_in_folder(folder_id, file_name):
    try:
        # Google Drive API 쿼리 설정
        query = f"'{folder_id}' in parents and name = '{file_name}' and trashed = false"
        response = drive_service.files().list(
            q=query, spaces='drive', fields='files(id, name)',
            supportsAllDrives=True, includeItemsFromAllDrives=True # Essential!!!!!
        ).execute()
        files = response.get('files', [])

        # 파일이 존재하면 첫 번째 파일의 ID 반환, 없으면 None 반환
        if files:
            file_id = files[0].get('id')
            print(f"File ID for '{file_name}': {file_id}")
            return file_id
        else:
            print(f"No file named '{file_name}' found in the folder.")
            return None
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

# 폴더 내 파일이 존재하는지 확인하는 함수
def is_file_exists_in_directory(folder_id, file_name):
    try:
        query = f"'{folder_id}' in parents and name = '{file_name}' and trashed = false"
        response = drive_service.files().list(
            q=query, spaces='drive', fields='files(id, name)',
            supportsAllDrives=True, includeItemsFromAllDrives=True
        ).execute()
        files = response.get('files', [])
        return len(files) > 0
    except HttpError as error:
        print(f"An error occurred while checking file existence: {error}")
        return False

# 스프레드시트 생성 함수
def create_spreadsheet(folder_id, file_name):
    template_id = config.investment_table_template_id

    try:
        file_metadata = {
            'name': file_name,
            'mimeType': 'application/vnd.google-apps.spreadsheet',
            'parents': [folder_id]
        }
        file = drive_service.files().create(body=file_metadata, fields='id', supportsAllDrives=True).execute()
        print(f"Created spreadsheet with ID: {file.get('id')}")
    except HttpError as error:
        print(f"An error occurred while creating the spreadsheet: {error}")

    # try:
    #     # 파일 복사 설정
    #     file_metadata = {
    #         'name': file_name,
    #         'parents': [folder_id]
    #     }
        
    #     # 템플릿 스프레드시트 복사
    #     file = drive_service.files().copy(
    #         fileId=template_id,
    #         body=file_metadata,
    #         supportsAllDrives=True
    #     ).execute()
        
    #     print(f"Created spreadsheet with ID: {file.get('id')}")
    #     return file.get('id')
        
    # except HttpError as error:
    #     print(f"An error occurred while creating the spreadsheet: {error}")
    #     return None

# 폴더 접근 권한 확인
def check_folder_access(folder_id):
    try:
        drive_service.files().get(fileId=folder_id, supportsAllDrives=True).execute()
        print("Access to folder is confirmed.")
        return True
    except HttpError as error:
        print(f"Cannot access folder: {error}")
        return False

# inv_id가 선택된 상황입니다
# ex) 라포랩스 (kv : KV_190 inv : KV_190_5)

# dataframe으로 모두 조회하는 방식임
def load_data(db_1, db_4, db_7):
    db_1_info = db_1
    db_4_info = db_4
    db_7_info = db_7

# file_id에 해당하는 스프레드시트에 DataFrame 반영 함수
def update_basic_with_dataframes(file_id, basic_df):
    # NaN 값을 빈 문자열로 대체
    basic_df = basic_df.fillna('')  

    # '펀드명' 또는 '약정금액'이 포함된 행 제거
    basic_df = basic_df[~basic_df.iloc[:, 0].str.contains("펀드명", na=False)]
    # 카카오 벤처스 포함된 행 제거하기
    basic_df = basic_df[~basic_df.iloc[:, 0].str.contains("카카오벤처스", na=False)]

    client = gspread.authorize(credentials)
    # 스프레드시트 열기
    spreadsheet = client.open_by_key(file_id)
    worksheet = spreadsheet.sheet1  # 첫 번째 시트
    
    # 스프레드시트 초기화
    worksheet.clear()

    # 해당 표의 제목을 설정한다
    worksheet.update('A1', [["1. 운용 중인 투자조합 기본정보"]])

    
    # 첫 번째 행에 열 제목 설정
    headers = [
        '조합명', '결성금액', '투자재원', '결성일', '투자기간 만료일', 
        '존속기간 만료일', '대표펀드매니저', '핵심운용인력', '투자기간'
    ]
    worksheet.append_row(headers, table_range="A3")  # 세 번째 행에 열 제목 추가
    
    # DataFrame의 키 값을 제외하고 데이터만 리스트로 변환하여 추가
    data = basic_df.reset_index(drop=True).values.tolist()  # 인덱스를 초기화하여 키 제거
    worksheet.append_rows(data, table_range="A4")  # 데이터를 네 번째 행부터 추가


def update_invest_with_dataframes(file_id, invest_df):
    client = gspread.authorize(credentials)
    # 스프레드시트 열기
    spreadsheet = client.open_by_key(file_id)
    worksheet = spreadsheet.sheet1  # 첫 번째 시트
    
    # 마지막 데이터가 위치한 행 다음에 데이터 추가 위치 계산
    last_row = len(worksheet.get_all_values()) + 2  # 마지막 행 다음 + 한 줄 띄우기

    # 표 제목 추가
    worksheet.update_cell(last_row, 1, '2. 투자대상 기업정보')
    invest_df = invest_df.fillna('')
    
    # 투자 대상 기업정보 추가
    invest_data = [
        ['(1) 투자대상 기업명', invest_df['회사명'].iloc[0]],
        ['(2) 발굴자', invest_df['발굴자1'].iloc[0], invest_df['발굴자2'].iloc[0], invest_df['발굴자3'].iloc[0]],
        ['(3) 후속/후행 투자 여부', invest_df['INV ID 상태'].iloc[0]],
        ['(4) 투자예정금액', invest_df['투자금액(원화)'].iloc[0]],
        ['(5) 투자예정시기', invest_df['투자 납입일'].iloc[0]]
    ]

    # 데이터 추가
    for i, row_data in enumerate(invest_data):
        title = row_data[0]
        worksheet.update_cell(last_row + i + 1, 1, title)  # 제목을 A열에 추가
        
        # 데이터 값을 B열부터 오른쪽으로 추가
        for j, value in enumerate(row_data[1:]):
            worksheet.update_cell(last_row + i + 1, 2 + j, value)  # 데이터를 B열부터 추가

def update_invest_date(file_id, basic_df, invest_df):
    # 구글 스프레드시트 인증
    credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/spreadsheets'])
    client = gspread.authorize(credentials)
    
    # 날짜 형식 변환
    basic_df['투자기간 만료일'] = pd.to_datetime(basic_df['투자기간 만료일'], format='%Y-%m-%d', errors='coerce')
    invest_df['투자 납입일'] = pd.to_datetime(invest_df['투자 납입일'], format='%Y-%m-%d', errors='coerce')

    # 4번째 행부터 마지막 행까지만 투자기간을 업데이트 (DataFrame 인덱스는 0부터 시작하므로 3부터 슬라이싱)
    for index, row in basic_df.iloc[2:].iterrows():
        # 투자기간 만료일이 투자예정시기보다 크거나 같으면 'O', 아니면 'X'
        if row['투자기간 만료일'] >= invest_df['투자 납입일'].iloc[0]:
            basic_df.at[index, '투자기간'] = 'O'
        else:
            basic_df.at[index, '투자기간'] = 'X'

    # 스프레드시트 열기
    spreadsheet = client.open_by_key(file_id)
    worksheet = spreadsheet.sheet1  # 첫 번째 시트

    # 업데이트할 열 추출 (투자기간 열만)
    투자기간_values = basic_df['투자기간'].values.tolist()
    
    # Google Sheets의 투자기간 열에 값 업데이트
    cell_range = f"I2:I{len(투자기간_values) + 1}"  # 투자기간 열의 위치에 맞춰서 설정
    worksheet.update(cell_range, [[value] for value in 투자기간_values])

    print('update invest_date completed')

def fetch_sheet_as_dataframe(file_id, sheet_name):
    # Google Sheets 파일에 인증하고 열기
    gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
    spreadsheet = gc.open_by_key(file_id)
    sheet = spreadsheet.worksheet(sheet_name)  # 특정 워크시트 가져오기
    
    # Google Sheets 데이터를 가져와서 데이터프레임으로 변환
    data = sheet.get_all_values()  # 모든 데이터를 리스트로 가져오기
    headers = data.pop(0)  # 첫 번째 행을 헤더로 설정
    df = pd.DataFrame(data, columns=headers)  # 데이터프레임 생성
    
    return df

def update_invest_src(file_id, basic_df):
    invest_src_id = config.investment_resources_overview_id
    copy_id = '1eK9rdEHm0rovV8H37c7r57e4eEXqUjQPe1LUMlA1QVI'

    # Google Sheets API 인증 설정
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
    client = gspread.authorize(creds)

    # 원본 시트 열기
    source_sheet = client.open_by_key(invest_src_id).get_worksheet(1) 

    # 원본 시트에서 전체 데이터 가져오기
    source_data = source_sheet.get_all_values()

    # 복사할 대상 시트 열기
    destination_sheet = client.open_by_key(copy_id).sheet1

    # 대상 시트의 범위에 데이터를 업데이트 (전체 데이터 반영)
    destination_sheet.clear()  # 먼저 대상 시트의 내용을 지웁니다.
    destination_sheet.update('A1', source_data)  # A1 셀부터 데이터를 복사

def get_basic_info_from_spreadsheet(file_id, sheet_name="Sheet1", target_keyword="조합명"):
    # Google API 자격 증명 설정 (서비스 계정 파일 필요)
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    
    # 스프레드시트 데이터를 읽어옵니다.
    result = sheet.values().get(spreadsheetId=file_id, range=sheet_name).execute()
    values = result.get('values', [])
    
    # 스프레드시트에서 조합명이 포함된 위치 찾기
    start_index = None
    for i, row in enumerate(values):
        if target_keyword in row:
            start_index = i
            break
    
    # 조합명 이후 데이터를 빈칸 전까지 추출
    if start_index is not None:
        data_rows = []
        for row in values[start_index + 1:]:
            if any(cell.strip() for cell in row):  # 빈 행이 아닌 경우만 추가
                data_rows.append(row)
            else:
                break  # 빈 행을 만나면 중단
    
        # DataFrame으로 변환
        df = pd.DataFrame(data_rows)
        return df
    else:
        print(f"{target_keyword}를 찾을 수 없습니다.")
        return pd.DataFrame()  # 빈 데이터프레임 반환

def update_invest_distribution(file_id, fund_name, inv_id):
    # Google Sheets 파일에 인증하고 열기
    gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
    spreadsheet = gc.open_by_key(file_id)
    sheet = spreadsheet.sheet1  # 기본 워크시트 선택

    # db7_id 스프레드시트 열기
    db7_id = config.db_7_id
    client = gspread.authorize(credentials)
    db7_sheet = client.open_by_key(db7_id).sheet1  # 첫 번째 시트 사용 (필요 시 시트 이름으로 변경)

    # B열에서 fund_name과 같은 데이터 검색 및 해당 데이터의 D열 반환
    fund_data_in_b = db7_sheet.col_values(2)  # B열의 모든 데이터 가져오기

    # fund_name이 위치한 행 찾기
    row_num = None
    for idx, value in enumerate(fund_data_in_b, start=1):  # 행 번호가 1부터 시작
        if value == fund_name:
            row_num = idx
            break

    # D열의 데이터 반환
    if row_num:
        fund_commitment = db7_sheet.cell(row_num, 5).value  # D열의 데이터 가져오기 (4는 D열에 해당)
        print(f"펀드 약정 금액 : {fund_commitment}") 
    else:
        print("fund_name을 찾을 수 없습니다.")

    # fund_commitment =>>>> 펀드 약정 금액

    # 마지막으로 작성된 데이터 위치 확인
    data = sheet.get_all_values()
    last_row = len(data) + 2  # 마지막 데이터 이후 한 줄을 건너뜀

    # '3. 투자재원 배분 결정 : 투자재원 배분기준 지침 참조'
    sheet.update(f'A{last_row}', [['3. 투자재원 배분 결정 : 투자재원 배분기준 지침 참조']])
    last_row = last_row + 2

    # 총 3개의 표를 구성합니다
    # 1번째 표 구성 (제목)
    sheet.update(f'A{last_row}', [['(1) 기투자한 조합이 있을 경우 우선 배정 가능']])

    # '(3) 후속/후행 투자 여부' 셀을 찾고 해당 셀의 우측 값을 조회
    try:
        cell = sheet.find('(3) 후속/후행 투자 여부')
        right_cell_value = sheet.cell(cell.row, cell.col + 1).value  # 우측 셀 값 가져오기

        # 조회한 값을 last_row에 업데이트
        sheet.update(f'A{last_row + 1}', [[f'{right_cell_value}']])

    except gspread.exceptions.CellNotFound:
        print("셀 '(3) 후속/후행 투자 여부'를 찾을 수 없습니다.")
    last_row += 3 

    # 2번째 표 구성 (제목 및 헤더)
    sheet.update(f'A{last_row}', [['(2) 투자의무비율 & 주목적/특수목적비율 충족 필요 조합 우선 배정 여부']])
    last_row += 1
    headers_2 = [["조합명", "투자기간 이내", "잔여재원여부", "투자의무비율 충족 필요", "주∙특수목적 충족 필요", "주∙특수목적 해당여부", "판단"]]
    sheet.update(f'A{last_row}:G{last_row}', headers_2)

    last_row += 1
    basic_info_df = get_basic_info_from_spreadsheet(file_id)
    second_filterd_df = basic_info_df[basic_info_df[8] == 'O']

    for _, row in second_filterd_df.iterrows():
        # 호에서 inv_id 해당되는 데이터 파악하고 인정투자 금액의 합 구하기
        # config.investment_present_table_id 스프레드 시트 중 '호'로 끝나는 시트만 조회
        # inv_id를 키로 데이터를 탐색 and W열 값이 '여' 인 경우 AE값 AG값을 곱한다. AF가 기준 통화
        # 합과 fund_commitment 비교한다
        # 조건에 따라 O 혹은 X로 설정한다




        # 0번째 열과 9번째 열 값 추출
        data_to_add = [[row[0], row[8], '', '']]
        sheet.update(f'A{last_row}:D{last_row}', data_to_add)  # 열 A와 B에 각각 추가
        last_row += 1  # 다음 행으로 이동

    last_row += 1

    # 3번째 표 구성 (제목 및 헤더)
    sheet.update(f'A{last_row}', [['(3) 핵심운용인력 우선 배정 가능']])
    last_row += 1
    headers_3 = [["조합명", "투자기간 이내", "잔여재원여부", "핵심운용인력 우선 배정"]]
    sheet.update(f'A{last_row}:D{last_row}', headers_3)

    last_row += 1
    basic_info_df = get_basic_info_from_spreadsheet(file_id)
    second_filterd_df = basic_info_df[basic_info_df[8] == 'O']

    # '(2) 발굴자' 셀을 찾고 우측 셀 값을 조회
    try:
        finder_cell = sheet.find('(2) 발굴자')
        finder_right_value = sheet.cell(finder_cell.row, finder_cell.col + 1).value  # 우측 셀 값 가져오기
        print(f'finder_right_value : {finder_right_value}')


        # 각 행에 대해 조건에 따라 값을 업데이트
        for _, row in second_filterd_df.iterrows():
            # 대표펀드 매니저와 핵심운용인력에 존재 여부 확인
            fund_manager = row[6]  # 실제 컬럼명으로 변경 필요
            core_staff = row[7]  # 실제 컬럼명으로 변경 필요
            
            # 각각의 값을 쉼표로 구분하여 분리
            fund_manager_list = fund_manager.split(',') if ',' in fund_manager else [fund_manager]
            core_staff_list = core_staff.split(',') if ',' in core_staff else [core_staff]

            # 두 리스트를 합쳐 전체 인원을 full_staff에 저장
            full_staff = fund_manager_list + core_staff_list
            full_staff = [name.strip() for name in full_staff]  # 각 이름의 앞뒤 공백 제거

            allocation_status = 'O' if finder_right_value in full_staff else 'X'

            # 결과를 업데이트
            sheet.update(f'A{last_row}', [[row[0], row[8],'' ,allocation_status]])  # A열, B열, D열에 데이터 추가
            last_row += 1

    except gspread.exceptions.CellNotFound:
        print("셀 '(2) 발굴자'를 찾을 수 없습니다.")
    
    last_row += 2 #  Next pretention

def update_invest_summary(file_id, fund_name):
    # Google Sheets 파일에 인증하고 열기
    gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
    spreadsheet = gc.open_by_key(file_id)
    sheet = spreadsheet.sheet1  # 기본 워크시트 선택

    # 마지막으로 작성된 데이터 위치 확인
    data = sheet.get_all_values()
    last_row = len(data) + 2  # 마지막 데이터 이후 한 줄을 건너뜀
    
    # title
    sheet.update(f'A{last_row}', [['4. 투자 배분금액 및 근거']])
    last_row += 1
    sheet.update(f'A{last_row}', [['(1) 투자 배분금액']])
    last_row += 1

    headers_1 = [["투자조합명", "금번 투자금액 이내"]]
    sheet.update(f'A{last_row}:B{last_row}', headers_1)
    last_row += 1

    # sheet에서 '(4) 투자예정금액' 셀을 탐색한다
    # 해당 셀의 우측값을 조회한다
    # money에 결과를 저장한다
    # '(4) 투자예정금액' 셀을 탐색하고 우측 값을 조회하여 money에 저장
    try:
        target_cell = sheet.find('(4) 투자예정금액')
        money = sheet.cell(target_cell.row, target_cell.col + 1).value  # 우측 셀 값 가져오기

        # 확인용 출력
        print(f'fund_name: {fund_name}')
        print(f"투자예정금액 우측 값: {money}")
        
    except gspread.exceptions.CellNotFound:
        print("셀 '(4) 투자예정금액'을 찾을 수 없습니다.")
        money = None  # 셀을 찾지 못했을 때 None으로 설정

    sheet.update(f'A{last_row}:B{last_row}', [[fund_name, money]])

    last_row = last_row + 2
    sheet.update(f'A{last_row}', [['(2) 배분 사유']])
    last_row = last_row + 1
    sheet.update(f'A{last_row}', [['조합 담당자가 사유 쓰기']])
    last_row = last_row + 1
    sheet.update(f'A{last_row}', [['EX) 투자 가능한 조합 중 주목적에 해당하며 재원이 있는 조합에 배정']])
    last_row = last_row + 1
    sheet.update(f'A{last_row}', [['투자 가능한 조합 중 기투자한 조합에 우선 배정']])
    last_row = last_row + 1
    sheet.update(f'A{last_row}', [['투자 가능한 조합 중 주목적, 특수목적 비율 충족이 필요한 조합에 배정']])
    last_row = last_row + 1
    sheet.update(f'A{last_row}', [['투자 가능한 조합 중 핵심운용인력이 발굴자로 있는 조합에 우선 배정']])




def get_all_data_from_spreadsheet(spreadsheeet_id):
    # 스프레드시트 ID 및 데이터 가져오기
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(spreadsheeet_id)
    worksheet = spreadsheet.sheet1  # 첫 번째 시트

    # 전체 데이터를 가져와 DataFrame으로 변환
    data = worksheet.get_all_values()
    df = pd.DataFrame(data)

    return df

def create_basic_info_table():
    db_7_spreadsheet_info = get_all_data_from_spreadsheet(config.db_7_id)

    NAME = 1   
    STATUS = 15 
    COMMITED_AMOUNT_INFO = 4
    ESTABLISHMENT_DATE = 10
    INVEST_EXPIRATION_DATE = 14
    DURATION_EXPIRATION_DATE = 11
    LEAD_FUND_MANAGER = 16 
    KEY_OPERATING_PERSONNEL = 17

    # db_7_spreadsheet_info 정보 중 '상태' 가 청산이 아닌 데이터만 조회합니다
    filtered_data = db_7_spreadsheet_info[db_7_spreadsheet_info[STATUS] != '청산']

    # 투자재원 채우기
    # filtered_data의 조합명과 비교, 일치하면 투자가능재원 값을 넣고 아니면 '-'로 메꾸기
    compared_file_id = config.investment_resources_overview_id
    client = gspread.authorize(credentials)
    # 스프레드시트 불러오기
    spreadsheet = client.open_by_key(compared_file_id)

    # '실시간'이라는 시트 가져오기
    sheet = spreadsheet.worksheet('실시간')

    # 3번째 행과 23번째 행 데이터 가져오기
    row_3 = sheet.row_values(3)
    row_23 = sheet.row_values(23)

    # 3번째 행의 데이터에서 공백을 제외한 요소를 리스트로 저장
    row_3_filtered = [item for item in row_3 if item.strip() != '']
    # 23번째 행에서 '투자집행가능'으로 시작하지 않는 요소와 공백을 제외한 요소를 리스트로 저장
    row_23_filtered = [item for item in row_23 if item.strip() != '' and not item.startswith('투자집행가능')]

    # row_3_filtered와 row_23_filtered 각각의 요소를 쌍으로 묶기
    paired_data = list(zip(row_3_filtered, row_23_filtered))
    print(paired_data)

    result_list = []
    for name in row_3_filtered:
        matched = False
        for pair in paired_data:
            if name == pair[0]:
                result_list.append(pair[1])
                matched = True
                break
        if not matched:
            result_list.append('-')

    # 출력
    print("결과 리스트:", result_list)

    table_data = pd.DataFrame({
        '조합명': filtered_data[NAME],  # 예: 조합명을 0번 인덱스로 설정
        '결성금액': filtered_data[COMMITED_AMOUNT_INFO],
        '투자재원': None,  # 필요에 따라 수정
        '결성일': filtered_data[ESTABLISHMENT_DATE],
        '투자기간 만료일': filtered_data[INVEST_EXPIRATION_DATE],
        '존속기간 만료일': filtered_data[DURATION_EXPIRATION_DATE],
        '대표펀드 매니저': filtered_data[LEAD_FUND_MANAGER],
        '핵심운용인력': filtered_data[KEY_OPERATING_PERSONNEL],
        '투자기간': None  # 필요에 따라 수정
    })

    return table_data

def create_invest_Target_Company_information(db_1_df, db_4_df):
    # db_1_df에서 회사명 조회
    company_names = db_1_df['회사명'].iloc[0] if '회사명' in db_1_df.columns else None
    print("회사명:", company_names)
    
    # db_4_df에서 발굴자1, 발굴자2, 발굴자3 조회
    discoverer1 = db_4_df['발굴자1'].iloc[0] if '발굴자1' in db_4_df.columns else None
    discoverer2 = db_4_df['발굴자2'].iloc[0] if '발굴자2' in db_4_df.columns else None
    discoverer3 = db_4_df['발굴자3'].iloc[0] if '발굴자3' in db_4_df.columns else None
    print("발굴자1:", discoverer1)
    print("발굴자2:", discoverer2)
    print("발굴자3:", discoverer3)
    
    # db_4_df에서 'INV ID' 조회, 마지막 문자가 '1'이면 'O', 아니면 'X'
    if 'INV ID' in db_4_df.columns:
        INV_STATUS= db_4_df['INV ID'].apply(lambda x: 'O' if str(x).endswith('1') else 'X').iloc[0]
    print("INV ID 상태:", INV_STATUS)
    
    # db_4_df에서 투자금액(원화) 조회
    investment_amount = db_4_df['투자금액(원화)'].iloc[0] if '투자금액(원화)' in db_4_df.columns else None
    print("투자금액(원화):", investment_amount)
    
    # db_4_df에서 투자 납입일 조회
    investment_date = db_4_df['투자 납입일'].iloc[0] if '투자 납입일' in db_4_df.columns else None
    print("투자 납입일:", investment_date)

    result_df = pd.DataFrame({
        '회사명': [company_names],
        '발굴자1': [discoverer1],
        '발굴자2': [discoverer2],
        '발굴자3': [discoverer3],
        'INV ID 상태': [INV_STATUS],
        '투자금액(원화)': [investment_amount],
        '투자 납입일': [investment_date]
    })

    return result_df

def create_investmentTable(db_1_df, db_4_df, db_7_df, kv_id, inv_id):
    fund_name = db_7_df['펀드명'].iloc[0]

    basic_df = create_basic_info_table()
    invest_df = create_invest_Target_Company_information(db_1_df, db_4_df)

    company_name = invest_df['회사명'].iloc[0]
    file_name = '투자재원배분표_' + company_name

    if check_folder_access(folder_id):
        if not is_file_exists_in_directory(folder_id, file_name):
            create_spreadsheet(folder_id, file_name)
            time.sleep(5)
        else:
            print(f"The file '{file_name}' already exists in the folder.")
    else:
        print("Please verify folder access permissions.")
    
    file_id = get_file_id_in_folder(folder_id, file_name)

    update_basic_with_dataframes(file_id, basic_df)
    update_invest_with_dataframes(file_id, invest_df)

    print('디버그 출력창------------')
    print(f'basic_df column : {basic_df.columns}')
    print(f'invest_df column : {invest_df.columns}')
    print('디버그 출력창------------')

    update_invest_date(file_id, basic_df, invest_df)
    update_invest_src(file_id, basic_df) # 테스트 시트 확인하기 
    update_invest_distribution(file_id, fund_name, inv_id)
    update_invest_summary(file_id, fund_name)