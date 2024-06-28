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

def deposit_rotation_system_handler(message, say, user_states):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        say(f"<@{user_id}> 정기예금 회전 시스템을 종료합니다.\n")
        del user_states[user_id]
    else:
        if user_input.isdigit():
            if user_input == "1": # 질문하기(일반모델)(약 1원)
                say(f"<@{user_id}> 원하는 질문을 입력해주세요(일반모델 사용료 약 1원)\n"
                    "주의사항 본 서비스는 유료 서비스입니다 정기예금 회전 시스템과 관련된 질문만 해주세요\n"
                    "(종료를 원하시면 '종료'를 입력해주세요)\n"
                    )
                user_states[user_id] = 'deposit_rotation_waiting_low_chatgpt_input'
            elif user_input == "2": # 질문하기(상위모델)(약 10원)
                say(f"<@{user_id}> 원하는 질문을 입력해주세요(상위모델 사용료 약 10원)\n"
                    "주의사항 본 서비스는 유료 서비스입니다 정기예금 회전 시스템과 관련된 질문만 해주세요\n"
                    "(종료를 원하시면 '종료'를 입력해주세요)\n"
                    )
                user_states[user_id] = 'deposit_rotation_waiting_high_chatgpt_input'
            elif user_input == "3": # 최종 만기일이 다가온 정기예금 상품조회
                within_three_months, earliest_three = extract_near_deposit_info()
                say(f"<@{user_id}> 만기일이 3개월 이내로 남은 정보:\n"
                    f"{within_three_months}\n"
                    f"<@{user_id}>만기일이 가장 빠른 3개의 정보:\n"
                    f"{earliest_three}\n"
                    "조회가 끝났습니다.\n"
                    )
                del user_states[user_id]
            else:
                say(f"<@{user_id}> 잘못된 숫자를 입력했습니다. 다시 입력해주세요.\n")
                user_states[user_id] = 'deposit_rotation_waiting_only_number'
        else:
            say(f"<@{user_id}> 숫자만 입력해주세요. 다시 입력해주세요.")
            user_states[user_id] = 'deposit_rotation_waiting_only_number'

def deposit_rotation_system_low_model_handler(message, say, user_states):

    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        say(f"<@{user_id}> 정기예금 회전 시스템을 종료합니다.\n")
        del user_states[user_id]
    else:
        answer = qna_chatgpt_low_model(user_input)
        say(f"<@{user_id}> {answer}\n 답변이 완료되었습니다.")
        del user_states[user_id]

def deposit_rotation_system_high_model_handler(message, say, user_states):
    user_id = message['user']
    user_input = message['text']
    user_input = process_user_input(user_input)
    if user_input == '종료':
        say(f"<@{user_id}> 정기예금 회전 시스템을 종료합니다.\n")
        del user_states[user_id]
    else:
        answer = qna_chatgpt_high_model(user_input)
        say(f"<@{user_id}> {answer}\n 답변이 완료되었습니다.")
        del user_states[user_id]

def qna_chatgpt_low_model(user_input):
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
    return output

def qna_chatgpt_high_model(user_input):
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
    return output

def extract_near_deposit_info():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('kakao-test-422905-9ed51f908a0f.json', scope)
    client = gspread.authorize(creds)
    spreadsheet_id = deposit_id
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.sheet1
    data = worksheet.get_all_values()
    df = pd.DataFrame(data)
    columns = df.iloc[0].tolist()
    df = df[1:]
    df.columns = columns
    df = drop_empty_rows(df)
    df = fill_missing_values(df)
    df = replace_nan_with_empty_string(df)
    df['만기일'] = pd.to_datetime(df['만기일'])

    current_date = datetime.now()
    three_months_later = current_date + timedelta(days=90)

    within_three_months = df[df['만기일'] <= three_months_later]
    earliest_three = df.nsmallest(3, '만기일')
    return within_three_months, earliest_three

def deposit_data_to_json():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('kakao-test-422905-9ed51f908a0f.json', scope)
    client = gspread.authorize(creds)
    spreadsheet_id = deposit_id
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.sheet1
    data = worksheet.get_all_values()
    df = pd.DataFrame(data)
    columns = df.iloc[0].tolist()
    df = df[1:]
    df.columns = columns
    df = drop_empty_rows(df)
    df = fill_missing_values(df)
    df = replace_nan_with_empty_string(df)
    return convert_to_json(df)

def replace_nan_with_empty_string(df):
    return df.replace(np.nan, "", inplace=False)

def drop_empty_rows(df):
    df.replace("", np.nan, inplace=True)
    return df.dropna(how='all')

def fill_missing_values(df):
    df.fillna(method='ffill', inplace=True)
    return df

def convert_to_json(df):
    records = []
    grouped = df.groupby(['거래지점', '종류', '계좌번호', '최초금액', '기타'])

    for name, group in grouped:
        금융기관 = group.iloc[0]['금융기관']
        거래지점 = name[0]
        종류 = name[1]
        계좌번호 = name[2]
        최초금액 = name[3]
        기타 = name[4]
        
        날짜 = []
        for _, row in group.iterrows():
            날짜.append({
                "신규일": row["신규일"],
                "만기일": row["만기일"],
                "금리": row["금리"]
            })
        
        record = {
            "금융기관": 금융기관,
            "거래지점": 거래지점,
            "종류": 종류,
            "계좌번호": 계좌번호,
            "최초금액": 최초금액,
            "기타": 기타,
            "날짜": 날짜
        }
        records.append(record)
    return json.dumps(records, ensure_ascii=False)
    # return json.dumps(records, indent=4,ensure_ascii=False)

if __name__ == "__main__":
    extract_near_deposit_info()