import json

# 定义一个递归函数将字典中的键转换为小写
def lowercase_keys(obj):
    if isinstance(obj, dict):
        return {k.lower(): lowercase_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [lowercase_keys(item) for item in obj]
    else:
        return obj

# 读取 JSON 文件，转换键为小写，并保存到新文件中
def convert_json_keys_to_lowercase(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        json_content = json.load(f)

    lowercase_json_content = lowercase_keys(json_content)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(lowercase_json_content, f, ensure_ascii=False, indent=4)

split = 'dev'
# 输入和输出文件路径
input_file = f'raw/{split}.json'
output_file = f'{split}.json'

# 调用函数进行转换
convert_json_keys_to_lowercase(input_file, output_file)

print(f"转换完成，结果已保存到 {output_file}")