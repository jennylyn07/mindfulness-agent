# ☁️ Azure Services Setup Guide
### MindFlow — Mindfulness Agent · Code Without Barriers Hackathon 2026

This guide walks you through provisioning all Azure services required to run MindFlow from scratch, seeding the demo data, indexing journal entries into AI Search, and verifying connectivity.

---

## Overview of Required Services

| Service | Resource Name (example) | Purpose |
|---|---|---|
| Azure OpenAI | `mindflow-openai-2026` | `gpt-4o` for all agents + `text-embedding-3-small-1` for RAG |
| Azure Cosmos DB | `cosmos-jmagno-2026` | All persistence — users, journals, habits, mood logs, memory |
| Azure AI Search | `search-jmagno-2026` | Vector + keyword RAG over `journal-index` (Lumen agent) |
| Azure Functions | `mindflow-functions` | Habits CRUD, mood logging, weekly digest timer *(required — FastAPI proxies all habit/mood calls to it)* |

---

## Prerequisites

- An active [Azure subscription](https://portal.azure.com)
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed (`az --version`) — optional but useful
- [Azure Functions Core Tools v4](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local) (`func --version`) — required to run Functions locally
- Python 3.12+ with `.venv` activated and `backend/requirements.txt` installed
- Node.js 18+ (for the Next.js frontend)
- A `backend/.env` file (see [Environment Variables](#environment-variables))

---

## Step 1 — Azure OpenAI

### 1.1 Create the Resource

1. Go to [portal.azure.com](https://portal.azure.com) → **Create a resource** → search **Azure OpenAI**
2. Fill in:
   - **Subscription:** your subscription
   - **Resource Group:** create new or use existing (e.g., `rg-mindflow`)
   - **Region:** pick a region where GPT-4o is available — check the [model availability matrix](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models)
   - **Name:** e.g., `mindflow-openai-2026`
   - **Pricing tier:** `Standard S0`
3. Click **Review + Create → Create**

### 1.2 Deploy GPT-4o (Chat)

1. Open the resource → click **Go to Azure AI Foundry** (may also appear as **Azure OpenAI Studio**)
2. Navigate to **Deployments → + Deploy model**
3. Select:
   - **Model:** `gpt-4o`
   - **Deployment name:** `gpt-4o` ← must match `.env` exactly
   - **Deployment type:** `Standard`
4. Click **Deploy**

### 1.3 Deploy text-embedding-3-small (Embeddings)

Repeat the deployment process for a second model:

1. **Deployments → + Deploy model**
2. Select:
   - **Model:** `text-embedding-3-small`
   - **Deployment name:** `text-embedding-3-small-1` ← must match `.env` exactly
   - **Deployment type:** `Standard`
3. Click **Deploy**

> This embedding model generates the **1536-dimension vectors** used by Lumen's journal RAG search.

### 1.4 Get Your Keys

In the Azure portal, open your OpenAI resource → **Keys and Endpoint**:

- Copy **Endpoint** → `AZURE_OPENAI_ENDPOINT`
- Copy **Key 1** → `AZURE_OPENAI_KEY`

> **Important:** The endpoint should be the **base URL only** — e.g. `https://mindflow-openai-2026.openai.azure.com/`.
> If your portal shows a path like `/openai/v1`, the backend strips it automatically, but using the base URL avoids any ambiguity.

---

## Step 2 — Azure Cosmos DB

### 2.1 Create the Account

1. Portal → **Create a resource** → search **Azure Cosmos DB**
2. Select **Azure Cosmos DB for NoSQL** (the SQL API)
3. Fill in:
   - **Resource Group:** same as above
   - **Account Name:** e.g., `cosmos-jmagno-2026`
   - **Location:** same region
   - **Capacity mode:** `Serverless` ← recommended for hackathon (no minimum charge)
4. Click **Review + Create → Create**

### 2.2 Create the Database and Containers

Once provisioned, go to **Data Explorer** in the portal:

**Create Database:**
- Database id: `mindflow`
- ☑ Share throughput: **leave unchecked** (Serverless mode)

**Create all 5 containers** — all use partition key `/userId`:

| Container id | Partition key | Purpose |
|---|---|---|
| `users` | `/userId` | User profile + preferences |
| `journal_entries` | `/userId` | River agent journal history |
| `habits` | `/userId` | Grove agent habit tracking |
| `mood_logs` | `/userId` | Lumen agent mood history |
| `user_memory` | `/userId` | Memory agent persistent facts |

> The `seed.py` script will create these containers automatically if they don't exist yet, so manual creation is optional. Creating them manually first lets you verify provisioning before running scripts.

### 2.3 Get Your Keys

Open your Cosmos DB account → **Keys**:

- Copy **URI** → `COSMOS_ENDPOINT`
- Copy **PRIMARY KEY** → `COSMOS_KEY`

### 2.4 Seed the Demo Data

The seed script creates all 5 containers and populates the `demo-user-001` account with a full 14-day hackathon build arc:
- 1 user document
- 14 journal entries
- 5 habits with 7–14 days of logs
- 14 mood log entries
- 1 user memory document with 5 pre-populated facts

**Make sure `backend/.env` is filled in first**, then from the project root with `.venv` activated:

```powershell
python seed/seed.py
```

Expected output:
```
🌱 MindFlow Seed Script
   Endpoint: https://cosmos-jmagno-2026.documents.azure.com:443/
   Database: mindflow
   User ID:  demo-user-001

  ✓ Container ready: users
  ✓ Container ready: journal_entries
  ✓ Container ready: habits
  ✓ Container ready: mood_logs
  ✓ Container ready: user_memory
  ✓ User upserted: Jen (demo-user-001)
  ✓ Journal entries upserted: 14
  ✓ Habits upserted: 5
  ✓ Mood logs upserted: 14
  ✓ User memory upserted (5 facts)

✅ Seed complete. Demo account is ready.

⚠️  NEXT: Run python seed/bulk_index.py to embed and index journal entries into Azure AI Search.
```

> The seed script is idempotent — re-running it upserts the same deterministic documents. No duplicates will accumulate.

---

## Step 3 — Azure AI Search

### 3.1 Create the Resource

1. Portal → **Create a resource** → search **Azure AI Search**
2. Fill in:
   - **Resource Group:** same as above
   - **Service name:** e.g., `search-jmagno-2026`
   - **Location:** same region as OpenAI
   - **Pricing tier:** `Free` (for hackathon) or `Basic`
3. Click **Review + Create → Create**

### 3.2 Get Your Keys

Open your Search resource:

- Copy the **URL** from the Overview page → `SEARCH_ENDPOINT`
- Navigate to **Keys** → copy **Primary admin key** → `SEARCH_KEY`

### 3.3 Create the Search Index

The `journal-index` must exist before running `bulk_index.py`. You can create it two ways:

---

**Option A — Script (recommended)**

Run the setup script from the repo root with `.venv` activated. It creates the index with the exact schema automatically:

```powershell
python seed/setup_search_index.py
```

Expected output:
```
🔍 MindFlow Search Index Setup
   Endpoint:   https://search-jmagno-2026.search.windows.net
   Index name: journal-index

✅ Index 'journal-index' created/updated successfully.
   Fields: ['id', 'userId', 'content', 'embedding', 'mood', 'sentiment', 'themes', 'timestamp']

⚠️  NEXT: Run python seed/bulk_index.py to embed and index journal entries.
```

> Safe to re-run — `create_or_update_index` is idempotent. If `bulk_index.py` fails due to a field type mismatch, change the affected field in the script, delete the index in the portal, and re-run this script followed by `bulk_index.py`.

---

**Option B — Portal (manual fallback)**

If you prefer to create it manually in the portal, the exact schema is:

**Index name:** `journal-index`

| Field name | Type | Attributes |
|---|---|---|
| `id` | `Edm.String` | Key, Retrievable |
| `userId` | `Edm.String` | Retrievable, Filterable |
| `content` | `Edm.String` | Retrievable, Searchable (Standard analyzer) |
| `embedding` | `Collection(Edm.Single)` | Retrievable, Searchable — Dimensions: `1536`, HNSW |
| `mood` | `Edm.String` | Retrievable, Filterable |
| `sentiment` | `Edm.String` | Retrievable, Filterable |
| `themes` | `Collection(Edm.String)` | Retrievable, Filterable, Facetable |
| `timestamp` | `Edm.DateTimeOffset` | Retrievable, Filterable, Sortable |

Steps:
1. Open your AI Search resource → **Indexes → + Add index**
2. Add each field as listed above
3. For the `embedding` field: set type to **Collection(Edm.Single)**, enable **Vector search**, set dimensions to **1536**, create a vector search profile with **HNSW** algorithm
4. Save the index


### 3.4 Index Journal Entries

After seeding Cosmos and creating the index, run the bulk indexer. This fetches the 14 journal entries from Cosmos, generates embeddings using `text-embedding-3-small-1`, and uploads them to the `journal-index`:

```powershell
python seed/bulk_index.py
```

Expected output:
```
Fetching journal entries from Cosmos...
  -> Found 14 entries
     [2026-04-24] I felt both excited and terrified reading the hackathon...
     ...

Purging stale AI Search entries...
  -> Purged: 0 old documents

Bulk-indexing into Azure AI Search...
  -> Indexed: 14/14 documents

Waiting 3s for index to settle...
Test query: 'feeling anxious'...
  -> Results returned:
     [2026-04-24] Mood: anxious | Themes: hackathon kickoff, scope anxiety...
     ...
```

> If the test query returns no results immediately, wait ~30 seconds for the index to fully settle and retry.

---

## Step 4 — Azure Functions

The Azure Functions app handles habits CRUD, mood logging, and the weekly digest timer trigger. The FastAPI backend proxies all `/habits` and `/mood` calls to it — if Functions is not running locally, those routes return `503 Habits function unreachable`.

### 4.1 Running Functions Locally

```powershell
# From the azure-functions directory
cd azure-functions
func start
```

> **Azurite not needed for local dev.** The MindFlow function app has 6 HTTP triggers (habits + mood) and 1 timer trigger (`weekly_digest`, fires Sundays 08:00 UTC). HTTP triggers do not require local storage. The timer trigger does — but you'd never run it locally. `func start` may print a storage warning on startup; this is safe to ignore. All HTTP routes will work normally.

The local host starts at `http://localhost:7071`. Verify routes are registered:
```
Functions:
    get_habits: [GET]   http://localhost:7071/api/habits
    create_habit: [POST]  http://localhost:7071/api/habits
    log_habit: [PATCH] http://localhost:7071/api/habits/{habit_id}/log
    log_mood: [POST]  http://localhost:7071/api/mood
    weekly_digest: timerTrigger
```

Update `azure-functions/local.settings.json` with your real Cosmos credentials:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "COSMOS_ENDPOINT": "https://<your-account>.documents.azure.com:443/",
    "COSMOS_KEY": "<your-primary-key>",
    "COSMOS_DB_NAME": "mindflow",
    "DEMO_USER_ID": "demo-user-001",
    "BACKEND_URL": "http://localhost:8000"
  }
}
```

> `local.settings.json` is already in `.gitignore` — never commit it with real credentials.

### 4.2 Deploying Functions to Azure (Production)

```powershell
cd azure-functions
func azure functionapp publish <your-function-app-name>
```

Set all required Application Settings in the portal (**Function App → Configuration → Application settings**):
- `COSMOS_ENDPOINT`
- `COSMOS_KEY`
- `COSMOS_DB_NAME` = `mindflow`
- `DEMO_USER_ID` = `demo-user-001`
- `BACKEND_URL` = `https://<your-backend-app>.azurewebsites.net`

---

## Environment Variables

### `backend/.env` (FastAPI backend)

Create this file at `mindfulness-agent/backend/.env`. **Never commit it** (it is in `.gitignore`).

```dotenv
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<resource-name>.openai.azure.com/
AZURE_OPENAI_KEY=<your-key>
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBED_DEPLOYMENT=text-embedding-3-small-1
AZURE_OPENAI_API_VERSION=2024-02-01

# Azure Cosmos DB
COSMOS_ENDPOINT=https://<account-name>.documents.azure.com:443/
COSMOS_KEY=<your-primary-key>
COSMOS_DB_NAME=mindflow

# Azure AI Search
SEARCH_ENDPOINT=https://<service-name>.search.windows.net
SEARCH_KEY=<your-admin-key>
SEARCH_INDEX_NAME=journal-index

# App
DEMO_USER_ID=demo-user-001
FRONTEND_URL=http://localhost:3000
WEBSITES_PORT=8000

# Azure Functions URLs (leave as localhost for local dev)
FUNCTIONS_HABIT_URL=http://localhost:7071
FUNCTIONS_MOOD_URL=http://localhost:7071
```

> `FUNCTIONS_HABIT_URL` and `FUNCTIONS_MOOD_URL` point to the same Functions host. In production, replace with your deployed Function App URL.

### `frontend/.env.local` (Next.js frontend)

Create this file at `mindfulness-agent/frontend/.env.local`. The frontend needs **only one variable** — the backend API URL. Copy from the provided example:

```dotenv
# Development (default)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Production (uncomment when deploying to Azure)
# NEXT_PUBLIC_API_URL=https://mindflow-api.azurewebsites.net
```

> The example file already exists at `frontend/.env.local.example` — just copy and rename it.

### `azure-functions/local.settings.json` (Functions host)

See [Step 4.1](#41-running-functions-locally) above. This is a separate config file for the Functions runtime and is **not** read by the FastAPI backend.

---

## Verification

### Verify OpenAI (chat) connectivity

```powershell
python -c "
import asyncio
from openai import AsyncAzureOpenAI
import os
from dotenv import load_dotenv
load_dotenv('backend/.env')

async def test():
    client = AsyncAzureOpenAI(
        api_key=os.getenv('AZURE_OPENAI_KEY'),
        azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01'),
    )
    resp = await client.chat.completions.create(
        model=os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o'),
        messages=[{'role': 'user', 'content': 'Say hello in one word'}]
    )
    print('OpenAI Chat OK:', resp.choices[0].message.content)

asyncio.run(test())
"
```

### Verify OpenAI (embeddings) connectivity

```powershell
python -c "
import asyncio
from openai import AsyncAzureOpenAI
import os
from dotenv import load_dotenv
load_dotenv('backend/.env')

async def test():
    client = AsyncAzureOpenAI(
        api_key=os.getenv('AZURE_OPENAI_KEY'),
        azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01'),
    )
    resp = await client.embeddings.create(
        input='test embedding',
        model=os.getenv('AZURE_OPENAI_EMBED_DEPLOYMENT', 'text-embedding-3-small-1'),
    )
    vec = resp.data[0].embedding
    print(f'Embeddings OK: {len(vec)}-dim vector (expected 1536)')

asyncio.run(test())
"
```

### Verify Cosmos DB connectivity

```powershell
python -c "
from azure.cosmos import CosmosClient
import os
from dotenv import load_dotenv
load_dotenv('backend/.env')

client = CosmosClient(os.getenv('COSMOS_ENDPOINT'), os.getenv('COSMOS_KEY'))
db = client.get_database_client(os.getenv('COSMOS_DB_NAME', 'mindflow'))
props = db.read()
print('Cosmos OK. Database:', props['id'])
containers = list(db.list_containers())
print('Containers:', [c['id'] for c in containers])
"
```

### Verify AI Search connectivity

```powershell
python -c "
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv
load_dotenv('backend/.env')

client = SearchClient(
    endpoint=os.getenv('SEARCH_ENDPOINT'),
    index_name=os.getenv('SEARCH_INDEX_NAME', 'journal-index'),
    credential=AzureKeyCredential(os.getenv('SEARCH_KEY')),
)
count = client.get_document_count()
print(f'Search OK: {count} documents in journal-index')
"
```

### Start the full stack locally

> **Always run uvicorn from the repo root** — not from inside `backend/`. The codebase uses `backend.xxx` import paths that only resolve correctly from the repo root. Running from `backend/` causes `ModuleNotFoundError: No module named 'backend'`.

```powershell
# Terminal 1 — Azure Functions
cd azure-functions
func start

# Terminal 2 — FastAPI backend (run from repo root, not from backend/)
python -m uvicorn backend.main:app --reload --port 8000

# Terminal 3 — Next.js frontend
cd frontend
npm run dev
```

App is available at `http://localhost:3000`.

---

## Seed Script Reference

| Script | When to run | What it does |
|---|---|---|
| `python seed/setup_search_index.py` | **First** — before anything else | Creates `journal-index` in AI Search with exact schema + HNSW vector profile |
| `python seed/seed.py` | After index is created | Creates 5 Cosmos containers + seeds 14 journals, 5 habits, 14 mood logs, 1 user, 1 memory doc |
| `python seed/bulk_index.py` | After `seed.py` | Embeds + indexes all 14 journal entries into `journal-index` |
| `python seed/cleanup.py` | **Only when re-seeding** | Deletes all docs for `demo-user-001` from habits, journal_entries, mood_logs so `seed.py` can re-run cleanly |

> **Seed scripts are demo-only.** They pre-populate a 14-day hackathon story for `demo-user-001` so judges see a rich, realistic account from the first login. In production, real users generate their own data organically — no seeding needed.

> **Re-seed workflow:** `cleanup.py` → `seed.py` → `bulk_index.py`

---

## Post-Setup Checklist

| Step | Command / Action | Expected Result |
|---|---|---|
| ✅ `backend/.env` created | — | All 16 backend vars present |
| ✅ `frontend/.env.local` created | — | `NEXT_PUBLIC_API_URL` set |
| ✅ OpenAI chat ping | See verification snippet | Returns one-word response |
| ✅ Embeddings ping | See verification snippet | 1536-dim vector returned |
| ✅ Cosmos ping | See verification snippet | `mindflow` database + 5 containers |
| ✅ Search index created | `python seed/setup_search_index.py` (or Portal) | `journal-index` with 8 fields + vector profile |
| ✅ Demo data seeded | `python seed/seed.py` | 14 journals, 5 habits, 14 mood logs, 1 user |
| ✅ Journal entries indexed | `python seed/bulk_index.py` | 14/14 documents indexed |
| ✅ Search ping | See verification snippet | ≥ 14 documents in `journal-index` |
| ✅ Functions running | `func start` | 6 HTTP routes + timer registered |
| ✅ Full stack | `uvicorn` + `func start` + `npm run dev` | App loads at `localhost:3000` |

---

## Troubleshooting

### `[ERROR] COSMOS_ENDPOINT and COSMOS_KEY must be set in backend/.env`
The seed scripts read from `backend/.env`, not the project root. Ensure the file exists at `mindfulness-agent/backend/.env`.

### OpenAI `AuthenticationError` / 401
Verify `AZURE_OPENAI_KEY` matches **Key 1** or **Key 2** in the portal under **Keys and Endpoint**. The endpoint must be the base URL only — no trailing path like `/openai/v1`.

### OpenAI returns 404 for deployment
The deployment names in `.env` (`gpt-4o`, `text-embedding-3-small-1`) must **exactly** match the names you set in Azure AI Foundry — case-sensitive.

### Embeddings vector is not 1536 dimensions
The index `embedding` field is configured for 1536 dimensions. If your embedding model produces a different size, the upload will fail. Confirm that:
- The deployment in `AZURE_OPENAI_EMBED_DEPLOYMENT` exists in Azure AI Foundry
- The deployment name **exactly matches** `text-embedding-3-small-1` (case-sensitive)
- You are not using `text-embedding-ada-002` or `text-embedding-3-large`, which produce different vector sizes

### `bulk_index.py` returns `0/14 documents indexed`
- Confirm `SEARCH_ENDPOINT` and `SEARCH_KEY` are set correctly
- Confirm the `journal-index` exists in the portal before running the script
- Confirm the index has the `embedding` field configured as a vector field (1536-dim, HNSW)

### Search returns no results immediately after indexing
The index needs 10–30 seconds to settle after an upload. Wait and re-run the test query.

### `ResourceNotFoundError` on AI Search
Your Search resource may not be fully provisioned yet — wait 1–2 minutes after creation and retry.

### Cosmos DB `Request rate too large`
Serverless Cosmos has rate limits. Retry after a few seconds. If persistent, switch to Provisioned Throughput (400 RU/s minimum).

### Azure Functions `func start` fails with import errors
Install the Functions-specific requirements:
```powershell
cd azure-functions
pip install -r requirements.txt
```

### Backend startup is slow (~10–15 seconds)
This is expected — Semantic Kernel imports at startup on Windows. Per-request latency is unaffected once the server is ready.

---

## Architecture Reference

```
backend/.env (local only, never committed)
  ├── AZURE_OPENAI_*        → backend/kernel.py → all agents (River, Lumen, Grove, Memory)
  ├── COSMOS_*              → backend/providers/cosmos_repository.py → 5 containers
  ├── SEARCH_*              → backend/providers/search_provider.py → journal RAG
  └── FUNCTIONS_*_URL       → backend/api/habits.py, mood.py → Azure Functions proxy

azure-functions/local.settings.json (Functions runtime — separate from backend/.env)
  ├── COSMOS_*              → function_app.py → habits + mood_logs containers
  └── BACKEND_URL           → weekly_digest timer → calls /insights endpoint

seed/
  ├── setup_search_index.py     ← run first — creates journal-index schema + HNSW vector profile
  ├── seed.py                   ← run second — creates Cosmos containers, uploads demo data
  ├── bulk_index.py             ← run third — embeds + indexes journals into AI Search
  └── cleanup.py                ← re-seed only — wipes demo data so seed.py can re-run cleanly
```

---

*MindFlow — Code Without Barriers Hackathon 2026*
*Participant: Jennylyn Magno · Philippines · Solo submission*
