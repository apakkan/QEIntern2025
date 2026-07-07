# Local running & verification

How to run the service and how to exercise the agent pipeline end-to-end,
including the one environment quirk (P7) to be aware of on the shared dev VM.

## Running the service (normal environments)

The shippable entrypoint is the FastAPI app in `api_server.py`:

```bash
uvicorn api_server:app --host 127.0.0.1 --port 8000
```

It needs a populated `.env` (Mistral LLM + embeddings, Neon Postgres with the
`vector` extension, Neo4j). On startup it creates tables; it does **not** pull
qTest. To ingest real qTest requirements first:

```bash
python3 init_db.py        # pulls qTest requirements -> Postgres (+ embeddings)
```

> Note: `main.py` and the Docker `CMD` / compose `command:` run demo/test
> scripts, **not** the server. `uvicorn api_server:app` is the real entrypoint.

## P7 — the dev-VM quirk (environment, not a product bug)

On the shared sandbox VM this project is developed in, a **backgrounded or
long-running `uvicorn` process gets SIGTERM'd** (the shell reports exit code
144). This is the VM's process management reaping detached/long jobs — it is
**not** a defect in the application. On any normal host (a laptop, a container
with proper process supervision, a deployment) the server runs fine.

Two practical consequences on this VM:

1. **Don't rely on a backgrounded server for verification.** Starting `uvicorn &`
   and then making a slow request (e.g. an agent endpoint that takes minutes)
   tends to be killed mid-request.
2. **Verify the pipeline in-process instead** (below) — this is how P1–P5 were
   validated and is the reliable path here.

## In-process verification (the reliable pattern here)

Call the service functions directly, with the repo root on `PYTHONPATH`. This
exercises the real agents + real database without going through the HTTP server:

```bash
cd /path/to/QEIntern2025
PYTHONPATH=$PWD python3 -c "
from database.qtest_db import connect_db
from database.rag_utils import find_related_requirements
from gpt_agent import get_or_compute_risk, get_or_compute_testcases
conn = connect_db()
RID = 22895830                                   # any ingested requirement id
print('related:', find_related_requirements(conn, RID, top_k=5))
print('risk:',    get_or_compute_risk(conn, RID))          # computes + caches
print('tests:',   len(get_or_compute_testcases(conn, RID))) # computes + caches
conn.close()
"
```

Because risk and test-cases are cached (see below), a second call to either is
served from the database with no LLM call.

### Rate limits

The Mistral free tier throttles rapid-fire calls (~1 request/second). When
driving several agents in a row, **space the calls out** (a short sleep between
them) to avoid `429 Rate limit exceeded`. The limit is a short burst window, not
a daily cap — it recovers within a minute of idling.

## Caching model (why repeat views are stable)

Agent-derived results are cached in `central_vectors`, keyed by
`(story_number, source)`:

| Data | `source` | Endpoint | Recompute |
|------|----------|----------|-----------|
| Risk | `risk_agent` | `GET /requirements/{id}/risk` | call the endpoint on a cache miss |
| Test cases | `test_agent` | `GET /requirements/{id}/test-cases` | `?regenerate=true` |
| Related stories | — (live vector query) | `GET /requirements/{id}/related-stories` | always live (no LLM) |

A plain `GET /requirements/{id}` never triggers an LLM call — it shows cached
risk or `"Not assessed"`.
