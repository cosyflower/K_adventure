### sk-proj-KvJ1AX8zCUYXlEL7Q0fmT3BlbkFJghD5VpM4HRcyi0f8TBCQ
from openai import OpenAI

# 사용자 의도 파악용
def analyze_user_purpose(user_input):
    try:
        prompt = "문서 4종 생성해줘', '연차 신청해줘', '반차 신청해줘', 'DB 검색해줘', '일대일 미팅 검색해줘', '운영보고서 작성해줘', '없는 기능입니다' 중에 입력 값과 가장 비슷한 하나를 출력해줘"
        client = OpenAI(api_key='sk-proj-KvJ1AX8zCUYXlEL7Q0fmT3BlbkFJghD5VpM4HRcyi0f8TBCQ')
        response = client.chat.completions.create(
        model="ft:gpt-3.5-turbo-0125:personal:userpurposemodel:9RfNJJz2",
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
        model="ft:gpt-3.5-turbo-0125:personal:companymodelsmall:9S5Afwy4", 
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