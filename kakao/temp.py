

def get_info_equation_sheet():
    # Google Sheets 연결
    gc = gspread.service_account(filename=r'C:\Users\skkum\Desktop\K\2024년 1분기 재무제표\zerobot-425701-15f85b16185c.json')
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
    gc = gspread.service_account(filename=r'C:\Users\skkum\Desktop\K\2024년 1분기 재무제표\zerobot-425701-15f85b16185c.json')
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

result_json, equation_prompt, using_item = get_info_equation_sheet()
result_json = dict(OrderedDict({'회사명': "", **result_json}))
n, ft_json_list = filtering_jsonlist(A, using_item)
print(n)
if n == 0 :
    result = merge_and_deduplicate(ft_json_list)
    print(result)
    print("이거는 다음 코드 멈추기 그리고 이 값 수식에서 잘못되었다고 말해주기")
else:
    print(ft_json_list)
    final_output = []
    for ft_js in ft_json_list:
        output = ocr2_phase2_gpt(result_json, equation_prompt,ft_js)
        final_output.append(output)
    print(final_output)
    write_to_google_sheet(final_output)