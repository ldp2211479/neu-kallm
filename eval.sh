BASE_OUTPUT_PATH="outputs_sigangluo"
DATASET="timequestions"
MODE="equal"
SPLIT="test"
COT="True"
python eval.py \
    --dataset ${DATASET} \
    --input ${BASE_OUTPUT_PATH}/${DATASET}/${SPLIT}_out.json \
    --output ${BASE_OUTPUT_PATH}/${DATASET}/eval/${SPLIT}_${MODE}_${COT}_out.json \
    --use_cot_answer ${COT} \
    --mode ${MODE}