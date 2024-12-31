
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import Flask, request, jsonify

import os

def execute_rosebot_by_button(user_id, channel_id, client, content='로제봇 기능을 실행합니다.'):
    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=f"<@{user_id}> 님, {content}",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<@{user_id}> 님, {content}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "휴가 신청"
                            },
                            "style": "primary",
                            "value": "vacation_request",
                            "action_id": "vacation_request_id"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "휴가 내역 조회"
                            },
                            "style": "primary",
                            "value": "vacation_check",
                            "action_id": "vacation_check_id"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "휴가 삭제"
                            },
                            "style": "primary",
                            "value": "vacation_remove",
                            "action_id": "vacation_remove_id"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "남은 휴가 조회"
                            },
                            "style": "primary",
                            "value": "vacation_remained",
                            "action_id": "vacation_remained_id"
                        },
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "인사 총무"
                            },
                            "style": "danger",
                            "value": "no",
                            "action_id": "rosebot_2_id"
                        }
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "문서 작성"
                            },
                            "style": "danger",
                            "value": "no",
                            "action_id": "rosebot_3_id"
                        }
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": " 회수 상황판"
                            },
                            "style": "danger",
                            "value": "no",
                            "action_id": "rosebot_5_id"
                        }
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "검색"
                            },
                            "style": "danger",
                            "value": "no",
                            "action_id": "rosebot_6_id"
                        }
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "1on1"
                            },
                            "style": "danger",
                            "value": "no",
                            "action_id": "rosebot_7_id"
                        }
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "전체 사용자 권한 조회"},
                            "style": "primary",
                            "value": "view_all_users",
                            "action_id": "view_all_users"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "신규 사용자 배정"},
                            "style": "primary",
                            "value": "assign_new_user",
                            "action_id": "assign_new_user"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "내 권한 조회"},
                            "style": "primary",
                            "value": "view_self_authority",
                            "action_id": "view_self_authority"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "권한이 변경된 사용자 조회([임시]운영자 전용)"},
                            "style": "primary",
                            "value": "view_changed_users",
                            "action_id": "view_changed_users"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "권한 업데이트([임시]운영자 전용)"},
                            "style": "primary",
                            "value": "change_authority",
                            "action_id": "change_authority"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "임시 운영자 배정(운영자 전용)"},
                            "style": "primary",
                            "value": "assign_temp_admin",
                            "action_id": "assign_temp_admin"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "임시 운영자 목록 조회(운영자 전용)"},
                            "style": "primary",
                            "value": "view_temp_admins",
                            "action_id": "view_temp_admins"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "임시 운영자 회수(운영자 전용)"},
                            "style": "primary",
                            "value": "revoke_temp_admin",
                            "action_id": "revoke_temp_admin"
                        }
                    ]
                },
                # {
                #     "type": "actions",
                #     "elements": [
                #         {
                #             "type": "button",
                #             "text": {
                #                 "type": "plain_text",
                #                 "text": "OCR"
                #             },
                #             "style": "danger",
                #             "value": "OCR",
                #             "action_id": "rosebot_9_id"
                #         }
                #     ]
                # },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "OCR_1_JUDY"},
                            "style": "danger",
                            "value": "OCR_1_JUDY",
                            "action_id": "OCR_1_JUDY"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "OCR_2_BEN"},
                            "style": "danger",
                            "value": "OCR_2_BEN",
                            "action_id": "OCR_2_BEN"
                        },
                    ]
                }
            ]
        )
        return response
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

def vacation_handler_by_button(user_id, channel_id, client, content='휴가 시스템 기능을 실행합니다.'):
    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=f"<@{user_id}> 님, {content}",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<@{user_id}> 님, {content}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "*신청된 휴가 조회*"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "신청된 휴가 조회"
                        },
                        "style": "primary",
                        "value": "yes",
                        "action_id": "vacation_1_id"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "*신규 휴가 신청*"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "신규 휴가 신청"
                        },
                        "style": "danger",
                        "value": "no",
                        "action_id": "vacation_2_id"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "*남은 휴가 일수 조회*"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "남은 휴가 일수 조회"
                        },
                        "value": "yes",
                        "action_id": "vacation_3_id"
                    }
                }
            ]
        )
        return response
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")