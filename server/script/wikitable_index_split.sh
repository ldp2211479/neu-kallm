
# export CUDA_HOME=/usr/local/cuda-11.4

dataset_path=./dataset
model_path=./model
source=wikitable
model=colbert_checkpoint
collection=collection.tsv
tables_text=tables_text.pkl
nbits=2
nranks=4

python ./utils/wikitable/wikitable_index_split.py \
	--path_tables_text ${dataset_path}/${source}/${tables_text} \
	--collection ${model_path}/${source}/${collection} \
	--checkpoint ${model_path}/${source}/${model} \
	--root_path ${model_path}/${source} \
	--experiment_name ${source} \
	--index_name ${source}.nbits=${nbits} \
    --nbits ${nbits} \
    --nranks ${nranks} \
    --doc_maxlen 512