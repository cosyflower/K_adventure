import gspread
import pandas as pd
import config
import json

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Google Drive API 설정
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = config.kakao_json_key_path
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(credentials)
drive_service = build('drive', 'v3', credentials=credentials)

def get_all_data_as_flat_list(spreadsheet_id, sheet_name='제외항목'):
    try:
        # 구글 스프레드시트 API로 스프레드시트 열기
        sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)  # '제외항목' 시트 열기

        # 시트의 모든 데이터 가져오기
        all_data = sheet.get_all_values()  # 모든 행과 열의 데이터를 가져옴

        # 2차원 리스트를 1차원 리스트로 평탄화하고 공백 제거
        flat_list = [cell for row in all_data for cell in row if cell.strip()]  # 공백 제거

        return flat_list

    except Exception as e:
        print(f"Error while fetching data as flat list: {e}")
        return []

def get_all_key_cells_per_cp(spreadsheet_id):
    try:
        # 구글 스프레드시트 API로 스프레드시트 열기
        sheet = client.open_by_key(spreadsheet_id).sheet1  # 첫 번째 시트 사용
        rows = sheet.get_all_values()  # 스프레드시트의 모든 셀 값을 리스트로 가져옴

        # 결과를 저장할 변수
        company_data_list = []  # 각 회사 데이터를 저장할 리스트
        empty_row_count = 0  # 빈 행의 연속 카운트

        i = 0
        while i < len(rows):
            row = rows[i]

            # 빈 행 처리
            if not any(row):  # 현재 행이 완전히 비어있는 경우
                empty_row_count += 1
                if empty_row_count == 5:  # 빈 행이 연속으로 두 번 나오면 종료
                    break
                i += 1
                continue
            else:
                empty_row_count = 0  # 빈 행 카운트 초기화

            # "회사명"이 있는 행 확인
            if row[0] == "회사명":
                company_name_row = rows[i + 1]  # 회사명에 해당하는 데이터 행
                keys = row[1:]  # 헤더(Key)
                values = company_name_row[1:]  # 데이터(Value)
                company_name = company_name_row[0]  # 회사명(A열)

                # Key-Value 매칭
                company_data = dict(zip(keys, values))
                company_data_list.append({company_name: company_data})

                # 다음 데이터로 넘어감 (회사명 + 데이터 두 줄을 처리했으므로 2 증가)
                i += 2
            else:
                i += 1  # 회사명이 없는 경우 다음 행으로 이동

        # company_data_list를 temp_input.json 파일로 저장
        with open('validation_ocr2_input.json', 'w', encoding='utf-8') as json_file:
            json.dump(company_data_list, json_file, ensure_ascii=False, indent=4)

        return company_data_list

    except Exception as e:
        print(f"Error: {e}")
        return None

def get_column_ranges(spreadsheet_id):
    # 대 중 소 실제항목 범위 구하는 함수
    # 이후에 실제항목만 기준으로 범위를 구할 수도 있음
    try:
        # Google Spreadsheet 열기
        sheet = client.open_by_key(spreadsheet_id)
        worksheet = sheet.worksheet('재무상태표')  # '재무상태표' 시트를 참조

        # 첫 번째 행 데이터 가져오기 (헤더)
        header_row = worksheet.row_values(1)

        # 범위 초기화
        column_ranges = {
            "No.": None,
            "대분류": None,
            "중분류": None,
            "소분류": None,
            "실제항목": None,
        }

        # 열 위치 탐색
        for idx, value in enumerate(header_row):
            if value.strip() == "No.":
                column_ranges["No."] = (idx, None)  # 시작 위치 저장
            elif value.strip() == "대분류":
                if column_ranges["No."]:
                    column_ranges["No."] = (column_ranges["No."][0], idx)  # 끝 범위 저장
                column_ranges["대분류"] = (idx, None)  # 시작 위치 저장
            elif value.strip() == "중분류":
                if column_ranges["대분류"]:
                    column_ranges["대분류"] = (column_ranges["대분류"][0], idx)  # 끝 범위 저장
                column_ranges["중분류"] = (idx, None)  # 시작 위치 저장
            elif value.strip() == "소분류":
                if column_ranges["중분류"]:
                    column_ranges["중분류"] = (column_ranges["중분류"][0], idx)  # 끝 범위 저장
                column_ranges["소분류"] = (idx, None)  # 시작 위치 저장

        # "실제항목" 시작 범위는 소분류 끝 이후
        if column_ranges["소분류"]:
            column_ranges["소분류"] = (column_ranges["소분류"][0], column_ranges["소분류"][0] + 1)  # 소분류 범위 확정
            column_ranges["실제항목"] = (column_ranges["소분류"][1], len(header_row) + 100)  # 실제항목 범위 확정

        return column_ranges

    except Exception as e:
        print(f"Error in get_column_ranges: {e}")
        return None
    
