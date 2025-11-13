import os
import re
import pandas as pd
from datetime import datetime, timedelta
import warnings
from sentence_transformers import SentenceTransformer
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

class FinanceAIChatbot:
    def __init__(self, api_key: str, dataset_path: str):
        if not api_key:
            raise ValueError("API key is required!")

        genai.configure(api_key=api_key)
        self.model_name = self._select_model()
        self.model = genai.GenerativeModel(self.model_name)

        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection("finance_faqs_context")
        self._load_dataset(dataset_path)

        self.session_start = datetime.now()
        self.total_queries = 0
        self.response_cache = {}
        self.cache_duration = timedelta(minutes=10)

        self._check_connection()

    def _select_model(self):
        return "gemini-2.5-flash" 

    def _check_connection(self):
        # verify Gemini API connectivity
        try:
            _ = self.model.generate_content("Connection test successful.")
            print(f"Gemini model connected ({self.model_name})\n")
        except Exception as e:
            print(f"Model connection failed: {e}\n")

    # dataset
    def _load_dataset(self, dataset_path):
        df = pd.read_csv(dataset_path)
        df.dropna(inplace=True)

        texts = df["input"].tolist()
        answers = df["output"].tolist()
        embeddings = self.embedder.encode(texts, show_progress_bar=True)

        # Chunk large data into batches to prevent Chroma OOM
        batch_size = 1500
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_embeds = embeddings[i : i + batch_size]
            batch_answers = answers[i : i + batch_size]
            self.collection.add(
                documents=batch_texts,
                embeddings=batch_embeds,
                metadatas=[{"answer": a} for a in batch_answers],
                ids=[str(j) for j in range(i, i + len(batch_texts))],
            )
        print(f"Dataset embedded into Chroma ({len(texts)} entries)\n")

    # response logic
    def _normalize(self, text: str) -> str:
        text = str(text).lower().strip()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _query_backend(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            if hasattr(response, "text") and response.text:
                return response.text.strip()
            return "No valid response generated."
        except Exception as e:
            return f"Backend Error: {str(e)}"

    def _build_context(self, user_query: str, top_k: int = 3) -> str:
        # retrieve relevant context from Chroma
        query_emb = self.embedder.encode([user_query])
        results = self.collection.query(query_embeddings=query_emb, n_results=top_k)

        context = ""
        for i in range(len(results["documents"][0])):
            q = results["documents"][0][i]
            a = results["metadatas"][0][i]["answer"]
            context += f"{i+1}. Q: {q}\nA: {a}\n\n"
        return context

    def get_response(self, user_query: str) -> str:
        cache_key = self._normalize(user_query)
        if cache_key in self.response_cache:
            cached_response, cache_time = self.response_cache[cache_key]
            if datetime.now() - cache_time < self.cache_duration:
                return cached_response + "\n\n(Cached response)"

        context = self._build_context(user_query, top_k=3)

        prompt = f"""
            You are a helpful, trustworthy financial assistant.
            Use the dataset context below to answer the user's question accurately.

            Context:
            {context}

            User Question: {user_query}

            Answer clearly in under 150 words and provide one actionable insight if possible.
        """

        answer = self._query_backend(prompt)
        self.response_cache[cache_key] = (answer, datetime.now())
        self.total_queries += 1
        return answer


    def chat(self):
        print("\nFinance AI Chatbot Ready!")
        print("Type 'exit' or 'quit' to end session.\n")

        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue

                if user_input.lower() in ["quit", "exit", "bye"]:
                    print("\nGoodbye! Stay financially smart.")
                    break

                if user_input.lower() == "stats":
                    continue

                response = self.get_response(user_input)
                print(f"\nBot:\n{response}\n")

            except KeyboardInterrupt:
                print("\n\nSession interrupted.")
                break
            except Exception as e:
                print(f"\nError: {e}")

if __name__ == "__main__":
    try:
        api_key = os.getenv("AI_API_KEY")
        dataset_path = "final_combined.csv" 

        if not api_key:
            raise ValueError("API key not found! Please set it in your .env file.")
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")

        bot = FinanceAIChatbot(api_key, dataset_path)
        bot.chat()

    except Exception as e:
        print(f"\nStartup failed: {e}")
