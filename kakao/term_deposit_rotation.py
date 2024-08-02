from formatting import process_user_input, get_proper_file_name
import googleapi
import gspread
import chatgpt
import json
import requests
from config import deposit_id, kakao_json_key_path
from openai import OpenAI
import pandas as pd
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
import pandas as pd
import json
import numpy as np
from directMessageApi import send_direct_message_to_user
from translator import clean_and_convert_to_int
import time

def deposit_rotation_system_handler(message, say, user_states):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        msg = (f"정기예금 회전 시스템을 종료합니다.\n")
        send_direct_message_to_user(user_id, msg)
        del user_states[user_id]
    else:
        if user_input.isdigit():
            if user_input == "1": # 질문하기(일반모델)(약 1원)
                msg = (f"원하는 질문을 입력해주세요\n"
                    "주의사항 본 서비스는 유료 서비스입니다 정기예금 회전 시스템과 관련된 질문만 해주세요\n"
                    "(종료를 원하시면 '종료'를 입력해주세요)\n"
                    )
                send_direct_message_to_user(user_id, msg)
                user_states[user_id] = 'deposit_rotation_waiting_low_chatgpt_input'
            # elif user_input == "2": # 질문하기(상위모델)(약 10원)
            #     msg = (f"<@{user_id}> 원하는 질문을 입력해주세요(상위모델 사용)\n"
            #         "주의사항 본 서비스는 유료 서비스입니다 정기예금 회전 시스템과 관련된 질문만 해주세요\n"
            #         "(종료를 원하시면 '종료'를 입력해주세요)\n"
            #         )
            #     send_direct_message_to_user(user_id, msg)
            #     user_states[user_id] = 'deposit_rotation_waiting_high_chatgpt_input'
            else:
                msg = (f"<@{user_id}> 잘못된 숫자를 입력했습니다. 다시 입력해주세요.\n")
                send_direct_message_to_user(user_id, msg)
                user_states[user_id] = 'deposit_rotation_waiting_only_number'
        else:
            msg = (f"<@{user_id}> 숫자만 입력해주세요. 다시 입력해주세요.")
            send_direct_message_to_user(user_id, msg)
            user_states[user_id] = 'deposit_rotation_waiting_only_number'

def deposit_rotation_system_low_model_handler(message, say, user_states):

    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        msg = (f"정기예금 회전 시스템을 종료합니다.\n")
        send_direct_message_to_user(user_id, msg)
        del user_states[user_id]
    else:
        msg = (f"답변을 준비중입니다...\n")
        send_direct_message_to_user(user_id, msg)
        answer = qna_chatgpt_low_model(user_input)
        msg = (f"{answer}\n 종료합니다.")
        send_direct_message_to_user(user_id, msg)
        del user_states[user_id]

# def deposit_rotation_system_high_model_handler(message, say, user_states):
#     user_id = message['user']
#     user_input = message['text']
#     user_input = process_user_input(user_input)
#     if user_input == '종료':
#         msg = (f"<@{user_id}> 정기예금 회전 시스템을 종료합니다.\n")
#         send_direct_message_to_user(user_id, msg)
#         del user_states[user_id]
#     else:
#         msg = (f"<@{user_id}> 답변을 준비중입니다...\n")
#         send_direct_message_to_user(user_id, msg)
#         answer = qna_chatgpt_high_model(user_input)
#         msg = (f"<@{user_id}> {answer}\n 답변이 완료되었습니다.")
#         send_direct_message_to_user(user_id, msg)
#         del user_states[user_id]

def qna_chatgpt_low_model(user_input):
    # try:
    from datetime import datetime
    # 오늘 날짜를 구함
    today = datetime.now().date()

    prompt = ""
    client = OpenAI(api_key='sk-proj-KvJ1AX8zCUYXlEL7Q0fmT3BlbkFJghD5VpM4HRcyi0f8TBCQ')
    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
        "role": "system",
        "content": prompt
        },
        {
        "role": "user",
        "content": "오늘날짜\n" + today + "\n참고자료\n" + deposit_data_to_json() + "\n" + user_input
        }
    ],)
    output = response.choices[0].message.content
    # except Exception as e:
    #     print(f"qna_chatgpt_low_model chatgpt error: {e}")
    #     return "서버 오류로 인해 사용이 불가능합니다 잠시후 다시 이용해 주세요"
    return output

