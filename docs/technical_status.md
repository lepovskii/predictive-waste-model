# Technical Status

_Last updated: 2026-06-18_

## Project Overview

This project is a **predictive waste model system** for estimating steel production WIP quality output.

The current prediction target is:

```text
wip_ton
```

The system predicts WIP at profile level, summarizes the result at daily production level, stores the result in PostgreSQL, and allows later reconciliation against actual WIP values.

The system is **not positioned as a decision support system**. It is a prediction and monitoring component for production quality analysis.

---

## Current Phase Status

| Phase | Status | Notes |
|---|---|---|
| Phase 0 - Environment Setup | Done | Docker Compose includes PostgreSQL and Redis. Backend and frontend environments are runnable locally. |
| Phase 1 - Database Schema & Migration | Done | SQLAlchemy models and Alembic migrations are available and applied. |
| Phase 2 - Model Training & Artifact | Done | Final Extra Trees model has been trained, tested, and integrated. |
| Phase 3 - FastAPI Core | Done | API accepts prediction requests, validates payloads, writes to PostgreSQL, and returns status data. |
| Phase 4 - Celery + Redis Integration | Done | Celery worker runs WIP inference asynchronously and updates database records. |
| Phase 5 - Sweeper & Fault Tolerance | Done | APScheduler sweeper marks stale PROCESSING logs as FAILED. Manual and automatic stale-task scenarios were verified. |
| Backend Adapter Layer | Done | CSV preview adapter supports raw GYS company format and canonical process CSV format. |
| Batch Prediction Endpoint | Done | `/predict/batch` accepts multiple normalized prediction payloads and returns per-date results. |
| Reconciliation Endpoint | Done | `/reconcile` stores actual WIP/prime values and updates status to RECONCILED when valid. |
| Phase 6 - Frontend Next.js | Done | Main UI flows are implemented: overview, upload, batch prediction, manual prediction, history, detail, and reconciliation. |
| Phase 7 - Full Docker Stack | Pending | FastAPI, Celery, and Next.js still need production/staging Docker service definitions. |
| Phase 8 - Documentation & Thesis Prep | In Progress | Technical status and ML experiment notes are maintained for thesis reporting. |

---

## Current Architecture

Current single-day prediction flow:

```text
Frontend / API Client
-> POST /predict
-> FastAPI validates payload with Pydantic
-> FastAPI inserts daily_production_logs and daily_profile_details
-> FastAPI dispatches Celery task predict_wip(task_id)
-> Celery loads final pipeline.pkl
-> Celery predicts WIP per profile
-> Celery updates predicted_wip_ton, estimasi_wip_total, and estimasi_prime
-> GET /status/{task_id} returns prediction result
```

Current CSV batch flow:

```text
Frontend upload page
-> POST /adapter/preview
-> CSV adapter detects and normalizes file
-> frontend shows preview status, issues, and normalized payloads
-> POST /predict/batch
-> FastAPI inserts accepted production dates
-> Celery runs one prediction task per accepted date
-> frontend polls /status/{task_id}
-> result table displays DRAFT/FAILED/RECONCILED states
```

Current reconciliation flow:

```text
Prediction detail page
-> user inputs actual WIP and optional actual prime
-> POST /reconcile
-> backend validates actual values
-> backend updates aktual_wip, aktual_prime, absolute error, and needs_retraining flag
-> status changes to RECONCILED
```

High-level architecture:

```text
Next.js Frontend
-> FastAPI
-> PostgreSQL
-> Celery Worker
-> ML Pipeline Artifact
-> PostgreSQL
-> Next.js status/result views
```

Runtime infrastructure:

```text
PostgreSQL = source of truth
Redis = Celery broker and result backend
APScheduler = stale PROCESSING row sweeper
```

---

## Main Model Artifact

The active model artifact is:

```text
ml_training/artifacts/wip_final_jan_oct_extra_trees/pipeline.pkl
```

Model:

```text
ExtraTreesRegressor
```

Target:

```text
wip_ton
```

Final test result on Nov-Dec:

| Metric | Model | Baseline Mean | Baseline Median |
|---|---:|---:|---:|
| RMSE | 177.37 | 200.97 | 217.02 |
| MAE | 110.00 | 139.61 | 147.58 |
| R2 | 0.102 | -0.153 | -0.345 |

Interpretation:

**The model outperformed both mean and median baselines** on untouched Nov-Dec final test data.

However, the model still tends to underpredict extreme WIP values. This limitation is documented and should be explained during evaluation.

