dataset_path=./dataset
source=wikipedia
dump_file=enwiki-latest-pages-articles.xml.bz2
text=text


python -m utils.wikipedia.wikiextractor.WikiExtractor ${dataset_path}/${dump_file} \
        --templates ${dataset_path}/${source}/wiki_templates.txt \
        --output ${dataset_path}/${source}/${text} \
        --links
