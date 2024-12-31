from google.oauth2 import service_account
from googleapiclient.discovery import build
from openai import OpenAI
from collections import OrderedDict

import gspread
import re
import json

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/cloud-platform']
SERVICE_ACCOUNT_FILE = r'C:\Users\KV_dev\Desktop\K_adventure\kakao\zerobot-425701-15f85b16185c.json'
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=creds)

def normalize_text(text):
    import unicodedata
    return unicodedata.normalize('NFC', text).replace(" ", "")

def list_file_names_in_folder(folder_id):
    """
    Google Drive API를 사용해 지정된 폴더의 파일명을 리스트 형태로 반환합니다.
    Returns:
        list: 폴더 내 파일명의 리스트. (예: ['file1', 'file2', ...])
    """
    # 폴더 내 파일 검색 쿼리
    query = f"'{folder_id}' in parents and trashed = false"
    
    # 파일 검색
    results = service.files().list(
        q=query,
        fields="files(name)",  # 파일 이름만 가져오기
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    
    # 검색 결과에서 파일명 추출
    items = results.get('files', [])
    file_names = [file['name'].split('_')[0] for file in items]  # '_' 앞부분만 추출

    if not file_names:
        print('No files found.')
        return []
    else:
        return file_names

def list_files_in_folder(folder_id):
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=query,
        supportsAllDrives=True,            # 공유 드라이브 지원
        includeItemsFromAllDrives=True      # 공유 드라이브의 항목 포함
    ).execute()
    items = results.get('files', [])
    
    if not items:
        print('No files found.')
        return []
    else:
        return items
    
from googleapiclient.http import MediaIoBaseDownload
import io

def download_file_data(file_id):
    request = service.files().get_media(fileId=file_id, supportsAllDrives=True)  # supportsAllDrives=True 추가
    file_data = io.BytesIO()
    downloader = MediaIoBaseDownload(file_data, request, chunksize=1024*1024)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    file_data.seek(0)
    return file_data

import pdfplumber
import pandas as pd
from io import BytesIO
def process_pdf(file_data):
    text = ''
    with pdfplumber.open(file_data) as pdf:
        for page_number, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                lines = page_text.splitlines()
                text += f"\n--- Page {page_number + 1} ---\n"
                
                for line_number, line in enumerate(lines):
                    # 빈 줄이나 비어 있는 텍스트 블록을 '[빈값]'으로 표시
                    if not line.strip():  # 라인이 비어 있는 경우
                        text += f"{line_number + 1}: [빈값]\n"
                    else:
                        text += f"{line_number + 1}: {line}\n"
            else:
                text += f"\n--- Page {page_number + 1} ---\nNo text found on this page.\n"
                
    return text

import pandas as pd
import io

def process_excel(file_data):
    xls = pd.ExcelFile(file_data)
    all_text = ''
    
    for sheet_name in xls.sheet_names:  # 모든 시트를 순회
        try:
            df = pd.read_excel(file_data, sheet_name=sheet_name, dtype=str)  # 모든 값을 문자열로 변환
            all_text += f"\n--- 시트: {sheet_name} ---\n"
            
            # 각 행을 순회하며 데이터 처리
            for index, row in df.iterrows():
                # 빈 값(NaN, None 등)을 '[빈값]'으로 대체
                row_text = ', '.join([str(value) if pd.notna(value) and value not in ['None', ''] else '[빈값]' for value in row.values])
                all_text += f"{index}: {row_text}\n"  # 행 번호와 데이터를 결합하여 저장
        except Exception as sheet_error:
            all_text += f"\n--- 시트: {sheet_name} 에서 오류 발생: {sheet_error} ---\n"
    
    return all_text


import base64
import requests
def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')
import os
from pdf2image import convert_from_bytes
def pdf_to_images_base64(file_data):

    poppler_path = r"C:\Users\KV_dev\Release-24.08.0-0\poppler-24.08.0\Library\bin"
    os.environ["PATH"] += os.pathsep + poppler_path
    
    # Convert PDF to images (one per page)
    images = convert_from_bytes(file_data.read(), poppler_path=poppler_path)
    
    # Encode each image to base64
    all_images_base64 = []
    for image in images:
        img_str = encode_image(image)
        all_images_base64.append(img_str)
    
    return all_images_base64

