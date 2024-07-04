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

def get_last_company_name():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.kakao_json_key_path, scope)
    client = gspread.authorize(creds)
    spreadsheet_id = config.db_1_id  # 스프레드시트 주소에 있는 아이디 가져오기
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.sheet1
    data = worksheet.get_all_values()
    df = pd.DataFrame(data)
    df.columns = df.iloc[0]
    df = df[1:]
    last_company_name = df['회사명'].iloc[-1]
    id = df['KV ID'].iloc[-1]
    return id,last_company_name

def get_company_id_from_company_name(company_name):
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.kakao_json_key_path, scope)
    client = gspread.authorize(creds)
    spreadsheet_id = config.db_1_id  # 스프레드시트 주소에 있는 아이디 가져오기
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.sheet1
    data = worksheet.get_all_values()
    df = pd.DataFrame(data)
    df.columns = df.iloc[0] 
    df = df[1:] 
    # matching_row = df[df['회사명'] == company_name]

    matching_full_name = df[df['회사명'] == company_name]
    matching_short_name = df[df['약식 회사명'] == company_name]
    combined_df = pd.concat([matching_full_name, matching_short_name])
    matching_row = combined_df.drop_duplicates()

    if not matching_row.empty:
        id = matching_row['KV ID'].iloc[0]
    else:
        id = 0
    return id

def get_inv_id_from_company_id(company_id):
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.kakao_json_key_path, scope)
    client = gspread.authorize(creds)
    spreadsheet_id = config.db_4_id  # 스프레드시트 주소에 있는 아이디 가져오기
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.sheet1
    data = worksheet.get_all_values()
    df = pd.DataFrame(data)
    df.columns = df.iloc[0] 
    df = df[1:] 
    matching_rows = df[df['KV ID'] == company_id]
    if not matching_rows.empty:
        ids = matching_rows['INV ID'].tolist()
    else:
        ids = []
    return ids, matching_rows

def get_db1_info_from_kv_id(kv_id):
    scope1 = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds1 = ServiceAccountCredentials.from_json_keyfile_name(config.kakao_json_key_path, scope1)
    client1 = gspread.authorize(creds1)
    spreadsheet_id1 = config.db_1_id  # 스프레드시트 주소에 있는 아이디 가져오기
    spreadsheet1 = client1.open_by_key(spreadsheet_id1)
    worksheet1 = spreadsheet1.sheet1
    data1 = worksheet1.get_all_values()
    df1 = pd.DataFrame(data1)
    df1.columns = df1.iloc[0]
    df1 = df1[1:]
    row = df1[df1['KV ID'] == kv_id]
    return row

def get_db3_info_from_kv_id(kv_id):
    scope3 = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds3 = ServiceAccountCredentials.from_json_keyfile_name(config.kakao_json_key_path, scope3)
    client3 = gspread.authorize(creds3)
    spreadsheet_id3 = config.db_3_id
    spreadsheet3 = client3.open_by_key(spreadsheet_id3)
    worksheet3 = spreadsheet3.worksheet('2023')
    data3 = worksheet3.get_all_values()
    df3 = pd.DataFrame(data3)
    df3.columns = df3.iloc[0]
    df3 = df3[1:]
    df3['기준시점'] = pd.to_datetime(df3['기준시점'], format='%Y.%m')  # 날짜 형식으로 변환
    matching_rows = df3[df3['KV ID'] == kv_id]
    latest_row = matching_rows[matching_rows['기준시점'] == matching_rows['기준시점'].max()]
    latest_row = latest_row.iloc[-1]
    return latest_row

def get_db4_info_from_inv_id(inv_id):
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.kakao_json_key_path, scope)
    client = gspread.authorize(creds)
    spreadsheet_id = config.db_4_id # 스프레드시트 주소에 있는 아이디 가져오기
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.sheet1
    data = worksheet.get_all_values()
    df = pd.DataFrame(data)
    df.columns = df.iloc[0]
    df = df[1:]
    row = df[df['INV ID'] == inv_id]
    return row

def get_db7_info_from_fund_num(fund_num):
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.kakao_json_key_path, scope)
    client = gspread.authorize(creds)
    spreadsheet_id = config.db_7_id # 스프레드시트 주소에 있는 아이디 가져오기
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.sheet1
    data = worksheet.get_all_values()
    df = pd.DataFrame(data)
    df.columns = df.iloc[0]
    df = df[1:]
    fund = "FUND_" + fund_num[:-1]
    row = df[df['펀드 ID'] == fund]
    return row

