
export CUDA_VISIBLE_DEVICES=0,1

gunicorn \
    'server_app:gunicorn_app( \
     colbert_root_path="./model", \
     wikipedia_colbert_index_path="wikipedia/indexes/wikipedia.all.nbits=1", \
     wikipedia_colbert_checkpoint="./model/wikipedia/colbert_checkpoint", \
     wikipedia_colbert_collection_path="./model/wikipedia/collection.tsv", \

     wikitable_colbert_index_path="wikitable/indexes/wikitable.nbits=2", \
     wikitable_colbert_checkpoint="./model/wikitable/colbert_checkpoint", \
     wikitable_colbert_collection_path="./model/wikitable/collection.tsv", \

     wikidata_llama_model_path="./model/wikidata/llama-7b-wikiwebquestions-qald7", \
     wikidata_refined_model_name="./model/wikidata/refined", \
     wikidata_path_qid_title_map="./model/wikidata/qid_to_title_en.pkl", \
     wikidata_path_title_pid_map="./model/wikidata/title_to_pid_en.pkl", \
     memory_map="false")' \
    --access-logfile=- \
    --bind 0.0.0.0:5000 \
    --workers 1 \
    --timeout 0 \