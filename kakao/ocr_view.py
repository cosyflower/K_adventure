
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import Flask, request, jsonify

import os

def start_ocr_program():
    """
    OCR 프로그램을 시작하는 함수.
    'OCR 프로그램을 시작합니다'와 주의사항을 출력하고, 예/아니오 입력을 기다립니다.
    """
    while True:
        print("OCR 프로그램을 시작합니다.")
        print("주의사항은 다음과 같습니다:\n"
                "---------------------------------------------------\n"
                "1. 파일 이름의 형식을 지켜주세요.\n"
                "2. 파일을 올바른 폴더(디렉토리)에 위치했는지 확인해주세요.\n"
                "3. 파일은 '기업명'으로 시작해야 하며 '_' 문자로 구분합니다.\n"
              )
        
        # YES / NO button activation
        user_input = input("계속 진행하시겠습니까? (예/아니오): ")

        if user_input == '예':
            print("OCR 프로그램을 시작합니다...")
            break  # 프로그램을 시작

        elif user_input == '아니오':
            # 중간에 진짜로 중단하시겠습니까? 라는 창 띄우기
            if confirm_exit():
                print("프로그램이 중단되었습니다.")
                return False # 프로그램 종료
            else:
                print("프로그램을 다시 시작합니다.\n\n\n")
                continue # 다시 처음부터 출력
        else:
            print("잘못된 입력입니다. '예' 또는 '아니오'를 입력해주세요.\n")
    return True

def show_progress_message(message="OCR 프로그램 진행중..."):
    print(message)

def show_comparison_results(common, only_in_listA, only_in_listB):
    """비교 결과를 문자열로 반환하는 함수"""
    
    result = []  # 출력 내용을 담을 리스트

    # 등기부등본의 올바른 기업명 출력
    result.append(print_separator())
    result.append(print_separator())

    result.append("등기부등본의 올바른 기업명:")
    if only_in_listA:
        result.append(' / '.join(only_in_listA))  # ' / '로 각 이름 구분하여 출력
        result.append('\n')
    else:
        result.append("*등기부등본 내 올바른 기업명이 없습니다.*")
        result.append('\n')

    # 재무제표의 올바른 기업명 출력
    result.append("주주명부의 올바른 기업명:")
    if only_in_listB:
        result.append(' / '.join(only_in_listB))  # ' / '로 각 이름 구분하여 출력
        result.append('\n')
    else:
        result.append("*주주명부 내 올바른 기업명이 없습니다.*")
        result.append('\n')

    result.append(print_separator())
    result.append(print_separator())

    # 공통된 이름 출력
    result.append('\n')
    result.append("공통된 기업명:")
    if common:
        result.append(' / '.join(common))  # ' / '로 각 이름 구분하여 출력
        result.append('\n')
    else:
        result.append("*공통된 기업명이 없습니다.*")
        result.append('\n')

    result.append('\n')
    result.append('\n')

    return ''.join(result)  # 리스트를 문자열로 변환하여 반환

# 구분선 출력 함수 수정 (문자열 반환)
def print_separator():
    return "--------------------------\n"

def show_not_found_results(not_found_A, not_found_B):
    """등기부등본과 재무제표에서 올바르지 않은 기업명 리스트를 문자열로 반환하는 함수"""
    
    result = []  # 결과를 저장할 리스트

    # 등기부등본에서 올바르지 않은 기업명 출력
    result.append("등기부등본에서 올바르지 않은 기업명 리스트:\n")
    if not_found_A:
        result.append(' / '.join(not_found_A))  # ' / ' 로 각 이름 구분하여 추가
        result.append('\n\n')
    else:
        result.append('*등기부등본 내 올바르지 않은 기업명이 없습니다.*\n\n')

    # 재무제표에서 올바르지 않은 기업명 출력
    result.append("주주명부에서 올바르지 않은 기업명 리스트:\n")
    if not_found_B:
        result.append(' / '.join(not_found_B))  # ' / ' 로 각 이름 구분하여 추가
        result.append('\n\n')
    else:
        result.append("*주주명부 내 올바르지 않은 기업명이 없습니다.*\n\n")

    return ''.join(result)  # 리스트를 문자열로 변환하여 반환

def show_found_and_not_found_results(found_A, not_found_A):
    """재무제표에서 올바른 기업명과 올바르지 않은 기업명 리스트를 문자열로 반환하는 함수"""

    result = []  # 결과를 저장할 리스트

    # 재무제표 내 올바른 기업명 출력
    result.append("재무제표 내 올바른 기업명 리스트:\n")
    if found_A:
        result.append(' | '.join(found_A))  # ' | ' 로 각 이름 구분하여 추가
        result.append('\n\n')
    else:
        result.append('*재무제표 내 올바른 기업명이 없습니다.*\n\n')

    # 재무제표 내 올바르지 않은 기업명 출력
    result.append("재무제표 내 올바르지 않은 기업명 리스트:\n")
    if not_found_A:
        result.append(' | '.join(not_found_A))  # ' | ' 로 각 이름 구분하여 추가
        result.append('\n\n')
    else:
        result.append("*재무제표 내 올바르지 않은 기업명이 없습니다.*\n\n")

    return ''.join(result)  # 리스트를 문자열로 변환하여 반환

def check_yes_or_no_init(user_id, channel_id, client, content='OCR 프로그램을 시작하시겠습니까'):
    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=f"<@{user_id}> 님, OCR 프로그램을 시작하시겠습니까?",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<@{user_id}> 님, {content}?"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "예"
                            },
                            "style": "primary",
                            "value": "yes",
                            "action_id": "yes_button_init"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "아니오"
                            },
                            "style": "danger",
                            "value": "no",
                            "action_id": "no_button_init"
                        }
                    ]
                }
            ]
        )
        return response
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

def check_yes_or_no_progress(user_id, channel_id, client, content='OCR 프로그램을 진행하시겠습니까'):
    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=f"<@{user_id}> 님, OCR 프로그램을 진행하시겠습니까?",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<@{user_id}> 님, {content}?"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "예"
                            },
                            "style": "primary",
                            "value": "yes",
                            "action_id": "yes_button_progress"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "아니오"
                            },
                            "style": "danger",
                            "value": "no",
                            "action_id": "no_button_progress"
                        }
                    ]
                }
            ]
        )
        return response
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")
