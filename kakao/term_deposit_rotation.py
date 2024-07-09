from formatting import process_user_input, get_proper_file_name
import googleapi
import gspread
import chatgpt
import json
import requests
from config import deposit_id
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

def deposit_rotation_system_handler(message, say, user_states):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        msg = (f"<@{user_id}> 정기예금 회전 시스템을 종료합니다.\n")
        send_direct_message_to_user(user_id, msg)
        del user_states[user_id]
    else:
        if user_input.isdigit():
            if user_input == "1": # 질문하기(일반모델)(약 1원)
                msg = (f"<@{user_id}> 원하는 질문을 입력해주세요(일반모델 사용)\n"
                    "주의사항 본 서비스는 유료 서비스입니다 정기예금 회전 시스템과 관련된 질문만 해주세요\n"
                    "(종료를 원하시면 '종료'를 입력해주세요)\n"
                    )
                send_direct_message_to_user(user_id, msg)
                user_states[user_id] = 'deposit_rotation_waiting_low_chatgpt_input'
            elif user_input == "2": # 질문하기(상위모델)(약 10원)
                msg = (f"<@{user_id}> 원하는 질문을 입력해주세요(상위모델 사용)\n"
                    "주의사항 본 서비스는 유료 서비스입니다 정기예금 회전 시스템과 관련된 질문만 해주세요\n"
                    "(종료를 원하시면 '종료'를 입력해주세요)\n"
                    )
                send_direct_message_to_user(user_id, msg)
                user_states[user_id] = 'deposit_rotation_waiting_high_chatgpt_input'
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
        msg = (f"<@{user_id}> 정기예금 회전 시스템을 종료합니다.\n")
        send_direct_message_to_user(user_id, msg)
        del user_states[user_id]
    else:
        msg = (f"<@{user_id}> 답변을 준비중입니다...\n")
        send_direct_message_to_user(user_id, msg)
        answer = qna_chatgpt_low_model(user_input)
        msg = (f"<@{user_id}> {answer}\n 답변이 완료되었습니다.")
        send_direct_message_to_user(user_id, msg)
        del user_states[user_id]

def deposit_rotation_system_high_model_handler(message, say, user_states):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        msg = (f"<@{user_id}> 정기예금 회전 시스템을 종료합니다.\n")
        send_direct_message_to_user(user_id, msg)
        del user_states[user_id]
    else:
        msg = (f"<@{user_id}> 답변을 준비중입니다...\n")
        send_direct_message_to_user(user_id, msg)
        answer = qna_chatgpt_high_model(user_input)
        msg = (f"<@{user_id}> {answer}\n 답변이 완료되었습니다.")
        send_direct_message_to_user(user_id, msg)
        del user_states[user_id]

def qna_chatgpt_low_model(user_input):
    try:
        prompt = ""
        client = OpenAI(api_key='sk-proj-KvJ1AX8zCUYXlEL7Q0fmT3BlbkFJghD5VpM4HRcyi0f8TBCQ')
        response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
            "role": "system",
            "content": prompt
            },
            {
            "role": "user",
            "content": deposit_data_to_json() + "\n" + user_input
            }
        ],)
        output = response.choices[0].message.content
    except Exception as e:
        print(f"qna_chatgpt_low_model chatgpt error: {e}")
        return "서버 오류로 인해 사용이 불가능합니다 잠시후 다시 이용해 주세요"
    return output

def qna_chatgpt_high_model(user_input):
    try:
        prompt = ""
        client = OpenAI(api_key='sk-proj-KvJ1AX8zCUYXlEL7Q0fmT3BlbkFJghD5VpM4HRcyi0f8TBCQ')
        response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
            "role": "system",
            "content": prompt
            },
            {
            "role": "user",
            "content": deposit_data_to_json() + "\n" + user_input
            }
        ],)
        output = response.choices[0].message.content
    except Exception as e:
        print(f"qna_chatgpt_high_model chatgpt error: {e}")
        return "서버 오류로 인해 사용이 불가능합니다 잠시후 다시 이용해 주세요"
    return output

def extract_deposit_df():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('kakao-test-422905-9ed51f908a0f.json', scope)
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
    current_time = datetime.now()
    final_df['신규일'] = pd.to_datetime(final_df['신규일'])
    final_df['만기일'] = pd.to_datetime(final_df['만기일'])
    final_df = final_df[(final_df['신규일'] <= current_time) & (final_df['만기일'] >= current_time)]
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
    creds = ServiceAccountCredentials.from_json_keyfile_name('kakao-test-422905-9ed51f908a0f.json', scope)
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
            df['시트명'] = sheet_name[2:]
            
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
    df.replace("", np.nan, inplace=True)
    return df.dropna(how='all')

def fill_missing_values(df):
    df["금융기관"] = df["금융기관"].fillna(method='ffill')
    df["거래지점"] = df["거래지점"].fillna(method='ffill')
    df["종류"] = df["종류"].fillna(method='ffill')
    df["계좌번호"] = df["계좌번호"].fillna(method='ffill')
    df["최초금액"] = df["최초금액"].fillna(method='ffill')
    return df

def convert_to_json(df):
    records = []
    grouped = df.groupby(['거래지점', '종류', '계좌번호', '최초금액','시트명'])

    for name, group in grouped:
        금융기관 = group.iloc[0]['금융기관']
        거래지점 = name[0]
        종류 = name[1]
        계좌번호 = name[2]
        최초금액 = name[3]
        시트명 = name[4]
        
        data = []
        for _, row in group.iterrows():
            data.append({
                "신규일": row["신규일"],
                "만기일": row["만기일"],
                "금리": row["금리"],
                "해지원금": row["해지 원금"],
                "해지이자": row["해지 이자"],
                "기타": row["기타"]
            })
        
        record = {
            "시트명": 시트명,
            "금융기관": 금융기관,
            "거래지점": 거래지점,
            "종류": 종류,
            "계좌번호": 계좌번호,
            "최초금액": 최초금액,
            "예금정보": data
        }
        records.append(record)
    # return json.dumps(records, ensure_ascii=False)
    return json.dumps(records, indent=4,ensure_ascii=False)

if __name__ == "__main__":
    print(deposit_data_to_json())
    print(extract_deposit_df())