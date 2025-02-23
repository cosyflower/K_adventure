import requests
import json

def get_all_users():
    url = "https://slack.com/api/users.list"
    headers = {
        "Authorization": f"Bearer xoxb-7070442783094-7112861109200-UImo7AdRysDFCYB69xub4Pxf"
    }
    params = {
        "limit": 100  # 한 번에 최대 200명의 사용자를 가져올 수 있습니다.
    }

    all_users = []
    while True:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        all_users.extend(data.get("members", []))
        # 다음 페이지가 있는 경우, cursor 정보를 사용하여 계속 가져옵니다.
        next_cursor = data.get("response_metadata", {}).get("next_cursor")
        if next_cursor:
            params["cursor"] = next_cursor
        else:
            break
    # 사용자 ID와 이름을 포함한 목록 생성
    users_info = [{
        "id": user["id"],
        "name": user["name"],
        "real_name": user.get("real_name", ""),
        "display_name": user["profile"].get("display_name", "")
    } for user in all_users]

    return users_info

def get_channel_users(channel_id):
    # Step 1: Get member IDs from the channel
    def get_channel_members(channel_id):
        url = "https://slack.com/api/conversations.members"
        headers = {
            "Authorization": f"Bearer xoxb-7070442783094-7112861109200-UImo7AdRysDFCYB69xub4Pxf"
        }
        params = {
            "channel": channel_id
        }

        member_ids = []
        while True:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            member_ids.extend(data.get("members", []))
            # 다음 페이지가 있는 경우, cursor 정보를 사용하여 계속 가져옵니다.
            next_cursor = data.get("response_metadata", {}).get("next_cursor")
            if next_cursor:
                params["cursor"] = next_cursor
            else:
                break
        return member_ids

    # Step 2: Get user info for each member ID
    def get_user_info(user_id):
        url = "https://slack.com/api/users.info"
        headers = {
            "Authorization": f"Bearer xoxb-7070442783094-7112861109200-UImo7AdRysDFCYB69xub4Pxf"
        }
        params = {
            "user": user_id
        }

        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        return data.get("user")


    member_ids = get_channel_members(channel_id)
    users_info = []

    for user_id in member_ids:
        user_info = get_user_info(user_id)
        if user_info:
            users_info.append({
                "id": user_info["id"],
                "name": user_info["name"],
                "real_name": user_info.get("real_name", ""),
                "display_name": user_info["profile"].get("display_name", "")
            })

    return users_info

## 새로운 사람 들어 왔을 때 이 함수 사용
def update_authority():

    management = get_channel_users("C0722D0PU22")
    executives = get_channel_users("C0722D0PU22")
    intern = get_channel_users("C0722D0PU22")
    all_user = get_all_users()

    user_info_dict = {}
    for user in management:
        user_info_dict[user['id']] = {**user, 'authority': 1}
    for user in executives:
        if user['id'] not in user_info_dict:
            user_info_dict[user['id']] = {**user, 'authority': 2}
    for user in intern:
        if user['id'] not in user_info_dict:
            user_info_dict[user['id']] = {**user, 'authority': 3}
    for user in all_user:
        if user['id'] not in user_info_dict:
            user_info_dict[user['id']] = {**user, 'authority': 4}
    with open("authority_change_list.json", 'r') as file:
        authority_change_list = json.load(file)
    for user_id, new_authority in authority_change_list.items():
        if user_id in user_info_dict:
            user_info_dict[user_id]['authority'] = new_authority
    with open('users_info.json', 'w', encoding='utf-8') as json_file:
        json.dump(user_info_dict, json_file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    update_authority()
    