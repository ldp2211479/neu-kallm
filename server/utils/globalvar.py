def init():
    global widipedia_searcher
    global wikitable_searcher
    global wikidata_llama_model
    global wikidata_llama_tokenizer
    global refinedLinker
    global jinja_environment
    
    global gpu_memory_utilization
    
    wikitable_searcher = None
    widipedia_searcher = None
    wikidata_llama_model = None
    wikidata_llama_tokenizer = None
    refinedLinker = None
    jinja_environment = None
    
    gpu_memory_utilization = 0.4