def send_single_image(image_data):
    
    # prompt = """입력된 이미지에서 숫자와 텍스트를 정확히 전부 추출해. 추출된 정보는 이미지를 기준으로 한줄씩 출력이 되면 좋겠어 예를들어
    #         1번째줄. ~~~
    #         2번째줄. ~~~\n
    #         이런식으로 출력해. 추출한 정보 사이의 공백이 있으면 적당한 탭이나 띄어쓰기로 구분을 해.
    #         이미지에 날인(도장)이 있다면 0. 날인확인 이라는 문구를 제일 앞에 추가해줘."""
            
    prompt = """입력된 이미지에서 제무상태표랑 손익계산서의 해당하는 정보를 전부 정리해줘.
                세부 항목도 전부 정확한 값으로 모두 정리해주고 전기 정보와 당기 정보가 있을텐데 정보를 구분해서 정리해줘.
                빠지는 정보가 있으면 안돼.
                이미지에 날짜 정보가 있으면 날짜 정보도 정리해줘.
                이미지에 도장이나 낙인이 있으면 있다고 알려줘.
                이렇게 모든 정보가 다 정리되어야해.
            """

    api_key = 'sk-proj-KvJ1AX8zCUYXlEL7Q0fmT3BlbkFJghD5VpM4HRcyi0f8TBCQ'
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]
        }
    ]
    payload = {
        "model": "gpt-4o",
        "messages": messages,
        "temperature" : 0.0
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']

financialstatements_json_format = {
            "손익계산서":{
                "매출액":0,
                "매출원가":0,
                "매출총이익":0,
                "판매비와관리비":0,
                "영업손실":0,
                "영업이익":0,
                "영업외수익":0,
                "영업외비용":0,
                "법인세차감전손실":0,
                "법인세차감전이익":0,
                "법인세등":0,
                "당기순손실":0,
                "당기순이익":0,
            },
            "재무상태표":{
                "유동자산":0,
                "비유동자산":0,
                "자산총계":0,
                "유동부채":0,
                "비유동부채":0,
                "부채총계":0,
                "자본금":0,
                "자본잉여금":0,
                "자본조정":0,
                "기타포괄손익누계액":0,
                "자본총계":0,
              "이익잉여금":0,
                "미처리결손금":0,
                "결손금":0,
            },
            "기준일":"",
            "연결유무":"",
            "날인유무":"",            
}
prompt_financialstatements ="재무상태표와 손익계산서 pdf를 OCR를 통해서 페이지 단위로 텍스트 정보를 추출한거야. \
        입력값을 분석해서 입력한 json 형태의 값을 채워서 하나의 재무상태표와 하나의 손익계산서만 있는 json 형태로 출력해. \
        문서에 당기랑 전기가 있을텐데 모든 값은 당기에 해당하는 값으로 채워.\
        만약에 당기 정보 안에서도 누적금액이랑 3개월치 금액이 따로 있다면, 당기 정보 안에서 누적금액에 해당하는 내용으로 채워. \
        결손금과 미처리 결손금, 이익잉여금은 모두 다 다른 항목이야. 정보가 없을 수 있지만 있는 정보는 따로 추출해.\
        자본금은 하위 항목과 상위 항목이 같은 자본금이라는 명칭을 쓸텐데 추출할때는 상위 항목의 자본금을 추출해.\
        수 데이터는 정확한 값을 추출해.\
        기준일은 문서에 2024년 6월 30일 기준 이렇게 있으면 2024/06/30 이런 형태로 바꿔서 넣어.\
        영업손실이나 영업이익은 둘 중에 하나만 문서에 있어 없는 항목은 그냥 0으로 두면 돼. 법인세차감전손실과 법인세차감전이익, 당기순손실과 당기순이익도 마찬가지야. \
        날인유무는 확인 이나 미확인 둘중에 하나만 입력해. \
        연결 유무는 '연결' , '별도' , '확인필요' 중에 하나를 적어.\
        '연결' 이나 '및 종속회사' 이나 'consolidated'라는 단어가 있으면 '연결' 이라고 적어.\
        이 모두에 해당하지 않으면 '별도' 라고 적어.\
        '별도'라는 단어가 있으면 '별도' 라고 적어.\
        문서에 '종속기업투자주식' 이 있으면 '확인필요'라 적어.    \
        정확히 다음의 json 형태로 출력해 key는 반드시 json 형태로 출력해고 value만 너가 채워야해 \
        출력 json 형태 : \n" + str(financialstatements_json_format)

def text_to_json_chatgpt(user_input, prompt):
    client = OpenAI(api_key = 'sk-proj-KvJ1AX8zCUYXlEL7Q0fmT3BlbkFJghD5VpM4HRcyi0f8TBCQ')
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=0.0
    )
    output = completion.choices[0].message.content
    return output

import json
def validate_json_format(data):
    required_keys = {'손익계산서', '재무상태표', '기준일', '연결유무', '날인유무'}
    손익계산서_keys = {'매출액', '매출원가', '매출총이익', '판매비와관리비', '영업손실', '영업이익', 
                      '영업외수익', '영업외비용', '법인세차감전손실', '법인세차감전이익', '법인세등', 
                      '당기순손실', '당기순이익'}
    재무상태표_keys = {'유동자산', '비유동자산', '자산총계', '유동부채', '비유동부채', '부채총계', 
                      '자본금', '자본잉여금', '자본조정', '기타포괄손익누계액', '자본총계', '이익잉여금', '결손금', '미처리결손금'}

    if not (isinstance(data, dict) and required_keys.issubset(data.keys())):
        return False

    if not (손익계산서_keys.issubset(data['손익계산서'].keys()) and 재무상태표_keys.issubset(data['재무상태표'].keys())):
        return False

    return True

def compare_multiple_jsons_for_excel_exist_files(json_list_yes_stamp, json_list):
    
    for json_data in json_list:
        if not validate_json_format(json_data):
            raise ValueError("JSON 형식이 맞지 않습니다. 올바른 양식을 사용하세요.")
    
    result = {}

    for section in ['손익계산서', '재무상태표']:
        result[section] = {}
        keys = json_list[0][section].keys()  # 첫 번째 JSON의 키를 기준으로
        for key in keys:
            # 모든 JSON에서 해당 키의 값이 같은지 확인
            values = [json_data[section].get(key) for json_data in json_list]
            is_same = all(value == values[0] for value in values)
            result[section][key] = {
                "값": values[0],
                "검토": 1 if is_same else 0
            }
    
    for key in ['기준일', '연결유무']:
        values = [json_data.get(key) for json_data in json_list]
        is_same = all(value == values[0] for value in values)
        result[key] = {
            "값": values[0],
            "검토": 1 if is_same else 0
        }
        
    for key in ['날인유무']:
        values = [json_data.get(key) for json_data in json_list_yes_stamp]
        is_same = all(value == values[0] for value in values)
        result[key] = {
            "값": values[0],
            "검토": 1 if is_same else 0
        }

    return result

def compare_multiple_jsons_for_excel_not_exist_files(json_list_yes_stamp, json_list, pdf_type):
    
    for json_data in json_list:
        if not validate_json_format(json_data):
            raise ValueError("JSON 형식이 맞지 않습니다. 올바른 양식을 사용하세요.")

    result = {}
    
    if pdf_type == "ocr":
        base_json = json_list[0]
        for section, items in base_json.items():
            if isinstance(items, dict):
                result[section] = {key: {"값": value, "검토": 1} for key, value in items.items()}
            else:
                result[section] = {"값": items, "검토": 1}
        return result

    for section in ['손익계산서', '재무상태표']:
        result[section] = {}
        keys = json_list[0][section].keys()
        for key in keys:
            values = [json_data[section].get(key) for json_data in json_list]
            is_same = all(value == values[0] for value in values)
            result[section][key] = {
                "값": values[0],
                "검토": 1 if is_same else 0
            }
    
    for key in ['기준일']:
        values = [json_data.get(key) for json_data in json_list]
        is_same = all(value == values[0] for value in values)
        result[key] = {
            "값": values[0],
            "검토": 1 if is_same else 0
        }
        
    for key in ['날인유무','연결유무']:
        values = [json_data.get(key) for json_data in json_list_yes_stamp]
        is_same = all(value == values[0] for value in values)
        result[key] = {
            "값": values[0],
            "검토": 1 if is_same else 0
        }

    return result