---

## Backend Modules

Current backend modules:

```text
backend/app/main.py
backend/app/api/routes.py
backend/app/api/adapter_routes.py
backend/app/schemas/prediction.py
backend/app/schemas/adapter.py
backend/app/schemas/reconciliation.py
backend/app/services/production_service.py
backend/app/services/ml_service.py
backend/app/services/csv_adapter_service.py
backend/app/services/reconciliation_service.py
backend/app/services/sweeper_service.py
backend/app/tasks/prediction_tasks.py
backend/app/core/database.py
backend/app/core/celery_app.py
backend/app/core/config.py
backend/app/core/scheduler.py
backend/app/models/waste.py
```

Module responsibilities:

| Module | Responsibility |
|---|---|
| `main.py` | Creates the FastAPI app, registers API routes, and starts/stops scheduler lifespan |
| `routes.py` | Defines prediction, batch, status, history, and reconciliation endpoints |
| `adapter_routes.py` | Defines `/adapter/preview` CSV upload endpoint |
| `prediction.py` | Defines prediction request and response validation schemas |
| `adapter.py` | Defines adapter preview response contract and issue reporting schemas |
| `reconciliation.py` | Defines actual WIP reconciliation request and response schemas |
| `production_service.py` | Handles database insert, duplicate checks, and prediction history lookup |
| `ml_service.py` | Loads model artifact and prepares model input DataFrame |
| `csv_adapter_service.py` | Parses raw/canonical CSV files into normalized prediction payloads |
| `reconciliation_service.py` | Applies actual values and calculates reconciliation result |
| `sweeper_service.py` | Finds stale PROCESSING rows and marks them FAILED |
| `prediction_tasks.py` | Defines Celery task `predict_wip` |
| `database.py` | Defines SQLAlchemy engine and session |
| `celery_app.py` | Defines Celery app using Redis |
| `config.py` | Reads environment variables |
| `scheduler.py` | Runs APScheduler background job for stale task sweeping |
| `waste.py` | Defines SQLAlchemy database models |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check API availability |
| POST | `/predict` | Accept one normalized production payload, insert database rows, and dispatch Celery task |
| POST | `/predict/batch` | Accept multiple normalized production payloads and submit each date independently |
| GET | `/status/{task_id}` | Return processing or prediction status |
| GET | `/predictions` | Return paginated prediction history with optional filters |
| POST | `/reconcile` | Store actual WIP values and reconcile prediction results |
| POST | `/adapter/preview` | Upload CSV and preview normalized prediction payloads without inserting database rows |

---

## CSV Adapter Contract

The adapter supports two detected formats:

| Format | Meaning |
|---|---|
| `gys_lsm_daily_prod_report` | Raw company daily production report export |
| `canonical_process_csv_v1` | Cleaner canonical CSV with process feature columns |

Adapter preview response includes:

```text
contract_version
source_file_name
detected_format
preview_status
is_valid_for_prediction
summary
normalized_payloads
issues
required_columns_missing
ignored_columns
```

Preview status meaning:

| Status | Meaning |
|---|---|
| `VALID` | CSV is safe for prediction without warning |
| `WARNING` | CSV is usable, but adapter found non-blocking issues |
| `INVALID` | CSV cannot be used for prediction |

The adapter intentionally ignores leakage/output columns such as:

```text
wip_ton
class_b_ton
reject_ton
miss_roll_ton
transfer_to_warehouse_ton
finish good / dispatch / stock columns
```

Supported adapter behavior:

```text
auto-detect delimiter: comma, semicolon, tab
read ragged CSV rows with inconsistent column counts
normalize raw GYS multi-row header by index mapping
normalize canonical headers with aliases
normalize dates such as 2-Dec-25 and 2025-12-02
normalize numeric values using US and Indonesian separators
skip Shutdown rows as INFO
skip footer artifacts such as TOTAL, blank rows, 1, and #REF! as INFO
default selected optional missing features to 0 with WARNING
flag energy total mismatch with WARNING
reject missing hard-required feature columns
```

Hard-required fields:

```text
production_date
profile_name
raw_material_ton
production_ton
material_pcs
production_pcs
total_hrs
availables_hrs
downtime_total_min
gas_total_day_nm3
electricity_total_kwh
```

---

## Frontend Modules

Current frontend pages:

```text
frontend/src/app/page.tsx
frontend/src/app/upload/page.tsx
frontend/src/app/manual/page.tsx
frontend/src/app/predictions/page.tsx
frontend/src/app/predictions/[taskId]/page.tsx
```

