
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
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "*휴가 신청*"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "휴가 신청"
                        },
                        "style": "primary",
                        "value": "yes",
                        "action_id": "rosebot_1_id"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "*인사 총무*"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "인사 총무"
                        },
                        "style": "danger",
                        "value": "no",
                        "action_id": "rosebot_2_id"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "*문서 작성*"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "문서 작성"
                        },
                        "value": "yes",
                        "action_id": "rosebot_3_id"
                    }
                },
                # {
                #     "type": "section",
                #     "text": {
                #         "type": "plain_text",
                #         "text": "*정기예금 회전 시스템*"
                #     },
                #     "accessory": {
                #         "type": "button",
                #         "text": {
                #             "type": "plain_text",
                #             "text": "정기예금 회전 시스템"
                #         },
                #         "style": "primary",
                #         "value": "yes",
                #         "action_id": "rosebot_4_id"
                #     }
                # },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "*회수 상황판*"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "회수 상황판"
                        },
                        "style": "danger",
                        "value": "yes",
                        "action_id": "rosebot_5_id"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "*검색*"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "검색"
                        },
                        "value": "yes",
                        "action_id": "rosebot_6_id"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "*1on1*"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "1on1"
                        },
                        "style": "primary",
                        "value": "yes",
                        "action_id": "rosebot_7_id"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "*보안 시스템*"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "보안 시스템"
                        },
                        "style": "danger",
                        "value": "yes",
                        "action_id": "rosebot_8_id"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "*OCR*"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "OCR"
                        },
                        "value": "yes",
                        "action_id": "rosebot_9_id"
                    }
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