import re
def chatgpt_output_to_json_form(chatgpt_output):
    match = re.search(r'\{.*\}', chatgpt_output, re.DOTALL)
    json_output = match.group(0)
    json_output = json.loads(json_output)
    return json_output

def excel_pdf_to_json(excel_extracted_text, ocr_extracted_text, pdf_or_ocr_extracted_text, pdf_type):
    excel_output1 = chatgpt_output_to_json_form(text_to_json_chatgpt(excel_extracted_text,prompt_financialstatements))
    excel_output2 = chatgpt_output_to_json_form(text_to_json_chatgpt(excel_extracted_text,prompt_financialstatements))
    ocr_output1 = chatgpt_output_to_json_form(text_to_json_chatgpt(ocr_extracted_text,prompt_financialstatements))
    ocr_output2 = chatgpt_output_to_json_form(text_to_json_chatgpt(ocr_extracted_text,prompt_financialstatements))
    # pdf_or_ocr_output1 = chatgpt_output_to_json_form(text_to_json_chatgpt(pdf_or_ocr_extracted_text,prompt_financialstatements))
    # pdf_or_ocr_output2 = chatgpt_output_to_json_form(text_to_json_chatgpt(pdf_or_ocr_extracted_text,prompt_financialstatements))
    json_list_yes_stamp = [ocr_output1,ocr_output2]
    # json_list = [excel_output1, excel_output2, ocr_output1, ocr_output2]
    json_list = [excel_output1, excel_output2, ocr_output1, ocr_output2]
    final_json_output = compare_multiple_jsons_for_excel_exist_files(json_list_yes_stamp, json_list)
    return final_json_output
   
def only_pdf_to_json(ocr_extracted_text, pdf_or_ocr_extracted_text, pdf_type):
    ocr_output1 = chatgpt_output_to_json_form(text_to_json_chatgpt(ocr_extracted_text,prompt_financialstatements))
    ocr_output2 = chatgpt_output_to_json_form(text_to_json_chatgpt(ocr_extracted_text,prompt_financialstatements))
    pdf_or_ocr_output1 = chatgpt_output_to_json_form(text_to_json_chatgpt(pdf_or_ocr_extracted_text,prompt_financialstatements))
    pdf_or_ocr_output2 = chatgpt_output_to_json_form(text_to_json_chatgpt(pdf_or_ocr_extracted_text,prompt_financialstatements))
    json_list_yes_stamp = [ocr_output1, ocr_output2]
    # json_list = [pdf_or_ocr_output1, pdf_or_ocr_output2, ocr_output1, ocr_output2]
    json_list = [pdf_or_ocr_output1, pdf_or_ocr_output2, ocr_output1, ocr_output2]
    final_json_output = compare_multiple_jsons_for_excel_not_exist_files(json_list_yes_stamp, json_list, pdf_type)
    return final_json_output
  
import gspread
from gspread_formatting import CellFormat, Color, TextFormat, format_cell_ranges

gc = gspread.service_account(filename=r'C:\Users\KV_dev\Desktop\K_adventure\kakao\zerobot-425701-15f85b16185c.json')
spreadsheet = gc.open_by_key("1T0Hh-8cttX7KXAPGUGkDOrWyCsrI_u9zrR461dmq52k")

# 텍스트 포맷 정의 (검정 글씨, 빨간 글씨)
black_text = CellFormat(textFormat=TextFormat(foregroundColor=Color(0, 0, 0)))
red_text = CellFormat(textFormat=TextFormat(foregroundColor=Color(1, 0, 0)))

def prepare_row_data(json_data, headers):
    row_values = []
    format_ranges = []

    for header in headers:
        # 매핑을 적용하여 JSON 데이터의 키를 실제 시트의 헤더와 맞춤
        mapped_header = header
        if header == "기타포괄누계액":
            mapped_header = "기타포괄손익누계액"
        elif header == "법인세":
            mapped_header = "법인세등"
        elif header == "일반관리비":
            mapped_header = "판매비와관리비"

        # 손익계산서와 재무상태표에서 header 또는 매핑된 값 찾기
        if mapped_header in json_data["손익계산서"]:
            value_dict = json_data["손익계산서"][mapped_header]
        elif mapped_header in json_data["재무상태표"]:
            value_dict = json_data["재무상태표"][mapped_header]
        else:
            # 기준일, 연결유무, 날인유무 같은 개별 항목 처리
            value_dict = json_data.get(header, {"값": "", "검토": 1})

        value = value_dict["값"]
        검토 = value_dict["검토"]

        # 이익 항목 계산: 이익 - 손실 방식
        if header == "영업이익":
            영업이익_검토 = json_data["손익계산서"]["영업이익"]["검토"]
            영업손실_검토 = json_data["손익계산서"].get("영업손실", {"검토": 1})["검토"]
            if 영업이익_검토 == 0 or 영업손실_검토 == 0:
                value = 0
                검토 = 0
            else:
                value = json_data["손익계산서"]["영업이익"]["값"] - json_data["손익계산서"].get("영업손실", {"값": 0})["값"]

        elif header == "당기순이익":
            당기순이익_검토 = json_data["손익계산서"]["당기순이익"]["검토"]
            당기순손실_검토 = json_data["손익계산서"].get("당기순손실", {"검토": 1})["검토"]
            if 당기순이익_검토 == 0 or 당기순손실_검토 == 0:
                value = 0
                검토 = 0
            else:
                value = json_data["손익계산서"]["당기순이익"]["값"] - json_data["손익계산서"].get("당기순손실", {"값": 0})["값"]

        elif header == "법인세차감전이익":
            법인세차감전이익_검토 = json_data["손익계산서"]["법인세차감전이익"]["검토"]
            법인세차감전손실_검토 = json_data["손익계산서"].get("법인세차감전손실", {"검토": 1})["검토"]
            if 법인세차감전이익_검토 == 0 or 법인세차감전손실_검토 == 0:
                value = 0
                검토 = 0
            else:
                value = json_data["손익계산서"]["법인세차감전이익"]["값"] - json_data["손익계산서"].get("법인세차감전손실", {"값": 0})["값"]

        # 포맷 설정: 검토 값에 따라 텍스트 색상 결정
        cell_format = black_text if 검토 == 1 else red_text
        row_values.append(value)
        format_ranges.append(cell_format)

    return row_values, format_ranges