Main frontend components:

```text
frontend/src/components/layout/
frontend/src/components/upload/
frontend/src/components/manual/
frontend/src/components/prediction/
frontend/src/components/common/
```

Implemented frontend flows:

| Flow | Status | Notes |
|---|---|---|
| Overview dashboard | Done | Shows system purpose, model snapshot, quick actions, workflow, and academic disclaimer |
| CSV upload preview | Done | Uploads CSV to `/adapter/preview` and shows VALID/WARNING/INVALID results |
| Batch prediction | Done | Submits normalized payloads to `/predict/batch` |
| Prediction polling | Done | Polls `/status/{task_id}` until final status |
| Prediction results table | Done | Displays output, estimated WIP, estimated prime, profile count, and status |
| Manual prediction form | Done | Allows direct JSON-compatible production input without CSV |
| Prediction history | Done | Shows paginated history from `/predictions` with status/date filters |
| Prediction detail page | Done | Shows daily summary, profile-level predictions, and reconciliation form |
| Reconciliation form | Done | Sends actual WIP/prime to `/reconcile` |
| Responsive layout | Done | Desktop sidebar and mobile top navigation are implemented |

Frontend design direction:

```text
clean industrial operations dashboard
warm neutral background
green/terracotta accent palette
monospace value text for numeric/status data
clear operational cards and tables
```

---

## Database Tables

### daily_production_logs

Stores one production day log.

Important columns:

| Column | Meaning |
|---|---|
| `id` | Primary key |
| `production_date` | Unique production date |
| `status` | Processing state |
| `task_id` | Celery/API tracking ID |
| `total_output_ton` | Sum of production output from all profiles |
| `estimasi_wip_total` | Total predicted WIP from all profiles |
| `estimasi_manual_class_b` | Manual class B estimate |
| `estimasi_manual_reject` | Manual reject estimate |
| `estimasi_prime` | Estimated prime output |
| `aktual_wip` | Actual WIP after reconciliation |
| `aktual_prime` | Actual prime after reconciliation |
| `needs_retraining` | Flag for future model drift/retraining |
| `created_at` | Creation timestamp |
| `updated_at` | Update timestamp |

### daily_profile_details

Stores profile-level production details and prediction result.

Important columns:

| Column | Meaning |
|---|---|
| `log_id` | Foreign key to daily production log |
| `detail_seq` | Profile sequence in request |
| `profile_name` | Steel profile name |
| `raw_material_ton` | Raw material tonnage |
| `production_ton` | Production tonnage |
| `material_pcs` | Material pieces |
| `production_pcs` | Production pieces |
| `total_hrs` | Total hours |
| `availables_hrs` | Available hours |
| `setup_time` | Setup time |
| `program_stop_min` | Program stop duration |
| `stand_change` | Stand change duration |
| `production_stop_min` | Production stop duration |
| `mechanic_stop_min` | Mechanic stop duration |
| `electric_stop_min` | Electric stop duration |
| `roll_shop_stop_min` | Roll shop stop duration |
| `test_rolling_stop_min` | Test rolling duration |
| `trial_rolling_stop_min` | Trial rolling duration |
| `others_stop_min` | Other stop duration |
| `downtime_total_min` | Total downtime |
| `rolling_hot_hrs` | Rolling hot hours |
| `idle_hrs` | Idle hours |
| `rolling_hrs` | Rolling hours |
| `gas_total_day_nm3` | Total daily gas consumption |
| `kv_20` | KV 20 electricity consumption |
| `kv_33` | KV 33 electricity consumption |
| `electricity_total_kwh` | Total electricity consumption |
| `predicted_wip_ton` | Model prediction result |
| `actual_wip_ton` | Actual WIP after reconciliation |

---

## Status Flow

Implemented states:

```text
PROCESSING -> DRAFT
PROCESSING -> ANOMALY
PROCESSING -> FAILED
DRAFT -> RECONCILED
ANOMALY -> RECONCILED
```

Status meaning:

| Status | Meaning |
|---|---|
| `PROCESSING` | Request has been accepted and Celery task should process it |
| `DRAFT` | Prediction completed successfully and awaits actual reconciliation |
| `ANOMALY` | Predicted WIP exceeds total production output |
| `FAILED` | Task dispatch, prediction, or stale processing failure |
| `RECONCILED` | Actual WIP/prime values have been stored and compared with prediction |

Sweeper protection:

```text
PROCESSING older than PROCESSING_TIMEOUT_MINUTES -> FAILED
```

---

## Validation Rules

The prediction API rejects:

```text
profile_name = Shutdown
empty profile_name
duplicate profile_name in one request
duplicate production_date inside batch request
production_ton <= 0
raw_material_ton <= 0
material_pcs <= 0
production_pcs <= 0
negative numeric process values
empty profiles list
unknown extra fields
duplicate production_date in database
```

The reconciliation API rejects:

```text
duplicate production_date in one reconciliation request
negative actual_wip_ton
negative actual_prime_ton
duplicate profile_name inside reconciliation profiles
profile-level actual WIP total that does not match daily actual_wip_ton
reconciliation for missing production_date
reconciliation for FAILED/PROCESSING rows
```

The adapter rejects or marks invalid:

```text
unsupported CSV format
missing hard-required columns
empty file
non-CSV file extension
file larger than 5 MB
no accepted production rows
invalid PredictRequest payload after normalization
```

---

## Current Verified Flows

### Local Integration Test - 2026-06-18

Integration test was run with local services active:

```text
PostgreSQL
Redis
FastAPI
Celery Worker
Next.js frontend dev server
```

Happy-path result:

| Area | Result |
|---|---|
| Backend health | `ok` |
| Frontend dev server | HTTP `200` |
| `POST /predict` | Accepted and completed |
| Celery inference | Completed and updated database |
| `GET /status/{task_id}` | Returned DRAFT result |
| `POST /predict/batch` | 2 items accepted |
| Batch polling | 2 tasks completed as DRAFT |
| `GET /predictions` | Returned paginated history |
| `POST /reconcile` | Updated one prediction to RECONCILED |
| `POST /adapter/preview` | Dummy CSV returned VALID |

Verified test records:

| Production Date | Final Status | Notes |
|---|---|---|
| 2031-05-19 | `RECONCILED` | Single prediction then reconciliation |
| 2031-05-20 | `DRAFT` | Batch prediction item |
| 2031-05-21 | `DRAFT` | Batch prediction item |

Negative-path result:

| Case | Expected Result | Verified Result |
|---|---|---|
| Duplicate production_date | HTTP `409` | Passed |
| Profile name `Shutdown` | HTTP `422` | Passed |
| Missing task id | HTTP `404` | Passed |
| Invalid CSV adapter preview | `INVALID`, `is_valid_for_prediction=false` | Passed |

### Build and Code Health

Frontend checks:

```text
npm.cmd run lint
npx.cmd tsc --noEmit
npm.cmd run build
```

Result:

```text
passed
```

Backend check:

```text
.\venv\Scripts\python.exe -m compileall app
```

Result:

```text
passed
```

Next.js production build routes:

```text
/
/manual
/upload
/predictions
/predictions/[taskId]
```

### Previously Verified Backend Flows

Single prediction flow was verified before frontend completion:

```text
POST /predict
-> FastAPI inserted data into PostgreSQL
-> Celery task predict_wip was dispatched automatically
-> Celery worker loaded pipeline.pkl
-> Celery predicted WIP per profile
-> Celery updated PostgreSQL
-> GET /status/{task_id} returned DRAFT status and predicted_wip_ton values
```

Sweeper flow was verified:

```text
create PROCESSING row
-> manually move updated_at to older than timeout
-> run sweeper
-> row status changed to FAILED
```

Automatic scheduler flow was verified:

```text
create PROCESSING row
-> leave row stale
-> APScheduler job runs automatically
-> row status changed to FAILED
```

Verified failed task example:

```text
task_id = 23faad8a-2a47-4bd1-ae41-40e8aa4edfa5
```

---

## Runtime Commands

### Start Docker Services

```powershell
docker compose up -d
```

### Start FastAPI

```powershell
cd backend
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

### Start Celery Worker

```powershell
cd backend
.\venv\Scripts\celery.exe -A app.core.celery_app.celery_app worker --loglevel=info --pool=solo
```

### Start Frontend

```powershell
cd frontend
npm.cmd run dev
```

### Check Alembic Current Revision

```powershell
cd backend
.\venv\Scripts\alembic.exe current
```

Expected current revision:

```text
f3c9a2d8b741
```

---

## Environment Variables

Backend environment file:

```text
backend/.env
```

Example variables:

```env
BACKEND_PORT=8000
SECRET_KEY=change-me
MODEL_ARTIFACT_PATH=ml_training/artifacts/wip_final_jan_oct_extra_trees/pipeline.pkl

