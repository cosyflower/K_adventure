"""
- [ ] 인자를 이름들이 담긴 리스트를 인자로 받는다
- [ ] 랜덤으로 값을 서로 매칭합니다. 2명씩 짝을 지어 매칭을 진행합니다
- [ ] 전체 인원이 홀수 인 경우에는 자기 자신과 짝을 짓는 경우가 반드시 존재한다
- [ ] 이런 경우에는 자기 자신과 짝을 짓은 경우를 1번만 허용한다
- [ ] 랜덤으로 계속 매칭할 때마다 기존에 만났던 짝을 만나면 다시 랜덤으로 매칭한다
- [ ] 이전에 매칭되었던 사람과 다시 매칭이 안될 때까지 반복.
- [ ] 모든 사람이 새로운 사람과 매칭된 경우 매칭 결과를 출력한다
- [ ] 모든 사람이 서로 다른 사람과 한번 씩 매칭이 완료되어야 종료한다
"""
import random

def match_names(name_list):
    if len(name_list) < 2:
        print("At least two names are required to make pairs.")
        return

    previous_matches = set()
    num_names = len(name_list)
    max_self_match = 1
    all_matches = []

    while True:
        random.shuffle(name_list)
        pairs = []
        self_match_count = 0
        for i in range(0, num_names, 2):
            if i + 1 < num_names:
                if (name_list[i], name_list[i+1]) in previous_matches or (name_list[i+1], name_list[i]) in previous_matches:
                    break
                pairs.append((name_list[i], name_list[i+1]))
            else:
                if self_match_count < max_self_match:
                    pairs.append((name_list[i], name_list[i]))
                    self_match_count += 1
                else:
                    break

        # Check if all pairs are unique
        if len(pairs) * 2 >= num_names and len(set(pairs)) == len(pairs):
            previous_matches.update(pairs)
            all_matches.append(pairs)
            if len(previous_matches) >= (num_names * (num_names - 1)) / 2 + (1 if num_names % 2 == 1 else 0):
                break

    print("All matching results:")
    for match in all_matches:
        print(match)
    return all_matches

# Example usage
name_list = ["Alice", "Bob", "Charlie", "David", "Eve"]
all_matching_results = match_names(name_list)