def update_sheet_with_json(json_data, sheet_name, company_name):
    worksheet = spreadsheet.worksheet(sheet_name)
    headers = worksheet.row_values(1)  # 첫 번째 행에 있는 헤더 가져오기
    row_values, format_ranges = prepare_row_data(json_data, headers[1:])
    
    # 회사 이름 추가
    row_values = [company_name] + row_values
    worksheet.append_row(row_values)

    # 추가된 행 번호 계산
    last_row = len(worksheet.get_all_values())

    # 포맷 적용
    for i, cell_format in enumerate(format_ranges, start=1):  # 첫 번째 데이터 열부터 시작
        cell_location = f'{chr(65 + i)}{last_row}'
        format_cell_ranges(worksheet, [(cell_location, cell_format)])

def update_etc_sheet(json_data, company_name, issues):
    worksheet = spreadsheet.worksheet("그 외")
    headers = worksheet.row_values(1)  # 첫 번째 행에 있는 헤더 가져오기
    row_values = [company_name]
    format_ranges = []

    # Add values for each header from json_data
    for header in headers[1:]:
        if header == "이슈":
            # Concatenate issues list into a single string with each issue on a new line
            issue_text = "\n".join([f"{i+1}. {issue}" for i, issue in enumerate(issues)])
            row_values.append(issue_text)
        else:
            value_dict = json_data.get(header, {"값": "", "검토": 1})
            row_values.append(value_dict["값"])

            # Set cell format based on 검토 값
            cell_format = black_text if value_dict["검토"] == 1 else red_text
            format_ranges.append(cell_format)

    # Append the data to the sheet
    worksheet.append_row(row_values)
    last_row = len(worksheet.get_all_values())

    # Apply format to cells
    for i, cell_format in enumerate(format_ranges, start=2):  # Start from the second column
        cell_location = f'{chr(64 + i)}{last_row}'  # A column onward
        format_cell_ranges(worksheet, [(cell_location, cell_format)])

def update_all_sheets(json_data, company_name, issues):
    update_sheet_with_json(json_data, "재무제표", company_name)
    update_sheet_with_json(json_data, "ERP", company_name)
    update_etc_sheet(json_data, company_name, issues)

def validate_financial_data(output_json, A):
    issues = []
    # Issue 1: 유동자산 + 비유동자산 = 자산총계
    if output_json["재무상태표"]["유동자산"]["값"] + output_json["재무상태표"]["비유동자산"]["값"] != output_json["재무상태표"]["자산총계"]["값"]:
        # for key in ["유동자산", "비유동자산", "자산총계"]:
        #     output_json["재무상태표"][key]["검토"] = 0
        issues.append("유동자산 + 비유동자산 != 자산총계")
    
    # Issue 2: 유동부채 + 비유동부채 = 부채총계
    if output_json["재무상태표"]["유동부채"]["값"] + output_json["재무상태표"]["비유동부채"]["값"] != output_json["재무상태표"]["부채총계"]["값"]:
        # for key in ["유동부채", "비유동부채", "부채총계"]:
        #     output_json["재무상태표"][key]["검토"] = 0
        issues.append("유동부채 + 비유동부채 != 부채총계")
    
    # Issue 3: 자본금 + 자본잉여금 + 자본조정 + 기타포괄손익누계액 + 이익잉여금 = 자본총계
    if (output_json["재무상태표"]["자본금"]["값"] + output_json["재무상태표"]["자본잉여금"]["값"] +
        output_json["재무상태표"]["자본조정"]["값"] + output_json["재무상태표"]["기타포괄손익누계액"]["값"] +
        output_json["재무상태표"]["이익잉여금"]["값"]) != output_json["재무상태표"]["자본총계"]["값"]:
        # for key in ["자본금", "자본잉여금", "자본조정", "기타포괄손익누계액", "이익잉여금", "자본총계"]:
        #     output_json["재무상태표"][key]["검토"] = 0
        issues.append("자본금+자본잉여금+자본조정+기타포괄손익누계액+이익잉여금 != 자본총계")
    
    # Issue 4: 매출액 - 매출원가 = 매출총이익
    if output_json["손익계산서"]["매출액"]["값"] - output_json["손익계산서"]["매출원가"]["값"] != output_json["손익계산서"]["매출총이익"]["값"]:
        # for key in ["매출액", "매출원가", "매출총이익"]:
        #     output_json["손익계산서"][key]["검토"] = 0
        issues.append("매출액 - 매출원가 != 매출총이익")
    
    # Issue 5: 영업이익과 영업손실 값 둘 다 0이 아닌 경우
    if output_json["손익계산서"]["영업이익"]["값"] != 0 and output_json["손익계산서"]["영업손실"]["값"] != 0:
        # output_json["손익계산서"]["영업이익"]["검토"] = 0
        # output_json["손익계산서"]["영업손실"]["검토"] = 0
        issues.append("영업이익과 영업손실값 둘 다 추출됨")
    
    # Issue 6: 법인세차감전이익과 법인세차감전손실 값 둘 다 0이 아닌 경우
    if output_json["손익계산서"]["법인세차감전이익"]["값"] != 0 and output_json["손익계산서"]["법인세차감전손실"]["값"] != 0:
        # output_json["손익계산서"]["법인세차감전이익"]["검토"] = 0
        # output_json["손익계산서"]["법인세차감전손실"]["검토"] = 0
        issues.append("법인세차감전이익과 법인세차감전손실값 둘 다 추출됨")
    
    # Issue 7: 당기순이익과 당기순손실 값 둘 다 0이 아닌 경우
    if output_json["손익계산서"]["당기순이익"]["값"] != 0 and output_json["손익계산서"]["당기순손실"]["값"] != 0:
        # output_json["손익계산서"]["당기순이익"]["검토"] = 0
        # output_json["손익계산서"]["당기순손실"]["검토"] = 0
        issues.append("당기순이익과 당기순손실값 둘 다 추출됨")
    
    # Issue 8: 영업손실이 0일 때, 영업이익 = 매출총이익 - 판매비와관리비
    if output_json["손익계산서"]["영업손실"]["값"] == 0:
        if output_json["손익계산서"]["영업이익"]["값"] != output_json["손익계산서"]["매출총이익"]["값"] - output_json["손익계산서"]["판매비와관리비"]["값"]:
            # for key in ["영업이익", "매출총이익", "판매비와관리비"]:
            #     output_json["손익계산서"][key]["검토"] = 0
            issues.append("영업이익 != 매출총이익-판매비와관리비")
    
    # Issue 8: 영업이익이 0일 때, -영업손실 = 매출총이익 - 판매비와관리비
    if output_json["손익계산서"]["영업이익"]["값"] == 0:
        if -output_json["손익계산서"]["영업손실"]["값"] != output_json["손익계산서"]["매출총이익"]["값"] - output_json["손익계산서"]["판매비와관리비"]["값"]:
            # for key in ["영업손실", "매출총이익", "판매비와관리비"]:
            #     output_json["손익계산서"][key]["검토"] = 0
            issues.append("-영업손실 != 매출총이익-판매비와관리비")
    
    # Issue 9: 자산총계 - 부채총계 = 자본총계
    if output_json["재무상태표"]["자산총계"]["값"] - output_json["재무상태표"]["부채총계"]["값"] != output_json["재무상태표"]["자본총계"]["값"]:
        # for key in ["자산총계", "부채총계", "자본총계"]:
        #     output_json["재무상태표"][key]["검토"] = 0
        issues.append("자산총계 - 부채총계 != 자본총계")
    
    # Issue 10: 자본금 = A
    if output_json["재무상태표"]["자본금"]["값"] != A:
        # output_json["재무상태표"]["자본금"]["검토"] = 0
        issues.append("등본의 자본금과 값이 일치하지 않음")
    
    return output_json, issues

