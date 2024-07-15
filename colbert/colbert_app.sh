
export CUDA_VISIBLE_DEVICES=3

gunicorn \
    'colbert_app:gunicorn_app( \
     wikipedia_colbert_index_path="./model/wikipedia_11_06_2023/wikipedia.all.1bits", \
     wikipedia_colbert_checkpoint="./model/colbert_checkpoint", \
     wikipedia_colbert_collection_path="./model/wikipedia_11_06_2023/collection_all.tsv", \
     
     wikidata_llama_model_path="./model/wikidata/llama-7b-wikiwebquestions-qald7", \
     wikidata_refined_model_name="./model/wikidata/refined", \
     wikidata_path_qid_title_map="./model/wikidata/qid_to_title_en.pkl", \
     wikidata_path_title_pid_map="./model/wikidata/title_to_pid_en.pkl", \
     
     memory_map="false")' \
    --access-logfile=- \
    --bind 0.0.0.0:5000 \
    --workers 1 \
    --timeout 0 \