# def qna_chatgpt_high_model(user_input):
#     try:
#         prompt = ""
#         client = OpenAI(api_key='sk-proj-KvJ1AX8zCUYXlEL7Q0fmT3BlbkFJghD5VpM4HRcyi0f8TBCQ')
#         response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[
#             {
#             "role": "system",
#             "content": prompt
#             },
#             {
#             "role": "user",
#             "content": deposit_data_to_json() + "\n" + user_input
#             }
#         ],)
#         output = response.choices[0].message.content
#     except Exception as e:
#         print(f"qna_chatgpt_high_model chatgpt error: {e}")
#         return "서버 오류로 인해 사용이 불가능합니다 잠시후 다시 이용해 주세요"
#     return output

def get_pending_payments_per_month():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(kakao_json_key_path, scope)
    client = gspread.authorize(creds)
    spreadsheet_id = deposit_id
    spreadsheet = client.open_by_key(spreadsheet_id)

    sheet = spreadsheet.worksheet('본계정_미수금액')
    # 첫번째 행을 제외한 데이터를 가지고 온다
    data = sheet.get_all_values()[1:]

    return data

def get_pending_payments_per_quarter():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(kakao_json_key_path, scope)
    client = gspread.authorize(creds)
    spreadsheet_id = deposit_id
    spreadsheet = client.open_by_key(spreadsheet_id)

    # 미수금액 이라는 문자열이 포함된 시트만 확인
    # 본계정_미수금액을 제외한 나머지 시트의 모든 데이터를 반환한다
    # 결과를 저장할 리스트
    all_data = []

    # 스프레드시트 내 모든 시트를 가져옴
    worksheets = spreadsheet.worksheets()

    # 각 시트를 순회하면서 "미수금액"이 포함된 시트를 확인
    for sheet in worksheets:
        if "미수금액" in sheet.title and sheet.title != "본계정_미수금액":
            # 첫번째 행을 제외한 데이터를 가지고 온다 
            data = sheet.get_all_values()[1:]
            all_data.append({
                "sheet_name": sheet.title,
                "data": data
            })
            all_data.append("delimeter")

    return all_data

def valid_deposit_df():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(kakao_json_key_path, scope)
    client = gspread.authorize(creds)
    spreadsheet_id = deposit_id
    spreadsheet = client.open_by_key(spreadsheet_id)

    # 미수금액 시트만 조회한다
    # 시작일, 만기일 조건을 확인하여 해당되지 않은 행만 확인한다
    for sheet in spreadsheet.worksheets():
        sheet_name = sheet.title
        if '미수금액' in sheet_name:
            checking_sheet = spreadsheet.worksheet(sheet_name)
            data = checking_sheet.get_all_records()

            # DataFrame으로 변환하여 시작일과 만기일을 확인
            df = pd.DataFrame(data)
            for index, row in df.iterrows():
                start_date = datetime.strptime(row['신규일'], '%Y-%m-%d')
                end_date = datetime.strptime(row['만기일'], '%Y-%m-%d')
                current_date = datetime.now()

                # 시작일과 만기일 조건을 확인
                if not (start_date <= current_date < end_date):
                    # 조건에 해당되지 않는 경우 '미수금액'을 0으로 업데이트
                    df.at[index, '미수금액'] = 0

            # DataFrame을 리스트로 변환하여 시트에 업데이트
            updated_data = df.values.tolist()
            checking_sheet.update(updated_data, 'A2')

def update_or_append_row(sheet, new_row):
    existing_data = sheet.get_all_values()
    for i, row in enumerate(existing_data):
        # 계좌번호를 기준으로 동일한 데이터를 찾음 (필요에 따라 다른 열을 비교 기준으로 사용 가능)
        if row[4] == new_row[4] and row[0] == new_row[0]:  # 계산 기준일 비교
            sheet.update(
                range_name=f'A{i+1}',  # 범위를 지정하는 인자
                values=[new_row]       # 업데이트할 데이터
            )
            
    sheet.append_row(new_row)  # 새로운 행 추가

