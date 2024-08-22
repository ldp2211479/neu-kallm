dataset_path=./dataset
model_path=./model
source=wikipedia
text=text
collection=collection.tsv
max_block_words=100
language=en

python utils/wikipedia/split_passages.py \
    --input_path ${dataset_path}/${source}/${text} \
    --output_path ${model_path}/${source}/${collection} \
    --max_block_words ${max_block_words} \
    --language ${language} \
    --translation_cache ${model_path}/${source}/translation_cache.json