POSTGRES_USER=skripsi_user
POSTGRES_PASSWORD=change-me
POSTGRES_DB=predictive_waste
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379

SWEEPER_ENABLED=true
SWEEPER_INTERVAL_SECONDS=60
PROCESSING_TIMEOUT_MINUTES=10
```

Frontend environment file:

```text
frontend/.env
```

Example variable:

```env
BACKEND_API_URL=http://127.0.0.1:8000
```

Important note:

`MODEL_ARTIFACT_PATH` is relative to the project root:

```text
predictive-waste-model/
```

Correct path:

```text
ml_training/artifacts/wip_final_jan_oct_extra_trees/pipeline.pkl
```

---

## Repository Hygiene

Current repository preparation:

```text
dataset CSV files were moved out of ml_training
archive_artifacts is local backup and should not be committed
.env files should not be committed
model artifacts are currently included for reproducible local inference
```

Recommended `.gitignore` protection:

```gitignore
**/.env
archive_artifacts/
ml_training/*.csv
```

Public repository caution:

```text
The repository includes ML artifacts and experiment prediction CSV files.
For company-related data governance, private repository is safer than public repository.
```

---

## Deployment Direction

Recommended staging deployment for usability testing:

```text
single low-cost VPS
Docker Compose
PostgreSQL container or managed PostgreSQL
Redis container
FastAPI container
Celery worker container
Next.js container
reverse proxy with HTTPS if public access is needed
```

Vercel-only deployment is not recommended for the full system because the project needs:

```text
persistent backend service
Celery worker
Redis broker
PostgreSQL
ML artifact loading
CSV upload handling
background processing
```

Vercel can be used for frontend only, but for thesis usability testing, a single VPS with Docker Compose is simpler and closer to the project architecture.

---

## Current Constraints

The system currently supports:

```text
normalized JSON prediction payloads
batch prediction payloads
raw GYS company CSV preview
canonical process CSV preview
multi-date CSV preview output
profile-level prediction
PostgreSQL persistence
Celery async inference
stale PROCESSING failure protection
manual actual WIP reconciliation
frontend upload, manual input, history, detail, and reconcile pages
```

The system does not yet support:

```text
full production Docker Compose app stack
role-based authentication
real company user management
automatic retraining pipeline
automatic database update from adapter preview without user confirmation
arbitrary unknown company CSV layouts outside known GYS/canonical patterns
```

---

## Known Limitations

Technical limitations:

```text
Automated pytest tests are not implemented yet.
FastAPI, Celery, and frontend are not yet containerized as production app services.
Adapter submit flow still requires frontend/client confirmation before /predict/batch.
No authentication or RBAC is implemented yet.
```

ML limitations:

```text
Dataset size is limited.
Extreme WIP values are difficult to predict.
The model tends to underpredict very high WIP cases.
The model predicts WIP only, not reject, class B, miss roll, or transfer to warehouse.
```

Adapter limitations:

```text
Adapter supports known raw GYS layout and canonical CSV aliases, not arbitrary unknown company formats.
If hard-required process features are missing, CSV is marked INVALID.
If optional features are missing, adapter may default them to 0 with WARNING.
Energy consistency checks are heuristic and intended as warning only.
```

---

## Next Phase

Next planned phase:

```text
Phase 7 - Full Docker Compose Stack and Deployment Preparation
```

Recommended next work:

```text
create Dockerfile for FastAPI
create Dockerfile for Celery worker or reuse backend image
create Dockerfile for Next.js frontend
update docker-compose.yml with application services
configure health checks and service dependencies
test docker compose up end-to-end
prepare VPS staging deployment plan
prepare usability testing checklist for company staff
```

Before deployment, recommended manual browser smoke test:

```text
open frontend
upload CSV
preview adapter result
submit batch prediction
wait for prediction results
open prediction detail
submit reconciliation
verify history/filter result
```

---

## Summary

Current system status:

```text
FastAPI Core: working
Database Schema: working
Alembic Migration: working
Celery Worker: working
ML Artifact Loading: working
Async Prediction Flow: working
Sweeper & Fault Tolerance: working
CSV Adapter Preview: working
Batch Prediction Endpoint: working
Reconciliation Endpoint: working
Frontend Main Flow: working
Frontend Production Build: passing
Local Integration Test: passing
```

The project is ready to proceed to:

```text
manual browser smoke testing
full Docker Compose stack
staging deployment preparation
usability testing with company staff
```