def update_deposit_df():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(kakao_json_key_path, scope)
    client = gspread.authorize(creds)
    spreadsheet_id = deposit_id
    spreadsheet = client.open_by_key(spreadsheet_id)

    # '##...+'_미수금액' 시트명 존재하는지 확인
    for sheet in spreadsheet.worksheets():
        sheet_name = sheet.title
        if sheet_name.startswith('##'):
            # 새로운 시트 이름 생성
            new_sheet_name = sheet_name[2:] + '_미수금액'
            # 새로운 시트가 존재하지 않는 경우 추가
            if new_sheet_name not in [ws.title for ws in spreadsheet.worksheets()]:
                new_sheet = spreadsheet.add_worksheet(title=new_sheet_name, rows="100", cols="20")
                # 새로운 시트에 컬럼 이름 추가
                columns = ['가입유형', '정기예금 가입액', '이자율', '가입일', '계산기준일', '경과일수', '이자 금액']
                new_sheet.append_row(columns)

    # deposit_info는 ['금융기관', '거래지점', '계좌번호', '신규일', '만기일', '최초금액', '금리', '해지원금', '이자', '기타', '중도해지유무', '시트명'] 으로 구성된 데이터
    deposit_info = extract_deposit_df()

    for index, row in deposit_info.iterrows():
        # 시트명을 '시트명_미수금액'으로 설정
        sheet_name = row['시트명'] + '_미수금액'
        new_sheet = spreadsheet.worksheet(sheet_name)

        # 계산 기준일 - 현재 날짜로 설정
        calc_date = datetime.now()
        
        # 신규일을 datetime 형식으로 변환
        start_date = datetime.strptime(row['신규일'], '%Y-%m-%d')
        
        # 경과 일수 계산
        days_difference = (calc_date - start_date).days
        
        # 이자율을 숫자로 변환 (백분율 제거 및 소수로 변환)
        interest_rate = float(row['금리'].strip('%')) / 100
        
        # 연도의 일수 (윤년 고려)
        year_days = 366 if start_date.year % 4 == 0 and (start_date.year % 100 != 0 or start_date.year % 400 == 0) else 365
        
        # 이자 금액 계산
        interest_amount = interest_rate * days_difference * float(clean_and_convert_to_int(row['최초금액'])) / year_days
        
        new_row = []
        new_row.append(row['금융기관'] + ' ' + '정기예금' + ' ' + row['계좌번호'])
        new_row.append(row['최초금액'])
        new_row.append(row['금리'])
        new_row.append(row['신규일'])
        new_row.append(calc_date.strftime('%Y-%m-%d'))
        new_row.append(days_difference)
        new_row.append(interest_amount)

        update_or_append_row(new_sheet, new_row)
        time.sleep(1)  # 1초 딜레이 추가

    print("One Completed!")

def extract_deposit_df():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(kakao_json_key_path, scope)
    client = gspread.authorize(creds)
    spreadsheet_id = deposit_id
    spreadsheet = client.open_by_key(spreadsheet_id)
    final_df = pd.DataFrame()
    # Iterate through all the sheets in the spreadsheet
    for sheet in spreadsheet.worksheets():
        sheet_name = sheet.title
        if sheet_name.startswith('##'):
            # Get all values from the sheet
            data = sheet.get_all_values()
            df = pd.DataFrame(data)
            
            # Extract column names and set them
            columns = df.iloc[0].tolist()
            df = df[1:]
            df.columns = columns
            df = drop_empty_rows(df)
            df = fill_missing_values(df)
            df = replace_nan_with_empty_string(df)
            # Add a new column for the sheet name (without '##')
            df['시트명'] = sheet_name[2:]
            
            # Append to the final DataFrame
            final_df = pd.concat([final_df, df], ignore_index=True)

    # 오늘 날짜의 월을 구합니다.
    current_month = datetime.now().month

    # '신규일'과 '만기일'을 datetime 형식으로 변환합니다.
    final_df['신규일'] = pd.to_datetime(final_df['신규일'])
    final_df['만기일'] = pd.to_datetime(final_df['만기일'])

    # 현재 날짜를 얻습니다.
    current_date = datetime.now()

    # '신규일'과 '만기일' 사이에 있는 행들을 필터링합니다.
    final_df = final_df[(final_df['신규일'] <= current_date) & (final_df['만기일'] > current_date)]

    # '신규일'과 '만기일'을 다시 문자열 형식으로 변환합니다.
    final_df['신규일'] = final_df['신규일'].dt.strftime('%Y-%m-%d')
    final_df['만기일'] = final_df['만기일'].dt.strftime('%Y-%m-%d')
    # final_df['만기일'] = pd.to_datetime(final_df['만기일'])
    # current_date = datetime.now()
    # three_months_later = current_date + timedelta(days=90)

    # within_three_months = final_df[final_df['만기일'] <= three_months_later]
    # earliest_three = final_df.nsmallest(3, '만기일')
    return final_df

