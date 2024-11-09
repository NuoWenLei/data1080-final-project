## Installation and Setup Mac

Follow these steps to set up and run AutoGen GraphRAG Local with Ollama and Chainlit UI:

1. **Install LLMs:**

   Visit [Ollama's website](https://ollama.com/) for installation files.

   ```bash
   ollama pull mistral
   ollama pull nomic-embed-text
   ollama pull llama3
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
   python -m graphrag init  --root .
   mv ./utils/settings.yaml ./
   ```

4. **Replace 'embedding.py' in the GraphRAG package folder using files from Utils folder:**

   Path example: ~/anaconda3/envs/rag_env/lib/python3.12/site-packages/graphrag/query/llm/oai/embedding.py

   ```bash
   cp ./utils/embedding.py ~/path/to/graphrag/
   ```

5. **Get Financial Data**

   ```bash
   python collect_data.py
   ```

   See [yfinance package](https://github.com/ranaroussi/yfinance?tab=readme-ov-file) for how we get data about specific stocks.

6. **Add GraphRAG API key in `.env`**

   ```env
   GRAPHRAG_API_KEY=<API_KEY>
   ```

7. **Create embeddings and knowledge graph:**
   ```bash
   python -m graphrag index --root .
   ```
8. **Start Lite-LLM proxy server:**
   ```bash
   litellm --model ollama_chat/llama3
   ```
9. **Run app:**
   ```bash
   chainlit run appUI.py
   ```

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
