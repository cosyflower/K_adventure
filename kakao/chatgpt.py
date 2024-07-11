### sk-proj-KvJ1AX8zCUYXlEL7Q0fmT3BlbkFJghD5VpM4HRcyi0f8TBCQ
from openai import OpenAI

# 사용자 의도 파악용
def analyze_user_purpose(user_input):
    try:
        prompt = "문서4종,정기예금회전시스템,일대일미팅,보안시스템,휴가신청시스템,로제봇 중에서 입력값의 오타나 의미를 고려해서 관련된 1개를 출력해. 만약에 관련된 항목이 없는 거 같으면 x를 출력해."
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
            "content": user_input
            }
        ],)
        output = response.choices[0].message.content
    except Exception as e:
        print(f"analyze_user_purpose chatgpt error: {e}")
        return user_input
    return output

# DB_1의 정확한 회사명 파악용
def analyze_company_name(all_company_names,user_input):
    try:
        prompt = "[]안에 있는 회사명들 중에서 ()안에 있는 회사명과 가장 비슷한 회사를 출력해."
        client = OpenAI(api_key='sk-proj-KvJ1AX8zCUYXlEL7Q0fmT3BlbkFJghD5VpM4HRcyi0f8TBCQ')
        response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {
            "role": "system",
            "content": prompt
            },
            {
            "role": "user",
            "content": str(all_company_names) + " (" + user_input + ")"
            }
        ],)
        output = response.choices[0].message.content
    except Exception as e:
        print(f"analyze_company_name chatgpt error: {e}")
        return user_input
    return output

if __name__ == "__main__":
    a = analyze_user_purpose("")
    print(a)