import googleapi
dummy_json_result = {
                "손익계산서": {
                    "매출액": {"값": 0, "검토": 0},
                    "매출원가": {"값": 0, "검토": 0},
                    "매출총이익": {"값": 0, "검토": 0},
                    "판매비와관리비": {"값": 0, "검토": 0},
                    "영업손실": {"값": 0, "검토": 0},
                    "영업이익": {"값": 0, "검토": 0},
                    "영업외수익": {"값": 0, "검토": 0},
                    "영업외비용": {"값": 0, "검토": 0},
                    "법인세차감전손실": {"값": 0, "검토": 0},
                    "법인세차감전이익": {"값": 0, "검토": 0},
                    "법인세등": {"값": 0, "검토": 0},
                    "당기순손실": {"값": 0, "검토": 0},
                    "당기순이익": {"값": 0, "검토": 0},
                },
                "재무상태표": {
                    "유동자산": {"값": 0, "검토": 0},
                    "비유동자산": {"값": 0, "검토": 0},
                    "자산총계": {"값": 0, "검토": 0},
                    "유동부채": {"값": 0, "검토": 0},
                    "비유동부채": {"값": 0, "검토": 0},
                    "부채총계": {"값": 0, "검토": 0},
                    "자본금": {"값": 0, "검토": 0},
                    "자본잉여금": {"값": 0, "검토": 0},
                    "자본조정": {"값": 0, "검토": 0},
                    "기타포괄손익누계액": {"값": 0, "검토": 0},
                    "자본총계": {"값": 0, "검토": 0},
                    "이익잉여금":{"값": 0, "검토": 0},
                    "결손금":{"값": 0, "검토": 0},
                    "미처리결손금":{"값": 0, "검토": 0},
                },
                "기준일": {"값": "error", "검토": 0},
                "연결유무": {"값": "error", "검토": 0},
                "날인유무": {"값": "error", "검토": 0}
            }

def process_files(normalized_company_name_list, files_financialstatements):
    print("normalized_company_name_list : " + str(normalized_company_name_list))
    company_files = {}
    for file_metadata in files_financialstatements:
        company_name = normalize_text(file_metadata['name'].split('_')[0])
        if company_name not in normalized_company_name_list:
            continue
        if company_name not in company_files:
            company_files[company_name] = {'excel': None, 'pdf': None}
        file_type = file_metadata['mimeType']
        if file_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel']:
            # try:
            file_data = download_file_data(file_metadata['id'])
            excel_extracted_text = process_excel(file_data)
            company_files[company_name]['excel'] = excel_extracted_text
            # except:
            #     print(company_name + "'s excel_extracted_text error")
        elif file_type == 'application/pdf':
            try:
                file_data = download_file_data(file_metadata['id'])
                file_data.seek(0)
                pdf_text = process_pdf(file_data)
                if len(pdf_text) > 500:
                    pdf_type = "pdf"
                    pdf_or_ocr_extracted_text = pdf_text
                else:
                    pdf_type = "ocr"
                    file_data.seek(0)
                    image_list = pdf_to_images_base64(file_data)
                    pdf_or_ocr_extracted_text = ""
                    for i,img_data in enumerate(image_list):
                        pdf_or_ocr_extracted_text = pdf_or_ocr_extracted_text + str(i+1)+" 번째 페이지\n" + send_single_image(img_data) + "\n"   
                file_data.seek(0)
                image_list = pdf_to_images_base64(file_data)
                ocr_extracted_text = ""
                for i,img_data in enumerate(image_list):
                    ocr_extracted_text = ocr_extracted_text + str(i+1)+" 번째 페이지\n" + send_single_image(img_data) + "\n"
                company_files[company_name]['pdf'] = (ocr_extracted_text, pdf_or_ocr_extracted_text, pdf_type)
            except:
                print(company_name + "'s pdf_extracted_text error")
    
    for company_name, files in company_files.items():
        if company_files[company_name]['excel'] and company_files[company_name]['pdf']:
            try:
                excel_extracted_text = company_files[company_name]['excel']
                ocr_extracted_text = company_files[company_name]['pdf'][0]
                pdf_or_ocr_extracted_text = company_files[company_name]['pdf'][1]
                pdf_type = company_files[company_name]['pdf'][2]
                output_json = excel_pdf_to_json(excel_extracted_text, ocr_extracted_text, pdf_or_ocr_extracted_text, pdf_type)
            except:
                output_json = dummy_json_result
                print(company_name + "'s excel_pdf_to_json error")
        elif company_files[company_name]['pdf']:
            try:
                ocr_extracted_text = company_files[company_name]['pdf'][0]
                pdf_or_ocr_extracted_text = company_files[company_name]['pdf'][1]
                pdf_type = company_files[company_name]['pdf'][2]
                output_json = only_pdf_to_json(ocr_extracted_text, pdf_or_ocr_extracted_text, pdf_type)
            except:
                output_json = dummy_json_result
                print(company_name + "'s only_pdf_to_json error")
        else:  
            output_json = dummy_json_result
            print("pdf 파일이 없습니다.")
        try:
            capital = googleapi.get_capital_from_company_name(company_name)
            output_json, issues = validate_financial_data(output_json, capital)
        except:
            capital = 0
            output_json, issues = validate_financial_data(output_json, capital)
            print(company_name + "'s googleapi.get_capital_from_company_name error")
            issues.append("자본금을 불러오지 못함")
        update_all_sheets(output_json, company_name, issues)
                       