def build_json_array_with_separation(val_all_cells_pd, mapping_db_id):
    try:
        # Mapping_DB 시트 열기
        sheet = client.open_by_key(mapping_db_id)

        # '재무상태표'와 '손익계산서' 시트 가져오기
        sheets_to_process = ['재무상태표', '손익계산서']
        column_ranges = {}
        all_data_rows = {}

        # 각 시트별로 범위와 데이터를 가져옴
        for sheet_name in sheets_to_process:
            worksheet = sheet.worksheet(sheet_name)
            column_ranges[sheet_name] = get_column_ranges(mapping_db_id)
            all_data_rows[sheet_name] = worksheet.get_all_values()

        # JSON 배열 생성
        json_array = []

        for company_data in val_all_cells_pd:
            for company_name, values in company_data.items():
                # JSON 요소 초기화
                json_element = {"index": company_name, "values": {"대분류": {}, "중분류": {}, "소분류": {}, "항목 값": {}}}

                # 각 항목 확인
                for item, value in values.items():
                    value = int(value) if value.isdigit() else 0  # 값이 숫자인 경우만 처리

                    # '재무상태표'와 '손익계산서'를 모두 순회
                    for sheet_name in sheets_to_process:
                        current_ranges = column_ranges[sheet_name]
                        actual_items_start = current_ranges["실제항목"][0]
                        actual_items_end = current_ranges["실제항목"][1]
                        대분류_range = range(current_ranges["대분류"][0], current_ranges["대분류"][1])
                        중분류_range = range(current_ranges["중분류"][0], current_ranges["중분류"][1])
                        소분류_range = range(current_ranges["소분류"][0], current_ranges["소분류"][1])

                        # 해당 시트의 모든 행 데이터 순회
                        for row in all_data_rows[sheet_name][1:]:  # 첫 번째 행 제외
                            # 실제항목 확인
                            actual_items = row[actual_items_start:actual_items_end]
                            actual_items = [i.strip() for i in actual_items if i.strip()]

                            if item in actual_items:
                                # 대분류, 중분류, 소분류 범위 전체 탐색
                                대분류_list = [row[idx].strip() for idx in 대분류_range if idx < len(row)]
                                중분류_list = [row[idx].strip() for idx in 중분류_range if idx < len(row)]
                                소분류_list = [row[idx].strip() for idx in 소분류_range if idx < len(row)]

                                # 각각의 Key에 대해 값을 분리하여 저장
                                for 대분류 in 대분류_list:
                                    if 대분류:
                                        if 대분류 in json_element["values"]["대분류"]:
                                            json_element["values"]["대분류"][대분류] += value
                                        else:
                                            json_element["values"]["대분류"][대분류] = value

                                for 중분류 in 중분류_list:
                                    if 중분류:
                                        if 중분류 in json_element["values"]["중분류"]:
                                            json_element["values"]["중분류"][중분류] += value
                                        else:
                                            json_element["values"]["중분류"][중분류] = value

                                for 소분류 in 소분류_list:
                                    if 소분류:
                                        if 소분류 in json_element["values"]["소분류"]:
                                            json_element["values"]["소분류"][소분류] += value
                                        else:
                                            json_element["values"]["소분류"][소분류] = value

                                # 항목 값 추가
                                if item in json_element["values"]["항목 값"]:
                                    json_element["values"]["항목 값"][item] += value
                                else:
                                    json_element["values"]["항목 값"][item] = value

                # JSON 배열에 추가
                json_array.append(json_element)

        # 추가 처리: 존재하지 않는 소분류 항목에 대해서 값 0으로 설정
        for json_element in json_array:
            for sheet_name in sheets_to_process:
                current_ranges = column_ranges[sheet_name]
                소분류_range = range(current_ranges["소분류"][0], current_ranges["소분류"][1])
                대분류_range = range(current_ranges["대분류"][0], current_ranges["대분류"][1])
                중분류_range = range(current_ranges["중분류"][0], current_ranges["중분류"][1])

                for row in all_data_rows[sheet_name][1:]:  # 첫 번째 행 제외
                    # 소분류 가져오기
                    소분류_list = [row[idx].strip() for idx in 소분류_range if idx < len(row)]
                    대분류_list = [row[idx].strip() for idx in 대분류_range if idx < len(row)]
                    중분류_list = [row[idx].strip() for idx in 중분류_range if idx < len(row)]

                    for 소분류 in 소분류_list:
                        if 소분류 and 소분류 not in json_element["values"]["소분류"]:
                            json_element["values"]["소분류"][소분류] = 0  # 값 0으로 추가

                            # 대분류와 중분류도 추가
                            for 대분류 in 대분류_list:
                                if 대분류:
                                    json_element["values"]["대분류"].setdefault(대분류, 0)

                            for 중분류 in 중분류_list:
                                if 중분류:
                                    json_element["values"]["중분류"].setdefault(중분류, 0)

        return json_array

    except Exception as e:
        print(f"Error: {e}")
        return None    