def get_time():
    korea_timezone = pytz.timezone('Asia/Seoul')
    korea_time = datetime.now(korea_timezone)
    return korea_time.strftime("%Y-%m-%d %H:%M:%S")

def get_day_of_week(input_date_str):    
    input_date = datetime.strptime(input_date_str, "%Y-%m-%d")
    two_weeks_before = input_date - timedelta(weeks=2)
    if two_weeks_before.weekday() != 0:
        two_weeks_before = two_weeks_before - timedelta(days=two_weeks_before.weekday())
    return two_weeks_before.strftime("%Y.%m.%d")

def change_count_form(num):
    num = str(num)
    num = num.replace(',', '')
    num = float(num)
    return f"{num:,}"

def change_money_form(num):
    num = str(num)
    num = num.replace(',', '')
    num = float(num)
    return f"{num:,}원"

def change_money_form2(num):
    num = str(num)
    locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
    num = num.replace(',', '')
    num = float(num)
    million_won = num / 1000000
    rounded_million = round(million_won)
    formatted_amount = locale.format_string("%d", rounded_million, grouping=True)
    return f"약 {formatted_amount}백만원"

def change_money_form3(amount):
    amount = str(amount)
    amount = amount.replace(',', '')
    amount = float(amount)
    locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
    million_won = amount / 1000000
    formatted_amount = locale.format_string("%.3f", million_won, grouping=True)
    return f"약 {formatted_amount}백만원"