# financialstatements_company_name_list = ["21세기전파상","가지랩","겟차","고이장례연구소","그렙","하이로컬","Market Stadium", "M3TA", "KASA NETWORK", "Intelon", "홈즈컴퍼니", "홀릭스팩토리", "하이로컬","플랭","드리모"]


# financialstatements_company_name_list = ["브룩허스트거라지"] ## 기업명
# financialstatements_folder_id = '1DSlMhSMAskZGtS1t4eNeFHlAeW7AsaLy' ## 재무제표 폴더

# normalized_company_name_list = [normalize_text(name) for name in financialstatements_company_name_list]
# files_financialstatements = list_files_in_folder(financialstatements_folder_id)
# process_files(normalized_company_name_list, files_financialstatements)

######################################################################       OCR2       ########################################################################
import json

def get_real_items():
    SHEET_ID = "1WACKlZYIoW7-aaLrzbeA3C4s9haTPnwQtr7LDi7PMSI"
    SHEET_RANGES = ["재무상태표", "손익계산서"]  # 추가 시트 이름 포함
    EXCLUSION_SHEET = "제외항목"
    sheets_service = build('sheets', 'v4', credentials=creds)
    sheet = sheets_service.spreadsheets()
    actual_items = []
    for SHEET_RANGE in SHEET_RANGES:
        result = sheet.values().get(spreadsheetId=SHEET_ID, range=SHEET_RANGE).execute()
        values = result.get('values', [])
        if not values:
            continue
        data_columns = [row[4:] for row in values if len(row) > 4]
        actual_items.extend([
            re.sub(r"[^가-힣a-zA-Z()_]", "", item)  # 숫자와 특수기호 제거, ( ) _ 는 남김
            for sublist in data_columns
            for item in sublist if item
        ])
    exclusion_result = sheet.values().get(spreadsheetId=SHEET_ID, range=EXCLUSION_SHEET).execute()
    exclusion_values = exclusion_result.get('values', [])
    exclusion_items = [
        re.sub(r"[^가-힣a-zA-Z()_]", "", item)  # 숫자와 특수기호 제거, ( ) _ 는 남김
        for sublist in exclusion_values
        for item in sublist if item
    ]
    return actual_items, exclusion_items


from typing import Optional
from pydantic import BaseModel

class Output(BaseModel):
    items: list[str]

from pydantic import BaseModel
def extract_item_from_txt_chatgpt(user_input):

    prompt = """
    재무상태표와 손익계산서 pdf를 OCR를 통해서 페이지 단위로 텍스트 정보를 추출한거야. \
    대부분의 텍스트는 항목명에 해당할텐데 전체 문서에서 항목명에 해당하는 모든걸 추출해.\
    감가상각누계액은 여러개가 있을 수 있어. \
    바로 위에 있는 항목의 감가상각누계액이라는걸 구분해서 추출해.\
    예를들어 바로 위 항목에 비품이 있으면 비품_감가상각누계액 이렇게 추출해.\
    항목명에 해당하는 값 또는 금액이 없어도 항목명을 추출해.\
    특수기호는 없애고 추출해.\
    _는 남겨주고, 띄어쓰기 없이 추출해, json 형태로 출력해.
    """ 

    client = OpenAI(api_key = 'sk-proj-KvJ1AX8zCUYXlEL7Q0fmT3BlbkFJghD5VpM4HRcyi0f8TBCQ')
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ],
        response_format=Output,
    )

    # GPT 응답에서 결과를 추출
    output = completion.choices[0].message.parsed
    return [
        re.sub(r"[^가-힣a-zA-Z0-9_]", "", re.sub(r"^[\u2160-\u217F]+", "", item)).strip()
        for item in output.items
    ]

prompt_ocr2 ="재무상태표와 손익계산서 pdf를 OCR를 통해서 페이지 단위로 텍스트 정보를 추출한거야. \
        입력값을 분석해서 입력한 json 형태의 값을 채워서 하나의 재무상태표와 하나의 손익계산서만 있는 json 형태로 출력해. \
        문서에 당기랑 전기가 있을텐데 모든 값은 당기에 해당하는 값으로 채워.\
        만약에 당기 정보 안에서도 누적금액이랑 3개월치 금액이 따로 있다면, 당기 정보 안에서 누적금액에 해당하는 내용으로 채워. \
        수 데이터는 정확한 값을 추출해.\
        정확히 다음의 json 형태로 출력해 key는 반드시 json 형태로 출력해고 value만 너가 채워야해 \
        출력 json 형태 : \n"

import openai
def text_to_json_chatgpt_ocr2(user_input, prompt):
    
    client = OpenAI(api_key = 'sk-proj-KvJ1AX8zCUYXlEL7Q0fmT3BlbkFJghD5VpM4HRcyi0f8TBCQ')
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=0.0
    )

    # GPT 응답에서 결과를 추출
    output = completion.choices[0].message.content
    return output
    
