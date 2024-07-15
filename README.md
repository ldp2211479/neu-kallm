## Environment

克隆仓库：

```
git clone 
cd 
```

创建Python环境：

```
conda env create -f requirements.yaml
```

激活环境并安装依赖包

```
conda activate kg
python -m spacy download en_core_web_sm
```

无论何时运行以下任何命令，请确保此环境都已激活。

## Model and Datasets Download



## Directory Structure

以下为实际运行的目录结构

- model
	- 
- datasets
	- tiq
	- timequestions
- colbert
	- model
		- wikipedia_11_06_2023
		- colbert_checkpoint
- outputs
- utils





## 😋How to run

#### 1. Running a retrieval service

进入环境

```bash
conda activate ldy_kg_wikichat
```

**Wikipedia Text and Table**

首先，为了从维基百科检索文本与表格，您可以通过运行以下指令来启动一个Colbert服务器，以对证据进行检索。建议您通过 **tmux** **/ screen** 等后台程序启动一个服务器后台，来持续监听信号。

```
cd colbert
bash colbert_app.sh
```

使用 ColBERT 不需要 GPU，因为它设置为使用 CPU。整个索引将加载到 RAM，这需要大约 100GB 的 RAM。如果您没有那么多 RAM，您可以通过添加`colbert_memory_map=true`到此命令来启用内存映射。这会将 RAM 使用量减少到大约 35GB，但会使检索速度变慢。

默认情况下，服务器监听端口 5000。您可以通过在新终端中运行如下 curl 命令来测试此服务器：

```bash
curl http://127.0.0.1:5000/search -d '{"query": "who is the current monarch of the united kingdom?", "evi_num": 1, "source": "wikipedia"}' -X GET -H 'Content-Type: application/json'
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

默认情况下，我们采用 Ollama 框架来进行测试。在 linux 系统中，您可以通过以下命令来下载 Ollama 框架，并运行一个本地的大模型，这非常方便快捷。 

```bash
curl -fsSL https://ollama.com/install.sh | sh
Ollama run llama3:70b
```

在确保您已经开启了上述检索服务器的前提下，您可以运行以下 sh 脚本来进行推理：

```
bash run.sh
```

除此之外，您可以选择采用 gpt-3.5-turbo-0613 、 GPT4 等模型进行推理。创建账户并获取 OpenAI 的 API 密钥 (https://openai.com)，并对脚本进行以下更改：

```bash
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



#### **eval**