def deposit_data_to_json():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(kakao_json_key_path, scope)
    client = gspread.authorize(creds)
    spreadsheet_id = deposit_id
    spreadsheet = client.open_by_key(spreadsheet_id)
    final_df = pd.DataFrame()
    for sheet in spreadsheet.worksheets():
        sheet_name = sheet.title
        if sheet_name.startswith('##'):
            # Get all values from the sheet
            data = sheet.get_all_values()
            df = pd.DataFrame(data)
            
            # Extract column names and set them
            columns = df.iloc[0].tolist()
            df = df[1:]
            df.columns = columns
            df = drop_empty_rows(df)
            df = fill_missing_values(df)
            df = replace_nan_with_empty_string(df)
            # Add a new column for the sheet name (without '##')
            df['스프레드시트명'] = sheet_name[2:]
            
            # Append to the final DataFrame
            final_df = pd.concat([final_df, df], ignore_index=True)
    current_time = datetime.now()
    final_df['신규일'] = pd.to_datetime(final_df['신규일'])
    final_df['만기일'] = pd.to_datetime(final_df['만기일'])
    final_df = final_df[(final_df['신규일'] <= current_time) & (final_df['만기일'] >= current_time) & (~final_df.apply(lambda row: row.astype(str).str.contains('해지').any(), axis=1))]
    final_df['신규일'] = final_df['신규일'].dt.strftime('%Y-%m-%d')
    final_df['만기일'] = final_df['만기일'].dt.strftime('%Y-%m-%d')
    return convert_to_json(final_df)

def replace_nan_with_empty_string(df):
    return df.replace(np.nan, "", inplace=False)

def drop_empty_rows(df):
    for col in df.columns:
        df[col] = df[col].map(lambda x: np.nan if x == "" else x)
    return df.dropna(how='all')

def fill_missing_values(df):
    df["금융기관"] = df["금융기관"].ffill()
    df["거래지점"] = df["거래지점"].ffill()
    df["계좌번호"] = df["계좌번호"].ffill()
    df["최초금액"] = df["최초금액"].ffill()
    return df

def convert_to_json(df):
    records = []
    grouped = df.groupby(['거래지점', '계좌번호', '최초금액','스프레드시트명'])

    for name, group in grouped:
        금융기관 = group.iloc[0]['금융기관']
        거래지점 = name[0]
        계좌번호 = name[1]
        최초금액 = name[2]
        시트명 = name[3]
        
        data = []
        for _, row in group.iterrows():
            data.append({
                "신규일": row["신규일"],
                "만기일": row["만기일"],
                "금리": row["금리"],
                "해지원금": row["해지원금"],
                "이자": row["이자"],
                "기타": row["기타"],
                "중도해지유무": row["중도해지유무"]
            })
        
        record = {
            "스프레드시트명": 시트명,
            "금융기관": 금융기관,
            "거래지점": 거래지점,
            "계좌번호": 계좌번호,
            "최초금액": 최초금액,
            "예금정보": data
        }
        records.append(record)
    # return json.dumps(records, ensure_ascii=False)
    return json.dumps(records, indent=4,ensure_ascii=False)