def process_json_list(json_list):
    keys = json_list[0].keys()
    result = {}
    for key in keys:
        values = [json_data.get(key) for json_data in json_list]
        is_same = all(value == values[0] for value in values)
        result[key] = {
            "값": values[0],
            "검토": 1 if is_same else 0
        }
    return result


def excel_pdf_to_json_ocr2(excel_extracted_text, ocr_extracted_text, items):
    result_dict = {item.replace(" ", ""): 0 for item in items}
    formatted_json = json.dumps(result_dict, ensure_ascii=False, indent=4)
    excel_output1 = chatgpt_output_to_json_form(text_to_json_chatgpt_ocr2(excel_extracted_text,prompt_ocr2+str(formatted_json)))
    excel_output2 = chatgpt_output_to_json_form(text_to_json_chatgpt_ocr2(excel_extracted_text,prompt_ocr2+str(formatted_json)))
    ocr_output1 = chatgpt_output_to_json_form(text_to_json_chatgpt_ocr2(ocr_extracted_text,prompt_ocr2+str(formatted_json)))
    ocr_output2 = chatgpt_output_to_json_form(text_to_json_chatgpt_ocr2(ocr_extracted_text,prompt_ocr2+str(formatted_json)))
    json_list = [excel_output1, excel_output2, ocr_output1, ocr_output2]
    final_json_output = process_json_list(json_list)
    return final_json_output

def only_pdf_to_json_ocr2(ocr_extracted_text, pdf_or_ocr_extracted_text, items):
    result_dict = {item.replace(" ", ""): 0 for item in items}
    formatted_json = json.dumps(result_dict, ensure_ascii=False, indent=4)
    ocr_output1 = chatgpt_output_to_json_form(text_to_json_chatgpt_ocr2(ocr_extracted_text,prompt_ocr2+str(formatted_json)))
    ocr_output2 = chatgpt_output_to_json_form(text_to_json_chatgpt_ocr2(ocr_extracted_text,prompt_ocr2+str(formatted_json)))
    pdf_or_ocr_output1 = chatgpt_output_to_json_form(text_to_json_chatgpt_ocr2(pdf_or_ocr_extracted_text,prompt_ocr2+str(formatted_json)))
    pdf_or_ocr_output2 = chatgpt_output_to_json_form(text_to_json_chatgpt_ocr2(pdf_or_ocr_extracted_text,prompt_ocr2+str(formatted_json)))
    json_list = [pdf_or_ocr_output1, pdf_or_ocr_output2, ocr_output1, ocr_output2]
    final_json_output = process_json_list(json_list)
    return final_json_output

from gspread_formatting import format_cell_range, CellFormat, TextFormat, Color

def write_json_to_sheet(json_data, company_name):
    # Google Sheets 인증 및 스프레드시트 열기
    gc = gspread.service_account(filename=r'C:\Users\KV_dev\Desktop\K_adventure\kakao\zerobot-425701-15f85b16185c.json')
    spreadsheet = gc.open_by_key("1sKbhatzVFQKABl2dh1xaRZwbzFYARiPJLZ2MYMtVG2Y")
    worksheet = spreadsheet.sheet1

    # 기존 데이터 아래 한 줄 띄우기
    existing_data = worksheet.get_all_values()
    next_row = len(existing_data) + 2  # Leave one blank row

    keys = list(json_data.keys())
    values = [json_data[key]["값"] for key in keys]
    checks = [json_data[key]["검토"] for key in keys]

    # 헤더 작성
    header_row = ["회사명"] + keys
    worksheet.update(f"A{next_row}", [header_row])
    next_row += 1

    # 회사명과 값 작성
    data_row = [company_name] + values
    worksheet.update(f"A{next_row}", [data_row])

    # 검토 값에 따라 글자색 설정
    for col_index, check in enumerate(checks, start=2):
        # 열과 행 범위 계산
        column_letter = gspread.utils.rowcol_to_a1(next_row, col_index).split(str(next_row))[0]
        cell_range = f"{column_letter}{next_row}"

        # 색상 설정 (검정색 또는 빨간색)
        text_color = Color(0, 0, 0) if check == 1 else Color(1, 0, 0)
        cell_format = CellFormat(
            textFormat=TextFormat(
                foregroundColor=text_color
            )
        )
        # 색상 적용
        format_cell_range(worksheet, cell_range, cell_format)