# 테스트용 함수 (변환하는 함수)
def convert_json_to_val_all_cells(json_file_path):
    try:
        # JSON 파일 읽기
        with open(json_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # val_all_cells_pd 형태로 변환
        val_all_cells_pd = []

        for item in data:
            for company_name, details in item.items():
                val_all_cells_pd.append({company_name: details})

        return val_all_cells_pd

    except Exception as e:
        print(f"Error: {e}")
        return None


def save_json_array_to_file(json_array, file_name="result.json"):
    try:
        # JSON 배열을 파일로 저장
        with open(file_name, "w", encoding="utf-8") as json_file:
            json.dump(json_array, json_file, ensure_ascii=False, indent=4)
        # print(f"JSON 배열이 {file_name}에 저장되었습니다.")
    except Exception as e:
        print(f"Error: {e}")

def restructure_json_array(json_array):
    try:
        # 결과를 저장할 리스트
        transformed_json = []

        # JSON 원소를 순회하며 구조를 변경
        for entry in json_array:
            transformed_entry = {}

            # 회사명 가져오기
            company_name = entry.get("index", "Unknown")
            transformed_entry["회사명"] = company_name  # 첫 번째 Key 설정
            
            # values 내 "대분류", "중분류", "소분류" 병합
            values = entry.get("values", {})
            for category in ["대분류", "중분류", "소분류"]:
                category_data = values.get(category, {})
                for key, value in category_data.items():
                    if key in transformed_entry:
                        transformed_entry[key] += value  # Key가 이미 존재하면 더하기
                    else:
                        transformed_entry[key] = value  # 처음이면 초기화

            # 결과 리스트에 추가
            transformed_json.append(transformed_entry)

        return transformed_json

    except Exception as e:
        print(f"Error: {e}")
        return None
    
def check_missing_items_in_actual_items(val_pd, mapping_db_id):
    try:
        # Mapping_DB 시트 열기
        sheet = client.open_by_key(mapping_db_id)

        # 처리할 시트 목록
        sheets_to_process = ['재무상태표', '손익계산서']
        actual_items_set = set()  # '실제항목' 범위 내 모든 데이터를 담을 집합

        # 각 시트에서 '실제항목' 범위의 데이터를 가져옵니다
        for sheet_name in sheets_to_process:
            worksheet = sheet.worksheet(sheet_name)
            header_row = worksheet.row_values(1)

            # '실제항목' 열 위치 확인
            actual_items_idx = header_row.index("실제항목")  # '실제항목'이 있는 열 인덱스
            start_idx = actual_items_idx
            end_idx = actual_items_idx + 200  # 실제항목 범위는 +200열까지

            # 시트의 데이터를 가져와서 실제항목 범위 데이터를 집합에 추가
            for row in worksheet.get_all_values()[1:]:  # 첫 번째 행(헤더) 제외
                actual_items_range = row[start_idx:end_idx]
                actual_items_set.update(item.strip() for item in actual_items_range if item.strip())
            
        # 누락된 항목들을 저장할 딕셔너리
        missing_items_dict = {}

        for company_entry in val_pd:
            # 회사명(키)와 상세 데이터(값)를 추출
            for company_name, values in company_entry.items():
                # '항목 값'을 가져와서 확인 (values 전체를 comparing_keys로 사용)
                comparing_keys = list(values.keys())  
                # 누락된 항목을 임시 리스트에 저장
                missing_items = [item for item in comparing_keys if item not in actual_items_set]

                # 누락된 항목이 존재하면 missing_items_dict에 추가
                if missing_items:
                    missing_items_dict[company_name] = missing_items
                
        return missing_items_dict

    except Exception as e:
        print(f"Error: {e}")
        return {}
    
def second_check_missing_items(missing_items_dict, all_categories_set, flattened_list):
    """
    missing_items_dict의 값이 all_categories_set에 존재하는지 확인하고,
    존재하지 않는 항목들을 final_missing_items_dict로 반환하는 함수.
    
    :param missing_items_dict: {회사명: [항목1, 항목2, ...]} 형태의 딕셔너리
    :param all_categories_set: 모든 분류 값을 포함한 set
    :return: {회사명: [존재하지 않는 항목]} 형태의 딕셔너리
    """
    final_missing_items_dict = {}

    for company, items in missing_items_dict.items():
        # 공백이 아닌 항목 중 all_categories_set에 없는 항목 추출
        missing_items = [item for item in items if item and item not in all_categories_set and item not in flattened_list]
        
        # 존재하지 않는 항목이 있는 경우에만 저장
        if missing_items:
            final_missing_items_dict[company] = missing_items

    return final_missing_items_dict
    
def extract_categories(json_file):
    """
    주어진 JSON 파일에서 대분류, 중분류, 소분류 값을 추출하여 set으로 반환하는 함수.
    
    :param json_file: JSON 파일 경로
    :return: 모든 분류 값을 포함한 set
    """
    all_categories_set = set()

    # JSON 파일 읽기
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    # 데이터가 리스트 형태로 시작하는 경우 처리
    if isinstance(data, list):
        for entry in data:
            if "values" in entry and isinstance(entry["values"], dict):
                for key in ["대분류", "중분류", "소분류"]:
                    if key in entry["values"] and isinstance(entry["values"][key], dict):
                        # 대분류, 중분류, 소분류의 키들을 set에 추가
                        all_categories_set.update(entry["values"][key].keys())

    # 데이터가 딕셔너리 형태로 시작하는 경우 처리
    elif isinstance(data, dict):
        for key in ["대분류", "중분류", "소분류"]:
            if key in data.get("values", {}) and isinstance(data["values"][key], dict):
                all_categories_set.update(data["values"][key].keys())

    return all_categories_set
    
def remove_error_entries(ocr2_phase1):
    """
    Key나 Value에 'error'가 포함된 요소를 삭제합니다.
    
    Args:
        ocr2_phase1 (dict): 입력 딕셔너리
    
    Returns:
        dict: 'error'가 제거된 새로운 딕셔너리
    """
    # 'error'가 포함되지 않은 항목만 새로운 딕셔너리에 저장
    cleaned_dict = {k: v for k, v in ocr2_phase1.items() if 'error' not in str(k).lower() and 'error' not in str(v).lower()}
    return cleaned_dict