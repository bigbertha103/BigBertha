# BUG REPORT — Session 2026-06-29

**Status** : Open  
**Date** : 2026-06-29  
**Platform** : LBB (Ubuntu server)  
**Test** : Long-run simulation (30 days) with Atelier-Mecaflux sample  
**Impact** : Critical — blocks all integration tests  

---

## Summary

5 cascading HTTP errors prevent the 30-day simulation from completing on LBB:
1. **HTTP 405** on document import → no KB ingestion
2. **Illegal Bearer token** on job execution → empty API key
3. **HTTP 405** on SENTINEL analysis → no metric scoring
4. **HTTP 404** on proposal fetch → auto-approval missing endpoint
5. **HTTP 404** on final report → cascade from BUG #3

---

## Details

### BUG #1 — HTTP 405 on POST `/api/knowledge/import`

**Symptoms** :
```
[ERROR] Import ../../../../Samples/Atelier-Mecaflux/company_profile.md : HTTP 405 : {"detail":"Method Not Allowed"}
[ERROR] Import ../../../../Samples/Atelier-Mecaflux/ressources_liens.md : HTTP 405 : {"detail":"Method Not Allowed"}
[ERROR] Import ../../../../Samples/Atelier-Mecaflux/problematiques.txt : HTTP 405 : {"detail":"Method Not Allowed"}
```

**Files** :
- **Test** : `tests/simulate_all.py:142` → `_post_multipart(f"{api_url}/api/knowledge/import", filepath)`
- **Route def** : `backend/routers/knowledge.py:22` → `@router.post("/knowledge/import")`
- **Handler** : `backend/routers/knowledge.py:28` → `async def import_documents(files: list[UploadFile])`

**Hypothesis** :
- Route not mounted in `main.py` after deployment
- OR: multipart encoding mismatch
- OR: FastAPI route registration issue on startup

**Expected behavior** : Should return `{"filename": "...", "status": "INDEXED", ...}` per file

**Workaround** : Verify route mounted via `curl -X POST http://localhost:8000/api/knowledge/import` with test file

---

### BUG #2 — Illegal header value `b'Bearer '` (empty token)

**Symptoms** :
```
Job #59 en cours….
→ [ERREUR job] Illegal header value b'Bearer '

Job #60 en cours….
→ [ERREUR job] Illegal header value b'Bearer '
```

**Files** :
- **Trigger** : `tests/simulate_all.py:666+` → Day 30 conversation messages trigger job creation
- **Root cause** : `backend/services/model_router.py:122`
  ```python
  headers = {
      "Authorization": f"Bearer {api_key.strip()}",  # ← api_key is ""
      ...
  }
  ```

**Root cause** :
- `openrouter_api_key` missing or empty in `.env` on LBB
- `model_router.py` loads config via `config.load_config()` (from DB or env)
- `api_key = config.get("openrouter_api_key", "")` returns empty string
- httpx validation rejects header value `"Bearer "` (trailing space, empty token)

**Expected behavior** : Either:
- Raise early error if no API key before constructing headers
- Skip job submission and log clear error
- Validate config on startup

**Fix required** :
1. Check if `.env` on LBB has `OPENROUTER_API_KEY` set
2. Add validation in `_call_openrouter()` before header construction (line 121)
3. Document required env vars in `.env.example`

---

### BUG #3 — HTTP 405 on POST `/api/sentinel/analyze`

**Symptoms** :
```
── SENTINEL ──────────────────────────────────
  [ERROR] SENTINEL : HTTP 405 : {"detail":"Method Not Allowed"}
```

**Files** :
- **Test** : `tests/simulate_all.py:215` → `_post_json(f"{api_url}/api/sentinel/analyze", {})`
- **Route def** : `backend/routers/sentinel.py:8` → `@router.post("/sentinel/analyze")`
- **Handler** : `backend/routers/sentinel.py:10` → `async def analyze(db=None)`

**Hypothesis** :
- Same as BUG #1 — route not mounted
- OR: Method restriction (app middleware?)

**Cascade** : Blocks SENTINEL scoring → BUG #5 downstream

---

### BUG #4 — HTTP 404 on GET `/api/learning-proposals?status=PENDING`

**Symptoms** :
```
── Auto-approbation proposals ────────────────
  [ERROR] Récupération proposals : API inaccessible : HTTP Error 404: Not Found
```

**Files** :
- **Test** : `tests/simulate_all.py:224` → `_get(f"{api_url}/api/learning-proposals?status=PENDING")`
- **Route def** : Not found in any router

**Hypothesis** :
- Endpoint not implemented in v2
- SENTINEL proposal auto-approval feature incomplete
- Should be in `backend/routers/proposals.py`

**Scope** : This is a v2 feature not yet coded. Backlog item.

---

### BUG #5 — HTTP 404 on GET `/api/sentinel/reports`

**Symptoms** :
```
Traceback (most recent call last):
  File "tests/simulate_all.py", line 525, in generate_final_report
    all_reports = _get(f"{api_url}/api/sentinel/reports")
urllib.error.HTTPError: HTTP Error 404: Not Found
```

**Files** :
- **Test** : `tests/simulate_all.py:525` → `_get(f"{api_url}/api/sentinel/reports")`
- **Route def** : `backend/routers/sentinel.py:31` → `@router.get("/sentinel/reports")`
- **Handler** : `backend/routers/sentinel.py:33` → `def list_reports()`

**Hypothesis** :
- Same as BUG #1, #3 — route mounting issue
- Cascade of BUG #3 (if SENTINEL never runs, reports endpoint also may fail)

---

## Quick Test Checklist

- [ ] On **PC (local dev)**: run `python tests/simulate_all.py --corpus-dir "Samples/Atelier-Mecaflux" --day-duration 0` → does it pass?
- [ ] On **LBB**: check `.env` has `OPENROUTER_API_KEY` set
- [ ] On **LBB**: run `curl -v -X POST -F "files=@samples/test.md" http://localhost:8000/api/knowledge/import`
- [ ] On **LBB**: check FastAPI startup logs for route registration errors
- [ ] On **LBB**: run `git status` and `git log --oneline -5` to confirm v2 deployment state

---

## Fix Priority

1. **P0 — BUG #2** : Add early validation for `openrouter_api_key` (1-line fix)
2. **P0 — BUG #1, #3, #5** : Verify route mounting on LBB (likely deployment issue, not code)
3. **P1 — BUG #4** : Implement `/api/learning-proposals?status=PENDING` endpoint (new feature)

---

## Next Steps

1. Verify `.env` on LBB
2. Check `backend/main.py` router inclusion on LBB
3. Add API key validation in `model_router.py`
4. Run simulation again from same state
5. Document findings in session closure

**Assigned to** : code review on LBB state + env config validation
