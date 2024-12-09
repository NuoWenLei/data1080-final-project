# Multi Agent System for Building Stock Portfolios

Took inspiration from [this repository](https://github.com/karthik-codex/Autogen_GraphRAG_Ollama) for project structure.

## Installation and Setup Mac

Follow these steps to set up and run AutoGen GraphRAG Local with Ollama and Chainlit UI:

1. **Install LLMs:**

   Visit [Ollama's website](https://ollama.com/) for installation files.

   ```bash
   ollama pull nomic-embed-text
   ollama serve
   ```

2. **Create conda environment and install packages:**
   ```bash
   conda create -n rag_env python=3.12
   conda activate rag_env
   pip install -r requirements.txt
   ```
3. **Initiate GraphRAG root folder:**

   ```bash
   mkdir -p ./input
   python -m graphrag init --root .
   cp ./utils/settings.yaml ./
   ```

4. **Replace 'embedding.py' and 'openai_embeddings_llm.py' in the GraphRAG package folder using files from Utils folder:**

   Path example: `~/anaconda3/envs/rag_env/lib/python3.12/site-packages/graphrag/query/llm/oai/embedding.py`

   ```bash
   cp ./utils/embedding.py ~/path/to/graphrag/query/llm/oai/
   ```

   Path example: `~/anaconda3/envs/rag_env/lib/python3.12/site-packages/graphrag/llm/openai/openai_embeddings_llm.py`

   ```bash
   cp ./utils/openai_embeddings_llm.py ~/path/to/graphrag/llm/openai/
   ```

5. **Get Financial Data**

   ```bash
   mkdir -p input/markdown/summaries
   mkdir ./tickers
   mv tickers.json ./tickers/
   python collect_data.py
   ```

   See [yfinance package](https://github.com/ranaroussi/yfinance?tab=readme-ov-file) for how we get data about specific stocks.

6. **Add GraphRAG API key in `.env`**

   ```env
   GRAPHRAG_API_KEY=<API_KEY>
   ```

7. **Reload your environmental variables**

   Close and reopen your terminal, then run the following in your terminal to confirm that your `.env` file is properly loaded.

   ```bash
   echo $GRAPHRAG_API_KEY
   ```

8. **Create embeddings and knowledge graph:**

   ```bash
   python -m graphrag index --root .
   ```

9. **Query GraphRag with CLI**

   ```bash
   python -m graphrag query --root . --method global --query "is there any recent trends that could impact the materials industry?"
   ```

<!-- 10. **Start Lite-LLM proxy server:**

```bash
litellm --model ollama_chat/llama3
```

11. **Run app:**
    ```bash
    chainlit run appUI.py
    ``` -->
    
10. **Run Portfolio Construction Script**

   ```bash
   python group_chat.py
   ```

11. **Check results at `weightages/`**

    - `sectors/` contain financial attribute rankings for every sector.
    - `overall_strategy.json` contains distribution of funds over sectors.
    - `final_investments.json` contains the final investments into each stock for each sector.

## For Jupyter Notebook Support

1. **Follow until step 4 in setup above**

2. **Install python kernel for notebook**

   ```bash
   python -m ipykernel install --user
   ```

3. **Run Jupyter Notebook**

   ```bash
   jupyter notebook
   ```
