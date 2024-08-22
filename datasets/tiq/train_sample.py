import json
import random

# Load the dataset
file_path = 'train.json'  # 修改为你的数据集文件路径

with open(file_path, 'r') as file:
    data = json.load(file)

# Function to balance and sample data
def sample_balanced_data(data, sample_size):
    # Group data by temporal_relation
    type_dict = {}
    for item in data:
        question_type = item["temporal_relation"][0]
        if question_type not in type_dict:
            type_dict[question_type] = []
        type_dict[question_type].append(item)
    
    # Calculate how many samples per type
    types = list(type_dict.keys())
    num_types = len(types)
    samples_per_type = sample_size // num_types

    # Sample data
    sampled_data = []
    for question_type in types:
        sampled_data.extend(random.sample(type_dict[question_type], min(samples_per_type, len(type_dict[question_type]))))
    
    return sampled_data

# Sample 200 balanced data points
sampled_data = sample_balanced_data(data, 200)

# Save the sampled data to a new JSON file
output_file_path = 'train_sample.json'
with open(output_file_path, 'w') as output_file:
    json.dump(sampled_data, output_file, indent=4)

print(f'Sampled data saved to {output_file_path}')