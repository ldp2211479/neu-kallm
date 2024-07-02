export CUDA_VISIBLE_DEVICES=0
BASE_MODEL="./model/Meta-Llama-3-8B-hf"
DATASET_NAME="./datasets/sparql-contrastive"
OUTPUT_DIR="./model/Meta-Llama-3-8B-hf-sparql-contrastive"
HF_TOKEN="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"
HUB_MODEL_ID="ldp2211479/COK"

python ./finetune/sft_trainer.py \
    --model_name $BASE_MODEL \
    --dataset_name $DATASET_NAME \
    --load_in_8bit \
    --use_peft \
    --batch_size 1 \
    --gradient_accumulation_steps 2 \
    --output_dir $OUTPUT_DIR \
    --num_train_epochs 3 \
    --push_to_hub True\
    --hub_model_id $HUB_MODEL_ID \
    --hf_token $HF_TOKEN \