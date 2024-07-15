export TRANSFORMERS_VERBOSITY=error
# export OPENAI_API_KEY=YOUR_KEY
export CUDA_VISIBLE_DEVICES=1,2
BASE_OUTPUT_PATH="outputs_sigangluo"
DATASET="tiq"
TYPE="test"
MODEL="llama3:70b"

python run.py \
    --model ${MODEL} \
    --dataset ${DATASET} \
    --input datasets/${DATASET}/${TYPE}.json \
    --output ${BASE_OUTPUT_PATH}/${DATASET}/${TYPE}_out.json
