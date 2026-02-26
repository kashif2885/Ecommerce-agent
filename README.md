# Adoob AI Assistant

A conversational AI agent for **Adoob** — an IT & electronics e-commerce store. Built as a technical assessment using LangGraph, FastAPI, ChromaDB, and the OpenAI API.
![Uploading image.png…]()


---

## Features

- **Pure ReAct agent** (LangGraph) — the LLM reasons over all tools simultaneously; rich tool descriptions guide routing without a separate intent classifier
- **Streaming responses** — tokens stream to the browser in real time via Server-Sent Events (SSE)
- **Tool trace panel** — every tool call (name, input, output) is shown live in a side panel
- **RAG knowledge base** — `Adoob_FAQ.pdf` is ingested at startup into ChromaDB; the agent retrieves relevant chunks to answer policy/store questions
- **Calendar booking** — fully mock in-memory appointment system with timezone-aware past-date validation (Asia/Riyadh)
- **Product catalog** — 10 IT products across 9 categories with search, detail lookup, and side-by-side comparison
- **Products page** — standalone `/products` page with live search, category filter, sort, and expandable spec cards
- **Engaging off-topic handling** — the agent redirects out-of-scope questions with wit and positivity, always steering back to Adoob

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | GPT-5.1 via OpenAI API |
| Embeddings | `text-embedding-3-large` |
| Agent framework | LangGraph (pure ReAct loop) |
| RAG vector store | ChromaDB (`langchain-chroma`) |
| PDF extraction | pdfplumber |
| API server | FastAPI + Uvicorn |
| Frontend | Vanilla JS, SSE streaming |

---

## Project Structure

```
FeelixAI/
├── app/
│   ├── config.py                  # pydantic-settings (.env loader)
│   ├── main.py                    # FastAPI app, lifespan, routes
│   ├── agent/
│   │   ├── graph.py               # LangGraph ReAct graph builder
│   │   ├── prompt.md              # System prompt template ({{DATE}}, {{TIME}} placeholders)
│   │   └── tools/
│   │       ├── calendar_tools.py  # check_availability, book, cancel, list
│   │       ├── catalog_tools.py   # search_products, get_product_details, compare_products
│   │       └── rag_tools.py       # make_rag_tool(vectorstore) factory
│   ├── rag/
│   │   └── ingestion.py           # PDF extraction + ChromaDB ingestion
│   └── routers/
│       └── chat.py                # POST /api/chat (SSE), GET /api/products, GET /api/health
├── static/
│   ├── index.html                 # Chat UI + Tool Trace panel
│   └── products.html              # Product catalog browser
├── Data/
│   └── Adoob_FAQ.pdf              # Knowledge base (store policies, rewards, FAQs)
├── .env                           # Local secrets (not committed)
├── .env.example                   # Template for required env vars
└── requirements.txt
```

---

## Setup

### 1. Clone & create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and fill in your OpenAI API key:

```bash
copy .env.example .env
```

`.env` contents:

```env
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-5.1
EMBEDDING_MODEL=text-embedding-3-large
CHROMA_PERSIST_DIR=./chroma_db_v2
PDF_PATH=./Data/Adoob_FAQ.pdf
```

### 4. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

On first run, the server will:
1. Extract and chunk `Adoob_FAQ.pdf` using pdfplumber
2. Embed all chunks with `text-embedding-3-large`
3. Persist the vector store to `./chroma_db_v2/`
4. Build the LangGraph agent

Subsequent runs load the existing vector store instantly (no re-embedding).

---

## Pages & Endpoints

| URL | Description |
|---|---|
| `http://localhost:8000/` | Chat assistant UI |
| `http://localhost:8000/products` | Product catalog browser |
| `POST /api/chat` | SSE stream — send `{message, session_id}` |
| `GET /api/products` | JSON — full product catalog |
| `GET /api/health` | Health check |
| `DELETE /api/sessions/{id}` | Clear a session's message history |

---

## Agent Tools

### Calendar (mock in-memory)
| Tool | Description |
|---|---|
| `check_availability(date, service)` | Lists open time slots on a given date |
| `book_appointment(date, time_slot, service, customer_name, ...)` | Books a slot, returns a booking ID |
| `cancel_appointment(booking_id, reason)` | Cancels a booking by ID |
| `list_appointments(customer_name)` | Lists all bookings for a customer |

> Slot times: 09:00–17:00 AST. Past dates and elapsed slots are automatically rejected.

### Product Catalog (10 products)
| Tool | Description |
|---|---|
| `search_products(query, category)` | Keyword search, returns top 5 by relevance + rating |
| `get_product_details(product_id)` | Full specs, price, stock for one product |
| `compare_products(product_ids)` | Side-by-side spec comparison for 2+ products |

Available categories: `Laptops`, `Audio`, `Gaming`, `Cameras`, `Smart Home`, `Office`, `Wearables`, `Storage`, `Peripherals`

### Knowledge Base (RAG)
| Tool | Description |
|---|---|
| `search_knowledge_base(query)` | Retrieves relevant chunks from `Adoob_FAQ.pdf` |

Knowledge base covers: store policies, shipping, returns, warranty, Adoob Rewards loyalty programme, B2B/corporate services, payment methods, security & privacy, FAQs, and technical glossary.

---

## SSE Event Types

The `POST /api/chat` endpoint streams newline-delimited `data: <json>` events:

| Event type | Payload fields | Description |
|---|---|---|
| `token` | `content` | Streaming LLM text token |
| `tool_start` | `tool_name`, `input` | Tool call initiated |
| `tool_end` | `tool_name`, `output`, `timestamp` | Tool call completed |
| `done` | `session_id`, `tool_trace` | Turn complete; full trace included |
| `error` | `message` | Something went wrong |

---

## Key Design Decisions

**Pure ReAct (no intent classifier)** — All 8 tools are bound to the LLM simultaneously. Detailed tool docstrings act as routing signals. This is simpler and equally correct for this use case.

**Timezone-aware calendar** — All date/time comparisons use `Asia/Riyadh` (AST, UTC+3) via Python's `zoneinfo` module. The `tzdata` package is included in `requirements.txt` for Windows compatibility.

**Streaming via `astream_events`** — Uses LangGraph's `graph.astream_events(..., version="v2")` so tool events and LLM tokens are emitted independently and can be forwarded to the browser as they happen.

**Session persistence** — Conversation history is kept in a server-side `dict[session_id → list[BaseMessage]]`. The client receives its `session_id` on the first `done` event and includes it in subsequent requests.

---

## Requirements

```
langchain>=0.3.0
langchain-openai>=0.3.0
langchain-community>=0.3.0
langchain-chroma>=0.1.0
langgraph>=0.2.0
openai>=1.50.0
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pdfplumber>=0.11.0
chromadb>=0.5.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-docx>=1.0.0
tzdata>=2024.1
```