# 운용지시서
def make_docx_fileA(db_1,db_4,db_7, current_time):
    SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = config.kakao_json_key_path
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('docs', 'v1', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)
    document_id = config.fileA_id
    
    COMPANY_NAME = db_1['회사명'].iloc[0]

    new_document = drive_service.files().copy(fileId=document_id, body={'name': COMPANY_NAME+'_운용지시서'},supportsAllDrives=True).execute()     
    new_document_id = new_document.get('id')

    FUND_NAME = db_7['펀드명'].iloc[0]
    
    BUSINESS_NUMBER = db_1['사업자등록번호'].iloc[0]
    SHARE_RATIO = db_4['지분율(투자시점)'].iloc[0]

    LISTING_OR_NOT = db_4['지분율(투자시점)'].iloc[0] 
    if LISTING_OR_NOT == "여":
        LISTING_OR_NOT = "상장"
    else:
        LISTING_OR_NOT = "비상장"
    
    RECOGNIZED_INVESTMENT_STATUS = db_4['인정투자여부'].iloc[0] 
    if RECOGNIZED_INVESTMENT_STATUS == "여":
        RECOGNIZED_INVESTMENT_STATUS = "O"
    else:
        RECOGNIZED_INVESTMENT_STATUS = "X"
    
    OVERSEAS_COMPANY1 = db_1['해외기업여부'].iloc[0] 
    if OVERSEAS_COMPANY1 == "여":
        OVERSEAS_COMPANY1 = "O"
    else:
        OVERSEAS_COMPANY1 = ""

    OVERSEAS_COMPANY2 = db_1['해외기업여부'].iloc[0] 
    if OVERSEAS_COMPANY2 == "여":
        OVERSEAS_COMPANY2 = ""
    else:
        OVERSEAS_COMPANY2 = "O"

    INVESTMENT_AMOUNT = change_money_form(db_4['투자금액(원화)'].iloc[0]) 
    INVESTMENT_COUNT = change_count_form(db_4['인수 주식수'].iloc[0])
    INVESTMENT_PRICE = change_money_form(db_4['투자단가(원화)'].iloc[0]) 
    INVESTMENT_CATEGORY = db_4['투자유형(투자시)'].iloc[0]
    BANK_NAME = db_7['수탁은행'].iloc[0]
    BANK_NUMBER = db_7['수탁 MMDA 계좌번호'].iloc[0]

    EXPECT_INVESTMENT_DATE = db_4['투자 납입일'].iloc[0]
    year, month, day = EXPECT_INVESTMENT_DATE.split('-')
    year = year[2:]
    EXPECT_INVESTMENT_DATE = f"{year}.{month}.{day}"

    requests = [
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^FUND_NAME%$^",
                    'matchCase': 'true'
                },
                'replaceText': FUND_NAME,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^COMPANY_NAME%$^",
                    'matchCase': 'true'
                },
                'replaceText':COMPANY_NAME,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^BUSINESS_NUMBER%$^",
                    'matchCase': 'true'
                },
                'replaceText':BUSINESS_NUMBER,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^SHARE_RATIO%$^",
                    'matchCase': 'true'
                },
                'replaceText':SHARE_RATIO,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^LISTING_OR_NOT%$^",
                    'matchCase': 'true'
                },
                'replaceText':LISTING_OR_NOT,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^RECOGNIZED_INVESTMENT_STATUS%$^",
                    'matchCase': 'true'
                },
                'replaceText':RECOGNIZED_INVESTMENT_STATUS,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^OVERSEAS_COMPANY1%$^",
                    'matchCase': 'true'
                },
                'replaceText':OVERSEAS_COMPANY1,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^OVERSEAS_COMPANY2%$^",
                    'matchCase': 'true'
                },
                'replaceText':OVERSEAS_COMPANY2,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_AMOUNT%$^",
                    'matchCase': 'true'
                },
                'replaceText':INVESTMENT_AMOUNT,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_COUNT%$^",
                    'matchCase': 'true'
                },
                'replaceText':INVESTMENT_COUNT,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_PRICE%$^",
                    'matchCase': 'true'
                },
                'replaceText':INVESTMENT_PRICE,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_CATEGORY%$^",
                    'matchCase': 'true'
                },
                'replaceText':INVESTMENT_CATEGORY,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^BANK_NAME%$^",
                    'matchCase': 'true'
                },
                'replaceText':BANK_NAME,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^BANK_NUMBER%$^",
                    'matchCase': 'true'
                },
                'replaceText':BANK_NUMBER,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^EXPECT_INVESTMENT_DATE%$^",
                    'matchCase': 'true'
                },
                'replaceText':EXPECT_INVESTMENT_DATE,
            }
        }
    ]

    result = service.documents().batchUpdate(documentId=new_document_id, body={'requests': requests}).execute()
    parent_folder_id = config.fileABCD_parent_folder_id

    folder_name = current_time + "_" + COMPANY_NAME
    query = f"'{parent_folder_id}' in parents and name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name)",supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    items = results.get('files', [])
    
    if items:
        folder_id = items[0]['id']
    else:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        folder = drive_service.files().create(body=file_metadata, fields='id',supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        folder_id = folder.get('id')

    file = drive_service.files().get(fileId=new_document_id, fields='parents',supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    previous_parents = ",".join(file.get('parents'))
    file = drive_service.files().update(fileId=new_document_id,
                                        addParents=folder_id,
                                        removeParents=previous_parents,
                                        fields='id, parents', supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    print(f"새 문서 ID: {new_document_id}, 저장된 폴더 ID: {folder_id}")
# 투자심의위원회 의사록
def make_docx_fileB(db_1,db_4,db_7, current_time):
    SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = config.kakao_json_key_path
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('docs', 'v1', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)
    document_id = config.fileB_id

    COMPANY_NAME = db_1['회사명'].iloc[0]

    new_document = drive_service.files().copy(fileId=document_id, body={'name': COMPANY_NAME + '_투심위의사록'},supportsAllDrives=True).execute()     
    new_document_id = new_document.get('id')

    INVESTMENT_DATE_MONDAY = get_day_of_week(db_4['투자 납입일'].iloc[0])
    
    BUSINESS_NUMBER = db_1['사업자등록번호'].iloc[0]
    INVESTMENT_CATEGORY = db_4['투자유형(투자시)'].iloc[0]
    NEW_OLD = db_4['신주/구주여부'].iloc[0]
    INVESTMENT_AMOUNT = change_money_form(db_4['투자금액(원화)'].iloc[0]) 
    INVESTMENT_COUNT = change_count_form(db_4['인수 주식수'].iloc[0])
    INVESTMENT_PRICE = change_money_form(db_4['투자단가(원화)'].iloc[0]) 
    SHARE_RATIO = db_4['지분율(투자시점)'].iloc[0]
    FUND_NAME = db_7['펀드명'].iloc[0]
    REPRESENTATIVE_FUND_MANAGER = db_7['대표펀드매니저'].iloc[0].split(", ")
    CORE_OPERATING_PERSONNEL = db_7['핵심운용인력'].iloc[0].split(", ")
    n = len(REPRESENTATIVE_FUND_MANAGER) + len(CORE_OPERATING_PERSONNEL)
    PEOPLE_NUMBER = str(n) + "/" + str(n)
    
    requests = [
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_DATE_MONDAY%$^",
                    'matchCase': 'true'
                },
                'replaceText': INVESTMENT_DATE_MONDAY,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^COMPANY_NAME%$^",
                    'matchCase': 'true'
                },
                'replaceText':COMPANY_NAME,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^BUSINESS_NUMBER%$^",
                    'matchCase': 'true'
                },
                'replaceText':BUSINESS_NUMBER,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^SHARE_RATIO%$^",
                    'matchCase': 'true'
                },
                'replaceText':SHARE_RATIO,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_AMOUNT%$^",
                    'matchCase': 'true'
                },
                'replaceText':INVESTMENT_AMOUNT,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_COUNT%$^",
                    'matchCase': 'true'
                },
                'replaceText':INVESTMENT_COUNT,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_PRICE%$^",
                    'matchCase': 'true'
                },
                'replaceText':INVESTMENT_PRICE,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_CATEGORY%$^",
                    'matchCase': 'true'
                },
                'replaceText':INVESTMENT_CATEGORY,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^FUND_NAME%$^",
                    'matchCase': 'true'
                },
                'replaceText':FUND_NAME,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^NEW_OLD%$^",
                    'matchCase': 'true'
                },
                'replaceText':NEW_OLD,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^PEOPLE_NUMBER%$^",
                    'matchCase': 'true'
                },
                'replaceText':PEOPLE_NUMBER,
            }
        },
    ]

    result = service.documents().batchUpdate(documentId=new_document_id, body={'requests': requests}).execute()
    parent_folder_id = config.fileABCD_parent_folder_id

    folder_name = current_time + "_" + COMPANY_NAME

    query = f"'{parent_folder_id}' in parents and name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name)",supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    items = results.get('files', [])
    
    if items:
        folder_id = items[0]['id']
    else:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        folder = drive_service.files().create(body=file_metadata, fields='id',supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        folder_id = folder.get('id')

    file = drive_service.files().get(fileId=new_document_id, fields='parents',supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    previous_parents = ",".join(file.get('parents'))
    file = drive_service.files().update(fileId=new_document_id,
                                        addParents=folder_id,
                                        removeParents=previous_parents,
                                        fields='id, parents',supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    print(f"새 문서 ID: {new_document_id}, 저장된 폴더 ID: {folder_id}")
    return new_document_id
# 준법사항 체크리스트(벤처투자조합)
def make_docx_fileC(db_1,db_4,db_7,total_investment, total_investment_in, current_time):
    SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = config.kakao_json_key_path
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('docs', 'v1', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)
    document_id = config.fileC_id
    COMPANY_NAME = db_1['회사명'].iloc[0]

    new_document = drive_service.files().copy(fileId=document_id, body={'name': COMPANY_NAME+'_준법사항_체크리스트'},supportsAllDrives=True).execute()     
    new_document_id = new_document.get('id')

    FUND_NAME = db_7['펀드명'].iloc[0]
    COMPANY_NAME = db_1['회사명'].iloc[0]
    COMPANY_REPRESENTATIVE_NAME = db_1['대표자명'].iloc[0]
    BUSINESS_NUMBER = db_1['사업자등록번호'].iloc[0]
    SHARE_RATIO = db_4['지분율(투자시점)'].iloc[0]
    INVESTMENT_CATEGORY = db_4['투자유형(투자시)'].iloc[0]
    INVESTMENT_AMOUNT = change_money_form(db_4['투자금액(원화)'].iloc[0]) 
    INVESTMENT_PRICE = change_money_form(db_4['투자단가(원화)'].iloc[0]) 

    INVESTMENT_CLASSIFICATION = db_1['해외기업여부'].iloc[0]
    if INVESTMENT_CLASSIFICATION =="여":
        INVESTMENT_CLASSIFICATION = "국내(), 해외(O)"
    else:
        INVESTMENT_CLASSIFICATION = "국내(O), 해외( )"

    contract = int(db_7['약정금액'].iloc[0].replace(",", ""))
    VALUE1 = change_money_form(str(total_investment))
    VALUE2 = str(format(round(total_investment * 100 / contract,2) , ".2f"))
    VALUE3 = change_money_form(str(total_investment_in))
    VALUE4 = str(format(round((total_investment_in * 1000) / (contract * 6),2) , ".2f"))
    
    EXCAVATOR1 = db_4['발굴자1'].iloc[0]
    EXCAVATOR1_contribution = db_4['발굴자1 기여도'].iloc[0]
    EXCAVATOR2 = db_4['발굴자2'].iloc[0]
    EXCAVATOR2_contribution = db_4['발굴자2 기여도'].iloc[0]
    EXCAVATOR3 = db_4['발굴자3'].iloc[0]
    EXCAVATOR3_contribution = db_4['발굴자3 기여도'].iloc[0]

    if len(EXCAVATOR3) > 1:
        EXCAVATOR = EXCAVATOR1 + "("+EXCAVATOR1_contribution+")" +"\n" + EXCAVATOR2 + "("+EXCAVATOR2_contribution+")" +"\n" + EXCAVATOR3 + "("+EXCAVATOR3_contribution+")"
    elif len(EXCAVATOR2) > 1:
        EXCAVATOR = EXCAVATOR1 + "("+EXCAVATOR1_contribution+")" +"\n" + EXCAVATOR2 + "("+EXCAVATOR2_contribution+")"
    else:
        EXCAVATOR = EXCAVATOR1 + "("+EXCAVATOR1_contribution+")"

    REVIEWER1 = db_4['심사자1'].iloc[0]
    REVIEWER1_contribution = db_4['심사자1 기여도'].iloc[0]
    REVIEWER2 = db_4['심사자2'].iloc[0]
    REVIEWER2_contribution = db_4['심사자2 기여도'].iloc[0]
    REVIEWER3 = db_4['심사자3'].iloc[0]
    REVIEWER3_contribution = db_4['심사자3 기여도'].iloc[0]
    REVIEWER4 = db_4['심사자4'].iloc[0]
    REVIEWER4_contribution = db_4['심사자4 기여도'].iloc[0]
    REVIEWER5 = db_4['심사자5'].iloc[0]
    REVIEWER5_contribution = db_4['심사자5 기여도'].iloc[0]

    if len(REVIEWER5) > 1:
        REVIEWER = REVIEWER1 + "("+REVIEWER1_contribution+")" +"\n" + REVIEWER2 + "("+REVIEWER2_contribution+")" +"\n" + REVIEWER3 + "("+REVIEWER3_contribution+")" +"\n" + REVIEWER4 + "("+REVIEWER4_contribution+")" +"\n" + REVIEWER5 + "("+REVIEWER5_contribution+")"
    elif len(REVIEWER4) > 1:
        REVIEWER = REVIEWER1 + "("+REVIEWER1_contribution+")" +"\n" + REVIEWER2 + "("+REVIEWER2_contribution+")" +"\n" + REVIEWER3 + "("+REVIEWER3_contribution+")" +"\n" + REVIEWER4 + "("+REVIEWER4_contribution+")"
    elif len(REVIEWER3) > 1:
        REVIEWER = REVIEWER1 + "("+REVIEWER1_contribution+")" +"\n" + REVIEWER2 + "("+REVIEWER2_contribution+")" +"\n" + REVIEWER3 + "("+REVIEWER3_contribution+")"
    elif len(REVIEWER2) > 1:
        REVIEWER = REVIEWER1 + "("+REVIEWER1_contribution+")" +"\n" + REVIEWER2 + "("+REVIEWER2_contribution+")"
    else:
        REVIEWER = REVIEWER1 + "("+REVIEWER1_contribution+")"

    VIGILANCE1 = db_1['사후관리자1'].iloc[0]
    VIGILANCE1_contribution = db_1['기여도1'].iloc[0]
    VIGILANCE2 = db_1['사후관리자2'].iloc[0]
    VIGILANCE2_contribution = db_1['기여도2'].iloc[0]
    VIGILANCE3 = db_1['사후관리자3'].iloc[0]
    VIGILANCE3_contribution = db_1['기여도3'].iloc[0]
    VIGILANCE4 = db_1['사후관리자4'].iloc[0]
    VIGILANCE4_contribution = db_1['기여도4'].iloc[0]

    if len(VIGILANCE4) > 1:
        VIGILANCE = VIGILANCE1 + "("+VIGILANCE1_contribution+")" +"\n" + VIGILANCE2 + "("+VIGILANCE2_contribution+")" +"\n" + VIGILANCE3 + "("+VIGILANCE3_contribution+")" +"\n" + VIGILANCE4 + "("+VIGILANCE4_contribution+")"
    elif len(VIGILANCE3) > 1:
        VIGILANCE = VIGILANCE1 + "("+VIGILANCE1_contribution+")" +"\n" + VIGILANCE2 + "("+VIGILANCE2_contribution+")" +"\n" + VIGILANCE3 + "("+VIGILANCE3_contribution+")"
    elif len(REVIEWER2) > 1:
        VIGILANCE = VIGILANCE1 + "("+VIGILANCE1_contribution+")" +"\n" + VIGILANCE2 + "("+VIGILANCE2_contribution+")"
    else:
        VIGILANCE = VIGILANCE1 + "("+VIGILANCE1_contribution+")"

    RECOGNIZED_INVESTMENT_STATUS = db_4['인정투자여부'].iloc[0] 
    if RECOGNIZED_INVESTMENT_STATUS == "여":
        RECOGNIZED_INVESTMENT_STATUS = "여(Y)"
    else:
        RECOGNIZED_INVESTMENT_STATUS = "부(N)"

    INVESTMENT_AMOUNT_VER2 = change_money_form2(db_4['투자금액(원화)'].iloc[0])
    CONTRACTED_AMOUNT = change_money_form2(int(int(db_7['약정금액'].iloc[0].replace(",", "")) * 0.2))
    INVESTMENT_DATE_MONDAY = get_day_of_week(db_4['투자 납입일'].iloc[0])
    
    requests = [
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_CLASSIFICATION%$^",
                    'matchCase': 'true'
                },
                'replaceText': INVESTMENT_CLASSIFICATION,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^VALUE4%$^",
                    'matchCase': 'true'
                },
                'replaceText': VALUE4,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^VALUE3%$^",
                    'matchCase': 'true'
                },
                'replaceText': VALUE3,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^VALUE2%$^",
                    'matchCase': 'true'
                },
                'replaceText': VALUE2,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^VALUE1%$^",
                    'matchCase': 'true'
                },
                'replaceText': VALUE1,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_DATE_MONDAY%$^",
                    'matchCase': 'true'
                },
                'replaceText': INVESTMENT_DATE_MONDAY,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^COMPANY_NAME%$^",
                    'matchCase': 'true'
                },
                'replaceText':COMPANY_NAME,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^BUSINESS_NUMBER%$^",
                    'matchCase': 'true'
                },
                'replaceText':BUSINESS_NUMBER,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^SHARE_RATIO%$^",
                    'matchCase': 'true'
                },
                'replaceText':SHARE_RATIO,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_AMOUNT%$^",
                    'matchCase': 'true'
                },
                'replaceText':INVESTMENT_AMOUNT,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_PRICE%$^",
                    'matchCase': 'true'
                },
                'replaceText':INVESTMENT_PRICE,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_CATEGORY%$^",
                    'matchCase': 'true'
                },
                'replaceText':INVESTMENT_CATEGORY,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^FUND_NAME%$^",
                    'matchCase': 'true'
                },
                'replaceText':FUND_NAME,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^COMPANY_REPRESENTATIVE_NAME%$^",
                    'matchCase': 'true'
                },
                'replaceText':COMPANY_REPRESENTATIVE_NAME,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^EXCAVATOR%$^",
                    'matchCase': 'true'
                },
                'replaceText':EXCAVATOR,
            }
        },
                {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^REVIEWER%$^",
                    'matchCase': 'true'
                },
                'replaceText':REVIEWER,
            }
        },
                {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^VIGILANCE%$^",
                    'matchCase': 'true'
                },
                'replaceText':VIGILANCE,
            }
        },
                {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_AMOUNT_VER2%$^",
                    'matchCase': 'true'
                },
                'replaceText':INVESTMENT_AMOUNT_VER2,
            }
        },
                {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^CONTRACTED_AMOUNT%$^",
                    'matchCase': 'true'
                },
                'replaceText':CONTRACTED_AMOUNT,
            }
        },
                {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^RECOGNIZED_INVESTMENT_STATUS%$^",
                    'matchCase': 'true'
                },
                'replaceText':RECOGNIZED_INVESTMENT_STATUS,
            }
        }
    ]

    result = service.documents().batchUpdate(documentId=new_document_id, body={'requests': requests}).execute()
    parent_folder_id = config.fileABCD_parent_folder_id

    folder_name = current_time + "_" + COMPANY_NAME

    query = f"'{parent_folder_id}' in parents and name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name)",supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    items = results.get('files', [])
    
    if items:
        folder_id = items[0]['id']
    else:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        folder = drive_service.files().create(body=file_metadata, fields='id',supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        folder_id = folder.get('id')

    file = drive_service.files().get(fileId=new_document_id, fields='parents',supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    previous_parents = ",".join(file.get('parents'))
    file = drive_service.files().update(fileId=new_document_id,
                                        addParents=folder_id,
                                        removeParents=previous_parents,
                                        fields='id, parents',supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    print(f"새 문서 ID: {new_document_id}, 저장된 폴더 ID: {folder_id}")
# 투자집행품의서
def make_docx_fileD(db_1,db_4,db_7, current_time):
    SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = config.kakao_json_key_path
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('docs', 'v1', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)
    document_id = config.fileD_id

    COMPANY_NAME = db_1['회사명'].iloc[0]

    new_document = drive_service.files().copy(fileId=document_id, body={'name': COMPANY_NAME + '_투자집행품의서'},supportsAllDrives=True).execute()     
    new_document_id = new_document.get('id')

    DRAFT_DATE = db_4['투자 납입일'].iloc[0]
    year, month, day = DRAFT_DATE.split('-')
    DRAFT_DATE = f"{year}.{month}.{day}"

    
    INVESTMENT_AMOUNT = change_money_form(db_4['투자금액(원화)'].iloc[0]) 
    INVESTMENT_COUNT = change_count_form(db_4['인수 주식수'].iloc[0])
    INVESTMENT_PRICE = change_money_form(db_4['투자단가(원화)'].iloc[0])
    INVESTMENT_CATEGORY = db_4['투자유형(투자시)'].iloc[0]
    FUND_NAME = db_7['펀드명'].iloc[0]
    
    requests = [
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^DRAFT_DATE%$^",
                    'matchCase': 'true'
                },
                'replaceText': DRAFT_DATE,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^COMPANY_NAME%$^",
                    'matchCase': 'true'
                },
                'replaceText':COMPANY_NAME,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_AMOUNT%$^",
                    'matchCase': 'true'
                },
                'replaceText':INVESTMENT_AMOUNT,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_COUNT%$^",
                    'matchCase': 'true'
                },
                'replaceText':INVESTMENT_COUNT,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_PRICE%$^",
                    'matchCase': 'true'
                },
                'replaceText':INVESTMENT_PRICE,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^INVESTMENT_CATEGORY%$^",
                    'matchCase': 'true'
                },
                'replaceText':INVESTMENT_CATEGORY,
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': "%$^FUND_NAME%$^",
                    'matchCase': 'true'
                },
                'replaceText':FUND_NAME,
            }
        }
    ]

    result = service.documents().batchUpdate(documentId=new_document_id, body={'requests': requests}).execute()
    parent_folder_id = config.fileABCD_parent_folder_id

    folder_name = current_time + "_" + COMPANY_NAME

    query = f"'{parent_folder_id}' in parents and name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name)",supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    items = results.get('files', [])
    
    if items:
        folder_id = items[0]['id']
    else:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        folder = drive_service.files().create(body=file_metadata, fields='id',supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        folder_id = folder.get('id')

    file = drive_service.files().get(fileId=new_document_id, fields='parents',supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    previous_parents = ",".join(file.get('parents'))
    file = drive_service.files().update(fileId=new_document_id,
                                        addParents=folder_id,
                                        removeParents=previous_parents,
                                        fields='id, parents',supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    print(f"새 문서 ID: {new_document_id}, 저장된 폴더 ID: {folder_id}")

def get_extra_info_frome_inv_id(inv_id,fund_num):
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.kakao_json_key_path, scope)
    client = gspread.authorize(creds)
    spreadsheet_id = config.db_4_id  # 스프레드시트 주소에 있는 아이디 가져오기
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.sheet1
    data = worksheet.get_all_values()
    df = pd.DataFrame(data)
    df.columns = df.iloc[0]
    df = df[1:]
    df = df[df['투자한 조합'] == fund_num]

    target_date = pd.to_datetime(df.loc[df['INV ID'] == inv_id, '투자 납입일'].iloc[0])
    df = df[pd.to_datetime(df['투자 납입일']) < target_date]

    df['투자금액(원화)'] = df['투자금액(원화)'].str.replace(',', '')
    df['투자금액(원화)'] = pd.to_numeric(df['투자금액(원화)'])
    total_investment = df['투자금액(원화)'].sum()

    df = df[df['인정투자여부'] == "여"]
    df['투자금액(원화)'] = pd.to_numeric(df['투자금액(원화)'])
    total_investment_in = df['투자금액(원화)'].sum()
    return total_investment, total_investment_in

def update_tableB(db_7,doc_id):

    SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = config.kakao_json_key_path
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('docs', 'v1', credentials=credentials)
    document = service.documents().get(documentId=doc_id).execute()
    content = document.get('body').get('content')

    rep_fund_managers = db_7['대표펀드매니저'].iloc[0].split(", ")
    core_personnels = db_7['핵심운용인력'].iloc[0].split(", ")
    table_contents = []
    
    for manager in rep_fund_managers:
        table_contents.extend(['대표펀드매니저', manager, '찬성', ''])

    for personnel in core_personnels:
        table_contents.extend(['핵심펀드매니저', personnel, '찬성', ''])

    # %$^TABLE%$^ 자리표시자의 인덱스 찾기
    placeholder = '%$^TABLE%$^'
    indices = []

    for element in content:
        if 'table' in element:
            table = element['table']
            for row in table['tableRows']:
                for cell in row['tableCells']:
                    for cell_content in cell['content']:
                        if 'paragraph' in cell_content:
                            for text_run in cell_content['paragraph']['elements']:
                                if 'textRun' in text_run and placeholder in text_run['textRun']['content']:
                                    start_index = text_run['startIndex']
                                    end_index = start_index + len(placeholder)
                                    indices.append((start_index, end_index))

    if len(indices) < len(table_contents):
        print("Not enough placeholders in the document.")
        return

    # %$^TABLE%$^ 자리표시자를 뒤에서부터 table_contents로 대체
    requests = []
    for i in range(len(table_contents)-1, -1, -1):
        start_index, end_index = indices[i]
        requests.append({
            'deleteContentRange': {
                'range': {
                    'startIndex': start_index,
                    'endIndex': end_index
                }
            }
        })
        # 빈 문자열을 피하기 위한 확인 추가
        if table_contents[i]:
            requests.append({
                'insertText': {
                    'location': {
                        'index': start_index
                    },
                    'text': table_contents[i]
                }
            })

    result = service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    print(f'Updated {len(result.get("replies")) // 2} placeholders in the document.')

def update_tableB_ver2(doc_id):

    SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = config.kakao_json_key_path
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('docs', 'v1', credentials=credentials)
    document = service.documents().get(documentId=doc_id).execute()
    content = document.get('body').get('content')

    search_string = '%$^TABLE%$^'

    requests = []
    # Traverse the document to find tables
    for element in content:
        if 'table' in element:
            table = element['table']
            table_rows = table['tableRows']

            # Iterate through rows in reverse order to prevent index shifting issues
            for row_index in range(len(table_rows) - 1, -1, -1):
                row_contains_string = False
                row = table_rows[row_index]
                for cell in row['tableCells']:
                    cell_content = cell['content']
                    for cell_element in cell_content:
                        if 'paragraph' in cell_element:
                            paragraph = cell_element['paragraph']
                            for elem in paragraph['elements']:
                                if 'textRun' in elem:
                                    text = elem['textRun'].get('content', '')
                                    if search_string in text:
                                        row_contains_string = True
                                        break
                    if row_contains_string:
                        break
                
                if row_contains_string:
                    requests.append({
                        'deleteTableRow': {
                            'tableCellLocation': {
                                'tableStartLocation': {
                                    'index': element['startIndex']
                                },
                                'rowIndex': row_index
                            }
                        }
                    })

    # Execute the batch update
    if requests:
        result = service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()

        print(f"Deleted rows containing '{search_string}' from the document.")

def get_all_company_names():
    scope1 = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds1 = ServiceAccountCredentials.from_json_keyfile_name(config.kakao_json_key_path, scope1)
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

def get_kv_id_from_inv_id(inv_id):
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.kakao_json_key_path, scope)
    client = gspread.authorize(creds)
    spreadsheet_id = config.db_4_id  # 스프레드시트 주소에 있는 아이디 가져오기
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.sheet1
    data = worksheet.get_all_values()
    df = pd.DataFrame(data)
    df.columns = df.iloc[0]
    df = df[1:]
    row = df[df['INV ID'] == inv_id]
    kv_id = row['KV ID'].iloc[0]
    return kv_id

def get_inv_list_and_date(company_name):
    kv_id = get_company_id_from_company_name(company_name)
    _, matching_rows = get_inv_id_from_company_id(kv_id)
    selected_columns = matching_rows[['INV ID', '투자 납입일']]
    investments = []
    for index, row in selected_columns.iterrows():
        investments.append({'inv_id': row['INV ID'], 'investment_date': row['투자 납입일']})
    return investments

if __name__ == "__main__":
    # all_company_names = get_all_company_names()
    # print(all_company_names)
    # print(investments)
    # id,name = get_last_company_name()
    kv_id = get_company_id_from_company_name("(주)라포랩스")
    inv_id, _ = get_inv_id_from_company_id(kv_id)

    # kv_id = get_kv_id_from_inv_id(inv_id)
    print(inv_id)
    inv_id = inv_id[2]
    db_1 = get_db1_info_from_kv_id(kv_id)
    db_4 = get_db4_info_from_inv_id(inv_id)
    fund_num = db_4['투자한 조합'].iloc[-1]
    db_7 = get_db7_info_from_fund_num(fund_num)
    print(db_7)
    total_investment, total_investment_in = get_extra_info_frome_inv_id(inv_id,fund_num)
    make_docx_fileA(db_1,db_4,db_7)
    new_document_id = make_docx_fileB(db_1,db_4,db_7)
    update_tableB(db_7,new_document_id)
    update_tableB_ver2(new_document_id)
    make_docx_fileC(db_1, db_4, db_7, total_investment, total_investment_in)
    make_docx_fileD(db_1,db_4,db_7)