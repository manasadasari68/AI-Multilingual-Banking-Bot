# AI Multilingual Banking Support Bot

An AI-powered multilingual banking assistant built with FastAPI, Streamlit, LangChain, FAISS, HuggingFace embeddings, and OpenRouter. It detects the user's language, translates the question to English for retrieval and generation, answers from banking PDF documents using RAG, and returns the response in the user's original language.

## Features

- Multilingual support for English, Hindi, Telugu, Tamil, Bengali, Kannada, Malayalam, Marathi, Gujarati, Punjabi, Chinese, Japanese, and Korean
- Automatic language detection with `langdetect`
- Translation flow using `deep-translator`
- Retrieval-Augmented Generation with LangChain and FAISS
- Banking knowledge base from PDF documents
- OpenRouter LLM integration using models like `openai/gpt-4o-mini`
- FastAPI backend with session-based conversation memory
- Streamlit frontend with a polished chat UI and source previews
- Reindex endpoint to rebuild the PDF knowledge base on demand

## Project Structure

```text
project/
├── app/
│   ├── main.py
│   ├── rag.py
│   ├── translator.py
│   ├── language_detector.py
│   ├── chatbot.py
│   └── config.py
├── data/
│   ├── banking_faq.pdf
│   ├── credit_card_guidelines.pdf
│   ├── fraud_awareness.pdf
│   ├── loan_policy.pdf
│   └── rbi_guidelines.pdf
├── frontend/
│   └── streamlit_app.py
├── scripts/
│   └── generate_sample_pdfs.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## How It Works

1. The user sends a banking question in English, Hindi, Telugu, or Tamil.
2. The backend detects the language automatically.
3. Non-English questions are translated to English.
4. Relevant PDF chunks are retrieved from the FAISS knowledge base.
5. OpenRouter generates a grounded banking response from the retrieved context.
6. The response is translated back to the original language.
7. The frontend shows the answer, translated query, and supporting document snippets.

## Sample Banking Topics Covered

- Loan inquiry
- KYC information
- Credit card support
- Account opening
- Fraud awareness
- ATM queries

## Prerequisites

- Python 3.10+
- An OpenRouter API key

## Local Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create your environment file:

```bash
copy .env.example .env
```

4. Update `.env` with your OpenRouter key:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini
```

5. Regenerate the sample banking PDFs if needed:

```bash
python scripts/generate_sample_pdfs.py
```

## Run the Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend health endpoint:

```text
http://localhost:8000/
```

Chat endpoint:

```text
POST http://localhost:8000/chat
```

## Run the Frontend

Open a second terminal and run:

```bash
streamlit run frontend/streamlit_app.py
```

The frontend uses `http://localhost:8000` by default. To point it elsewhere:

```bash
set BACKEND_BASE_URL=http://localhost:8000
streamlit run frontend/streamlit_app.py
```

## API Request Example

Request:

```json
{
  "message": "హోమ్ లోన్ కోసం ఏ డాక్యుమెంట్స్ కావాలి?"
}
```

Response:

```json
{
  "session_id": "1ac9d2d4-c4e6-4a18-9ee5-12c7188f18fd",
  "language": "Telugu",
  "language_code": "te",
  "translated_query": "What documents are required for home loan?",
  "response": "హోమ్ లోన్ కోసం సాధారణంగా ఆధార్, పాన్, ఆదాయ రుజువు, బ్యాంక్ స్టేట్‌మెంట్లు మరియు ఆస్తి పత్రాలు అవసరం.",
  "response_in_english": "Based on the loan policy documents, home loans usually require Aadhaar, PAN, income proof, bank statements, and property papers.",
  "sources": [
    {
      "source": "loan_policy.pdf",
      "page": "1",
      "snippet": "Typical home loan documents include Aadhaar, PAN, salary slips or business income proof..."
    }
  ],
  "history": []
}
```

## Docker Deployment

### Backend only

```bash
docker build -t multilingual-banking-bot .
docker run --env-file .env -p 8000:8000 multilingual-banking-bot
```

### Backend + Frontend with Docker Compose

```bash
docker compose up --build
```

Services:

- FastAPI backend: `http://localhost:8000`
- Streamlit frontend: `http://localhost:8501`

## Knowledge Base Notes

- The app automatically scans all PDF files inside `data/`.
- On first startup, it creates a FAISS index in `vector_store/`.
- Use `POST /reindex` after adding or replacing PDFs.
- The repo also includes Markdown copies of the sample documents so you can read the same content directly in VS Code.

## Suggested PDFs for Real Usage

Replace the sample files in `data/` with real documents such as:

- RBI banking awareness booklets
- Bank loan policy documents
- Customer onboarding and KYC manuals
- Credit card usage and dispute guidelines
- Fraud prevention advisories

## Troubleshooting

- If the backend fails at startup, verify `OPENROUTER_API_KEY` in `.env`.
- If embedding startup fails, reinstall dependencies so `langchain-huggingface` and a modern `sentence-transformers` version are picked up.
- If answers are weak, add richer PDF content and call `POST /reindex`.
- If translations fall back to the original text, retry once because public translation services can occasionally fail.
- If FAISS index creation is slow on first run, that is expected while embeddings are generated.
- If PDFs do not preview in VS Code, open the `.md` files in `data/` instead. PDFs are binary files and VS Code may not preview them unless a PDF viewer extension is installed.
