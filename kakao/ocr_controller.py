from ocr_google_drive import get_authorized_service, get_folder_id_by_name, get_all_company_names, extract_prefix_from_filename, list_files_in_folder
from googleapiclient.errors import HttpError
import unicodedata


def normalize_string(text):
    """한글 문자열을 NFC로 정규화하고 공백 제거"""
    return unicodedata.normalize('NFC', text.replace(" ", "").strip())

def compare_name(total_names, comparing_names):
    """
    두 리스트를 비교하여 property_registry_prefixes 내에서 total_right_company_names와 일치하는 항목과
    일치하지 않는 항목을 반환하는 함수

    :param total_names: 기준이 되는 이름 리스트
    :param comparing_names: 비교 대상 이름 리스트
    :return: existing_names (일치하는 이름 리스트), not_found_names (일치하지 않는 이름 리스트)
    """
    # 각 리스트의 요소 내 공백 제거 및 정규화
    total_names = [normalize_string(name) for name in total_names]
    comparing_names = [normalize_string(name) for name in comparing_names]

    # 일치하는 이름 리스트 
    existing_names = [name for name in comparing_names if name in total_names]

    # 일치하지 않는 이름 리스트 
    not_found_names = [name for name in comparing_names if name not in total_names]

    return existing_names, not_found_names

def list_file_prefixes(service, folder_id):
    """
    해당 폴더 내의 모든 파일명을 조회하고, 각 파일명에서 '_' 앞까지의 정보를 추출하여 반환하는 함수
    :param service: Google Drive API 서비스 객체
    :param folder_id: 파일을 조회할 폴더 ID
    :return: 파일명에서 '_' 앞의 문자열을 리스트로 반환
    """
    files = list_files_in_folder(service, folder_id)
    file_prefixes = [extract_prefix_from_filename(file['name']) for file in files]
    return file_prefixes

def compare_controller(parent_folder_id):
    try:
        # Step 1: Authorize and get the Drive service
        service = get_authorized_service()

        # Step 2: 등기부등본, 재무제표 드라이브 아이디 정보 가지고 오기 (24년_4분기_등기부등본)
        property_registry_id = get_folder_id_by_name(service, parent_folder_id=parent_folder_id, folder_name='등기부등본')
        financial_statement_id = get_folder_id_by_name(service, parent_folder_id=parent_folder_id, folder_name='재무제표')
        shareholder_list_id = get_folder_id_by_name(service, parent_folder_id=parent_folder_id, folder_name='주주명부')

        if not property_registry_id:
            print("등기부등본 폴더를 찾을 수 없습니다.")
            return
        elif not financial_statement_id:
            print("재무제표 폴더를 찾을 수 없습니다.")
            return
            # return
        elif not shareholder_list_id:
            print("주주명부 폴더를 찾을 수 없습니다.")
            return
        
        # 아래는 순수회사명만 추출함 (별도, 연결 없이 단순 회사명만 추출하는 구간 )
        property_registry_prefixes = list_file_prefixes(service, property_registry_id)
        financial_statement_prefixes = list_file_prefixes(service, financial_statement_id)
        sharedholder_list_prefixes = list_file_prefixes(service, shareholder_list_id)

        # Step 5 : get_all_company_names() - 약식 회사명, 풀 회사명 네임리스트를 먼저 가지고 온다 
        short_company_names, full_company_names = get_all_company_names()
        total_right_company_names = short_company_names + full_company_names

        # Step 6 : total_right_company_names와 property_registry_prefixes를 비교
        # total_right_company_names와 financial_statement_prefixes를 비교
        pr_existing_names, pr_not_found_names = compare_name(total_right_company_names, property_registry_prefixes)
        fs_existing_names, fs_not_found_names = compare_name(total_right_company_names, financial_statement_prefixes)
        sh_existing_names, sh_not_found_names = compare_name(total_right_company_names, sharedholder_list_prefixes)

        return pr_existing_names, pr_not_found_names, fs_existing_names, fs_not_found_names, sh_existing_names, sh_not_found_names, \
            property_registry_id, financial_statement_id, shareholder_list_id 

    except HttpError as error:
        print(f"An error occurred: {error}")


def compare_prefix_lists(list1, list2):
    """
    두 리스트의 접두사를 비교하고, 공통된 접두사, list1에만 존재하는 접두사, list2에만 존재하는 접두사를 추출하는 함수
    :param list1: 첫 번째 리스트 (property_registry_prefixes)
    :param list2: 두 번째 리스트 (financial_statement_prefixes)
    :return: 공통된 이름 리스트, list1에만 존재하는 이름 리스트, list2에만 존재하는 이름 리스트
    """
    set1 = set(list1)
    set2 = set(list2)

    # 공통된 이름
    common_names = list(set1 & set2)

    # list1에만 존재하는 이름
    only_in_list1 = list(set1 - set2)

    # list2에만 존재하는 이름
    only_in_list2 = list(set2 - set1)

    return common_names, only_in_list1, only_in_list2

def compare_prefix_lists_three(list1, list2, list3):
    """
    세 리스트의 접두사를 비교하고, 공통된 접두사, list1에만 존재하는 접두사, 
    list2에만 존재하는 접두사, list3에만 존재하는 접두사를 추출하는 함수
    :param list1: 첫 번째 리스트 (property_registry_prefixes)
    :param list2: 두 번째 리스트 (financial_statement_prefixes)
    :param list3: 세 번째 리스트 (another_list)
    :return: 공통된 이름 리스트, list1에만 존재하는 이름 리스트, list2에만 존재하는 이름 리스트, list3에만 존재하는 이름 리스트
    """
    set1 = set(list1)
    set2 = set(list2)
    set3 = set(list3)

    # 공통된 이름 (세 리스트에 모두 존재하는 이름)
    common_names = list(set1 & set2 & set3)

    # list1에만 존재하는 이름
    only_in_list1 = list(set1 - set2 - set3)

    # list2에만 존재하는 이름
    only_in_list2 = list(set2 - set1 - set3)

    # list3에만 존재하는 이름
    only_in_list3 = list(set3 - set1 - set2)

    return common_names, only_in_list1, only_in_list2, only_in_list3

def ocr_handler():
    pass