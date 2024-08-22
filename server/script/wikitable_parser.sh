
dataset_path=./dataset
source=wikitable
dump_file=enwiki-latest-pages-articles.xml.bz2
tables_text=tables_text.pkl

python ./utils/wikitable/wikitable_parser.py \
	--path_dump_file ${dataset_path}/${dump_file} \
	--path_tables_text ${dataset_path}/${source}/${tables_text} \
