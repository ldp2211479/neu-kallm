

## Environment

Clone:

```
git clone 
cd 
```

#### Create environment for inference

Create a Python environment:

```
conda env create -f environments.yml
```

Activate the environment and install dependency packages：

```
conda activate kallm
python -m spacy download en_core_web_sm
```

#### Create environment for Retrieval

Create a Python environment:

```
cd server
conda env create -f server_env.yml
```

Activate the environment and install dependency packages：

```
conda activate kg_server
```



## Model and Datasets Download

#### Running ReFiNED model for Wikidata retrieval

Download the fine-tuned ReFiNED model by:

```
pip install https://github.com/amazon-science/ReFinED/archive/refs/tags/V1.zip 
mkdir -p <your_directory>
curl https://almond-static.stanford.edu/research/qald/refined-finetune/config.json -o <your_directory>/config.json
curl https://almond-static.stanford.edu/research/qald/refined-finetune/model.pt -o <your_directory>/model.pt
curl https://almond-static.stanford.edu/research/qald/refined-finetune/precomputed_entity_descriptions_emb_wikidata_33831487-300.np -o <your_directory>/precomputed_entity_descriptions_emb_wikidata_33831487-300.np
```

By default, I recommend you download it to `~/server/model/wikidata/refined`.



## Directory Structure

以下为实际运行的目录结构：

```
-- datasets
-- outputs
-- server
    -- ColBERT
    -- dataset （创建Wikipedia和Wikitable检索的中间文件）
        -- wikipedia
        -- wikitable
    -- model
        -- wikidata
            -- llama-7b-wikiwebquestions-qald7
            -- refined
        -- wikipedia
            -- indexes
            -- colbert_checkpoint
            collection.tsv
        -- wikitable
            -- indexes
            -- colbert_checkpoint
            collection.tsv
    -- prompts （Wikidata检索下LLAMA模型的提示模板）
    -- script （创建Wikipedia和Wikitable检索的脚本文件）
    -- utils
        -- wikitable
        -- wikipedia
        -- wikidata
        globalvar.py
    server_app.py
-- utils
    -- parser （数据解析器）
    -- retrieval （推理器与检索服务器的交互函数）
    eval_utils.py
    globalvar.py
    knowl_query.py
    openai_utils.py
    other_prompts.py
eval.py
run.py
```



## 😋How to run

#### 1. Running a retrieval service

进入环境

```bash
conda activate ldy_kg_wikichat
```

首先，为了从维基百科检索文本与表格，您可以通过运行以下指令来启动一个服务器，以对证据进行检索。建议您通过 **tmux** **/ screen** 等后台程序启动一个服务器后台，来持续监听信号。

```
cd colbert
bash colbert_app.sh
```

该服务器中存在三个参数，通过`source`参数来进行检索源的选择。

**Wikipedia Text and Table**

使用 ColBERT 不需要 GPU，因为它设置为使用 CPU。整个索引将加载到 RAM，这需要大约 100GB 的 RAM。如果您没有那么多 RAM，您可以通过添加`colbert_memory_map=true`到此命令来启用内存映射。这会将 RAM 使用量减少到大约 35GB，但会使检索速度变慢。

默认情况下，服务器监听端口 5000。您可以通过在新终端中运行如下 curl 命令来测试此服务器：

```bash
curl http://127.0.0.1:5000/search -d '{"query": "who is the current monarch of the united kingdom?", "evi_num": 1, "source": "wikipedia"}' -X GET -H 'Content-Type: application/json'
```

**Wikitable and Infobox**

默认情况下，服务器监听端口 5000。您可以通过在新终端中运行如下 curl 命令来测试此服务器：

```bash
curl http://127.0.0.1:5000/search -d '{"query": "who is the current monarch of the united kingdom?", "evi_num": 1, "source": "wikitable"}' -X GET -H 'Content-Type: application/json'
```

**Wikidata**

默认情况下，服务器监听端口 5000。您可以通过在新终端中运行如下 curl 命令来测试此服务器：

```bash
curl http://127.0.0.1:5000/search -d '{"query": "what is the political system in argentina?", "source":"wikidata"}' -X GET -H 'Content-Type: application/json'
```

#### 2. Inference

进入环境

```
conda activate ldy_kg_cok
```

默认情况下，我们采用 Ollama 框架来进行测试。在 Linux 系统中，您可以通过以下命令来下载 Ollama 框架，并运行一个本地的大模型，这非常方便快捷。 

```
curl -fsSL https://ollama.com/install.sh | sh
Ollama run llama3:70b
```

在确保您已经开启了上述检索服务器的前提下，您可以运行以下 sh 脚本来进行推理：

```
bash run.sh
```

除此之外，您可以选择采用 gpt-3.5-turbo-0613 、 GPT4 等模型进行推理。创建账户并获取 OpenAI 的 API 密钥 (https://openai.com)，并对脚本进行以下更改：

```
export TRANSFORMERS_VERBOSITY=error
export OPENAI_API_KEY=<YOUR_KEY>
DATASET="timequestions"
TYPE="train"
MODEL="gpt-3.5-turbo-0613"

python run.py \
    --model ${MODEL} \
    --dataset ${DATASET} \
    --input datasets/${DATASET}/${DATASET}_${TYPE}.json \
    --output outputs/${DATASET}/${DATASET}_${TYPE}_out.json
```



## 🤯Creating Colbert Indexes

#### 1. Download the Wikipedia dump

进入 `server` 中，运行以下脚本文件以下载最新的wikipedia dumps。

```
bash script/download_wikipedia_dumps.sh
```

默认情况下，文件`enwiki-latest-pages-articles.xml.bz2`会下载在`~/server/dataset`中。如果您需要，可以自行修改script文件夹中的脚本配置。

#### 2. Wikipedia

The following script defaults the wikipedia dump to the directory `~/server/dataset/enwiki-latest-pages-articles.xml.bz2`.

Run the Wikipedia parser：

```
bash script/wikipedia_parser.sh
```

This will extract the pages into a set of sharded files, which will be located in the text/ directory. This step takes a few hours.

Run the splitter：

```
bash script/wikipedia_split_passages.sh
```

This script will split the Wikipedia documents into blocks, with each block containing up to `max_block_words` words. It will write these blocks into `collection_all.tsv` which is then used for making the ColBERT index.

Run this command to start ColBERT indexing. This step should be run on GPUs:

```
bash script/wikipedia_index_split.sh
```

Optionally, you can merge all the smaller index files into a single file. This will enable you to use mempory mapping when loading the index, which will reduce the RAM usage at the cost of increasing the retrieval speed. This step requires enough RAM to load the entire index, about 100GB of RAM, but after that, the resulting index can be run on a machine with as little as 35GB of RAM.

```
bash script/wikipedia_coalesce_index.sh
```

#### 3. Wikitable and Infobox

The following script defaults the wikipedia dump to the directory `~/server/dataset/enwiki-latest-pages-articles.xml.bz2`.

Run the Wikitable and Infobox parser：

```
bash script/wikitable_parser.sh
```

By running [wikitextparser](https://github.com/5j9/wikitextparser) and regular expression, this will parse the Wikipedia page into a textualized table.

Run this command to generate ColBERT collection and start ColBERT indexing. This step should be run on GPUs:

```
bash script/wikitable_index_split.sh
```

Optionally, you can merge all the smaller index files into a single file. This will enable you to use mempory mapping when loading the index, which will reduce the RAM usage at the cost of increasing the retrieval speed. 

```
bash script/wikitable_coalesce_index.sh
```



## Evaluate