def ocr2_phase1(normalized_company_name_list, files_financialstatements):
    company_files = {}
    for file_metadata in files_financialstatements:
        company_name = normalize_text(file_metadata['name'].split('_')[0])
        if company_name not in normalized_company_name_list:
            continue
        if company_name not in company_files:
            company_files[company_name] = {'excel': None, 'pdf': None}
        file_type = file_metadata['mimeType']
        if file_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel']:
            try:
                file_data = download_file_data(file_metadata['id'])
                excel_extracted_text = process_excel(file_data)
                company_files[company_name]['excel'] = excel_extracted_text
            except:
                print(company_name + "'s excel_extracted_text error")
        elif file_type == 'application/pdf':
            try:
                file_data = download_file_data(file_metadata['id'])
                file_data.seek(0)
                pdf_text = process_pdf(file_data)
                if len(pdf_text) > 500:
                    pdf_type = "pdf"
                    pdf_or_ocr_extracted_text = pdf_text
                else:
                    pdf_type = "ocr"
                    file_data.seek(0)
                    image_list = pdf_to_images_base64(file_data)
                    pdf_or_ocr_extracted_text = ""
                    for i,img_data in enumerate(image_list):
                        pdf_or_ocr_extracted_text = pdf_or_ocr_extracted_text + str(i+1)+" 번째 페이지\n" + send_single_image(img_data) + "\n"   
                file_data.seek(0)
                image_list = pdf_to_images_base64(file_data)
                ocr_extracted_text = ""
                for i,img_data in enumerate(image_list):
                    ocr_extracted_text = ocr_extracted_text + str(i+1)+" 번째 페이지\n" + send_single_image(img_data) + "\n"
                company_files[company_name]['pdf'] = (ocr_extracted_text, pdf_or_ocr_extracted_text, pdf_type)
            except:
                print(company_name + "'s pdf_extracted_text error")

    phase1_output = {}
    for company_name, files in company_files.items():
        if company_files[company_name]['excel'] and company_files[company_name]['pdf']:
            try:
                excel_extracted_text = company_files[company_name]['excel']
                # ocr_extracted_text = company_files[company_name]['pdf'][0]
                pdf_or_ocr_extracted_text = company_files[company_name]['pdf'][1]
                actual_items, exclusion_items = get_real_items()
                items = extract_item_from_txt_chatgpt(pdf_or_ocr_extracted_text)
                updated_items = [item for item in items if item not in exclusion_items]
                extra_items = [item for item in updated_items if item not in actual_items]
                output_json = excel_pdf_to_json_ocr2(excel_extracted_text, pdf_or_ocr_extracted_text, updated_items)
                write_json_to_sheet(output_json, company_name)
            except:
                output_json = {"error":{"값":0,"검토": 0}}
                extra_items = ["해당기업오류남"]
                write_json_to_sheet(output_json, company_name)
                print(company_name + "'s excel_pdf_to_json error")
            phase1_output[company_name] = extra_items
        elif company_files[company_name]['pdf']:
            # try:
            ocr_extracted_text = company_files[company_name]['pdf'][0]
            pdf_or_ocr_extracted_text = company_files[company_name]['pdf'][1]
            items = extract_item_from_txt_chatgpt(ocr_extracted_text)
            actual_items, exclusion_items = get_real_items()
            items = extract_item_from_txt_chatgpt(ocr_extracted_text)
            updated_items = [item for item in items if item not in exclusion_items]
            extra_items = [item for item in updated_items if item not in actual_items]
            output_json = only_pdf_to_json_ocr2(ocr_extracted_text, pdf_or_ocr_extracted_text, updated_items)
            write_json_to_sheet(output_json, company_name)
            # except:
            #     output_json = {"error":{"값":0,"검토": 0}}
            #     extra_items = ["해당기업오류남"]
            #     write_json_to_sheet(output_json, company_name)
            #     print(company_name + "'s only_pdf_to_json error")
            phase1_output[company_name] = extra_items
        else:  
            output_json = dummy_json_result
            print("pdf 파일이 없습니다.")
    return phase1_output

def get_info_equation_sheet():
    # Google Sheets 연결
    gc = gspread.service_account(filename=r'C:\Users\KV_dev\Desktop\K_adventure\kakao\zerobot-425701-15f85b16185c.json')
    spreadsheet_id = '10slxMrxBKZcZc6ibA4H5M1D3y_XJhdpUPfgYHOxiMWE'
    sheet = gc.open_by_key(spreadsheet_id).sheet1

    # 헤더와 데이터 가져오기
    headers = sheet.row_values(1)  # 첫 번째 행 (헤더)
    data = sheet.get_all_records(expected_headers=headers)  # 데이터 읽기

    # 결과 저장 변수
    result_item = {}
    equation = ""
    using_item = set()

    # 데이터 처리 (결과 값이 있는 줄만 필터링)
    for row in data:
        if row.get("결과"):  # "결과" 열에 값이 있는 경우만 처리
            result = row.get("결과")
            result = result.replace(" ", "")
            formula = row.get("수식")
            # 3번째 열 이후 모든 열 가져오기
            items = [value.replace(" ", "") for key, value in row.items() if key not in ("결과", "수식") and value]

            # 업데이트
            result_item[result] = 0
            equation += f"{result}={formula}\\\n"
            using_item.update(items)

    # 정렬된 using_item 리스트
    using_item = sorted(using_item)
    return result_item, equation.strip(), using_item

def filtering_jsonlist(js, using_item):
    result = []
    missing_items = []  # 누락된 항목들을 모을 리스트
    for item in js:
        filtered_item = {key: item[key] for key in item if key == '회사명' or (key in using_item and key in item)}
        missing = [key for key in using_item if key not in item]
        if missing:
            missing_items.append({'회사명': item.get('회사명', 'Unknown'), '누락 항목': missing})
            continue  # 해당 아이템 건너뜀
        result.append(filtered_item)
    if missing_items:
        print("누락된 항목이 있는 데이터:", missing_items)
        return 0, missing_items
    return 1, result

def merge_and_deduplicate(data):
    all_missing_items = set()  # 중복 제거를 위해 set 사용
    for item in data:
        all_missing_items.update(item.get('누락 항목', []))  # '누락 항목' 병합
    return list(all_missing_items)  # 최종적으로 리스트로 반환

def chatgpt_output_to_json_form(chatgpt_output):
    match = re.search(r'\{.*\}', chatgpt_output, re.DOTALL)
    json_output = match.group(0)
    json_output = json.loads(json_output)
    return json_output

def ocr2_phase2_gpt(result_json, equation_prompt, js):
    prompt = equation_prompt + " 는 수식에 대한 설명이야. 이 수식과 입력값을 분석해서 최종 결과로 " + str(result_json) + "이 포멧으로 출력해. 반드시 json 포멧이여야 해. 수식을 정확하게 계산해서 값을 구해."

    client = OpenAI(api_key = 'sk-proj-KvJ1AX8zCUYXlEL7Q0fmT3BlbkFJghD5VpM4HRcyi0f8TBCQ')
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": str(js)}
        ],
    )

    # GPT 응답에서 결과를 추출
    output = completion.choices[0].message.content
    return chatgpt_output_to_json_form(output)

def write_to_google_sheet(data):
    # Google Sheets 연결
    gc = gspread.service_account(filename=r'C:\Users\KV_dev\Desktop\K_adventure\kakao\zerobot-425701-15f85b16185c.json')
    sheet = gc.open_by_key("1_jeDPUEAIhmUqwKEzGliuojkJ2UqRe8JvZCd9C2I4U8").sheet1

    # 마지막 행 찾기
    last_row = len(sheet.get_all_values())  # 현재 데이터가 있는 마지막 행 번호
    row_number = last_row + 2  # 한 줄 띄우고 다음 줄부터 시작

    for item in data:
        # Key (헤더) 작성
        sheet.insert_row(list(item.keys()), row_number)
        row_number += 1

        # Value (데이터) 작성
        sheet.insert_row(list(item.values()), row_number)
        row_number += 1

        # 빈 줄 추가
        row_number += 1