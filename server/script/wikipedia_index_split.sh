
# export CUDA_VISIBLE_DEVICES=0,1

dataset_path=./dataset
model_path=./model
source=wikipedia
model=colbert_checkpoint
collection=collection.tsv
nbits=1
doc_maxlen=512
split=all
nranks=4

python utils/wikipedia/index_wiki.py \
    --nbits ${nbits} \
    --doc_maxlen ${doc_maxlen} \
    --checkpoint ${model_path}/${source}/${model} \
    --split ${split} \
    --experiment_name ${source}_${split} \
    --index_name ${source}.${split}.nbits=${nbits} \
    --collection ${model_path}/${source}/${collection} \
    --nranks ${nranks}
