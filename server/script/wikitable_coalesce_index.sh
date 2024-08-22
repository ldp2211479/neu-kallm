
base_path=./model
source=wikitable
nbits=2

python ./utils/wikitable/coalesce.py \
	--input ${base_path}/${source}/${source}/indexes/wikitable_index.nbits=${nbits} \
	--output ${base_path}/${source}/indexes/${source}.nbits=${nbits}
