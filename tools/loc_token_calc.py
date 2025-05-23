import json

import tiktoken

def count_tokens(text, model="gpt-3.5-turbo"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


# Example usage
text = "You are a helpful, pattern-following assistant that translates corporate jargon into plain English."
model = "gpt-4o"
token_count = count_tokens(text, model)
print(f"Token count for '{text}' using {model}: {token_count}")

def loc_counter(data,):
    loc = 0
    for testcase in data:
        codelines = testcase["code"].split("\n")
        comment_mark = False
        counter = 0
        for codeline in codelines:
            if codeline.startswith("#"):
                continue
            if not comment_mark and (codeline.startswith('\"\"\"') or codeline.startswith("\'\'\'")):
                comment_mark = True
                continue
            if comment_mark and (codeline.startswith('\"\"\"') or codeline.startswith("\'\'\'")):
                comment_mark = False
                continue
            if comment_mark:
                continue
            counter += 1
        loc += counter
    return loc

loc = 0
token = 0
answers = json.load(open("data/project_eval_answer.json", "r", encoding="utf-8"))
n = len(answers)
for project_id in answers:
    answer = answers[project_id]
    loc += loc_counter(answer)
    for file in answer:
        token += count_tokens(file["code"])

print("#LOC:", loc/n)
print("#Tokens:", token/n)