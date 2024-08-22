

base_path=./model
source=wikipedia
nbits=1
split=all

python ./utils/wikipedia/coalesce.py \
	--input ${base_path}/${source}/${source}_${split}/indexes/${source}.${split}.nbits=${nbits} \
	--output ${base_path}/${source}/indexes/${source}.${split}.nbits=${nbits}