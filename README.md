# 🚀 BidCraft AI

**BidCraft AI** is an advanced, enterprise-grade GenAI solution designed to automate the grueling process of analyzing complex Request for Proposals (RFPs) and generating technical responses. Built specifically for Presales, Bid Management, and Business Development teams.

---

## 🎯 The Problem
Writing technical proposals and responding to tenders (RFPs) is a massive bottleneck for software houses, engineering firms, and consultancies. Teams spend hundreds of hours manually reading 500+ page documents, extracting requirements, and hunting through past projects to write custom responses. A single missed requirement can disqualify a company from winning a multi-million dollar contract.

## 💡 The Solution
**BidCraft AI** leverages an **Advanced RAG (Retrieval-Augmented Generation)** architecture to:
1. Parse complex RFP documents (including complex tables and multi-column layouts).
2. Query a secure, localized database of past company proposals and project histories.
3. Automatically generate precise, professional B2B technical responses complete with strict citations (referencing exact past files and page numbers).

---

## 🛠️ Architecture & Tech Stack

* **LLM Engine:** Groq API / Llama-3 (Fast, low-latency, and cost-efficient generation)
* **Document Parsing & Layout Analysis:** LlamaParse / Docling (Preserving table structures and multi-page formatting)
* **Embeddings:** HuggingFace (`BAAI/bge-m3` for robust cross-lingual support)
* **Vector Database:** ChromaDB (In-memory/Local vector storage for zero-cost architecture)
* **Frontend UI:** Streamlit (Interactive, rapid prototyping interface)
* **Backend Framework:** Python / FastAPI

---

## ⚙️ Core Engineering Features

* **Table-Aware Parsing:** Avoids standard broken text extraction by accurately interpreting tables and layout structures from complex PDF RFPs.
* **Metadata-Filtered Retrieval:** Prevents cross-project contamination and hallucinations by filtering knowledge base searches using targeted project metadata.
* **Strict Source Citations:** Every generated response explicitly points back to the historical company file and page used as evidence.
* **Modular Architecture:** Designed with clean separation of concerns, making it trivial to swap out free APIs for enterprise-grade self-hosted LLMs (`vLLM` / Ollama) or secure cloud infrastructure (Azure OpenAI / AWS Bedrock).

---

## 🚀 Getting Started Locally

**Prerequisites :**
- Python 3.10 or higher

**Installation :**
1. clone the repository:
```text
git clone [https://github.com/Ahmed-M-Gh/BidCraft-AI.git](https://github.com/Ahmed-M-Gh/BidCraft-AI.git)
cd bidcraft-ai
```

2. create python environment
```text
python -m venv env-name
``` 

3. Activate environment :
```text
env-name\Scripts\activate
```

4. update pip & Install Dependencies:
```text
python -m pip install --upgrade pip
pip install -r requirements.txt
```

5. Run the app:
```text
uvicorn src.main:app --reload --port 5000 --host 0.0.0.0
```
- after that go to [http://127.0.0.1:5000/docs](http://127.0.0.1:5000/docs) for swagger interface


## 👤 Author
**Ahmed Ghoneim**

> GenAI Engineer

[LinkedIn](https://www.linkedin.com/in/ahmed-ghoneim-3450892b7) • [Portfolio](https://portfolio-xi-nine-iekbhuzjyy.vercel.app/)