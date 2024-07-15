import json

# 读取JSON文件
def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# 格式化数据并保存到文件
def format_and_save_data(data, output_file_path):
    with open(output_file_path, 'w', encoding='utf-8') as file:
        for entry in data:
            question = entry.get('question', 'No question provided')
            cot_reason = entry.get('cot_reason', 'No reason provided')
            cot_answer = entry.get('cot_answer', 'No answer provided')
            knowl_wikipedia_list = entry['knowl_list']['Q']['wikipedia']

            file.write(f"Question: {question}\n")
            file.write(f"Original reason: {cot_reason}\n")
            file.write(f"Original final answer: {cot_answer}\n")

            # 处理知识列表
            file.write("Retrieved content:\n")
            for i, item in enumerate(knowl_wikipedia_list, start=1):
                title = item[0] if len(item) > 0 else 'No title'
                passage = item[1] if len(item) > 1 else 'No passage'
                file.write(f"{i}.Title: {title}, Passage: {passage}\n")
            
            file.write("New reason: \n")
            file.write("New final answer: \n")
            file.write("\n")  # 添加空行以分隔不同的条目


# 示例路径
file_path = 'timequestions/test_out.json'
output_file_path = 'timequestions/test_out_prompt.txt'

# 加载数据
data = load_json_file(file_path)

# 格式化数据并保存到文件
format_and_save_data(data, output_file_path)
