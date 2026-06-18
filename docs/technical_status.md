# Technical Status

_Last updated: 2026-06-10_

## Project Overview

This project is a **predictive waste model system** for estimating steel production WIP quality output.

The system currently focuses on predicting:

```text
wip_ton
```

The prediction result is stored per production profile and summarized at daily production level.

The system is **not positioned as a decision support system**, but as a prediction component for production quality monitoring.

---

## Current Phase Status

| Phase | Status | Notes |
|---|---|---|
| Phase 0 - Environment Setup | Done | Docker Compose includes PostgreSQL and Redis. Backend and frontend scaffold exist. |
| Phase 1 - Database Schema & Migration | Done | SQLAlchemy models and Alembic migrations are available and applied. |
| Phase 2 - Model Training & Artifact | Done | Final Extra Trees model has been trained and tested. |
| Phase 3 - FastAPI Core | Done | API can accept prediction requests and write to PostgreSQL. |
| Phase 4 - Celery + Redis Integration | Done | Celery worker runs WIP prediction asynchronously and updates database. |
| Phase 5 - Sweeper & Fault Tolerance | Done | APScheduler sweeper marks stale PROCESSING logs as FAILED. Manual and automatic stale-task scenarios were verified. |
| Backend Adapter Layer | Done | CSV preview adapter supports raw GYS company format and canonical CSV format. |
| Batch Prediction Endpoint | Done | `/predict/batch` accepts multiple normalized prediction payloads and returns per-date results. |
| Phase 6 - Frontend | Pending | Next.js scaffold exists, but app UI is not implemented yet. |
| Phase 7 - Full Docker Stack | Pending | FastAPI, Celery, and frontend are not yet containerized as application services. |
| Phase 8 - Documentation & Thesis Prep | In Progress | ML experiment artifacts and technical notes are available and being updated. |

---

## Current Architecture

Current single-day prediction flow:

```text
POST /predict
-> FastAPI validates payload with Pydantic
-> FastAPI inserts daily_production_logs and daily_profile_details
-> FastAPI dispatches Celery task predict_wip(task_id)
-> Celery loads final pipeline.pkl
-> Celery predicts WIP per profile
-> Celery updates predicted_wip_ton, estimasi_wip_total, and estimasi_prime
-> GET /status/{task_id} returns prediction result
```

Current CSV adapter preview flow:

```text
POST /adapter/preview
-> FastAPI receives CSV upload
-> CSV adapter detects file format
-> CSV adapter normalizes headers, dates, numeric values, and production rows
-> CSV adapter ignores output/leakage columns
-> CSV adapter returns normalized_payloads compatible with /predict or /predict/batch
```

Current batch prediction flow:

```text
POST /predict/batch
-> FastAPI receives multiple PredictRequest items
-> each production_date is inserted independently
-> each accepted item dispatches one Celery task
-> response returns ACCEPTED, DUPLICATE, or FAILED per production_date
```

High-level architecture:

```text
Client / Swagger UI / Future Frontend
-> FastAPI
-> PostgreSQL
-> Celery Worker
-> ML Pipeline Artifact
-> PostgreSQL
-> GET /status/{task_id}
```

Redis is used as:

```text
Celery broker
Celery result backend
```

APScheduler is used inside FastAPI for:

```text
stale PROCESSING row sweeping
```

Prediction results are persisted directly to PostgreSQL.

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

However, the model still tends to underpredict extreme WIP values.

---

## Backend Modules

Current backend modules:

```text
backend/app/main.py
backend/app/api/routes.py
backend/app/api/adapter_routes.py
backend/app/schemas/prediction.py
backend/app/schemas/adapter.py
backend/app/services/production_service.py
backend/app/services/ml_service.py
backend/app/services/csv_adapter_service.py
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
| `routes.py` | Defines `/health`, `/predict`, `/predict/batch`, and `/status/{task_id}` endpoints |
| `adapter_routes.py` | Defines `/adapter/preview` CSV upload endpoint |
| `prediction.py` | Defines prediction request and response validation schemas, including batch schemas |
| `adapter.py` | Defines adapter preview response contract and issue reporting schemas |
| `production_service.py` | Handles database insert and lookup logic |
| `ml_service.py` | Loads model artifact and prepares model input DataFrame |
| `csv_adapter_service.py` | Parses raw/canonical CSV files into normalized prediction payloads |
| `sweeper_service.py` | Finds stale PROCESSING rows and marks them FAILED |
| `prediction_tasks.py` | Defines Celery tasks including `predict_wip` |
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
| POST | `/adapter/preview` | Upload CSV and preview normalized prediction payloads without inserting database rows |

---

## API Flow

### POST /predict

The endpoint receives one normalized JSON payload.

It performs:

```text
Pydantic validation
-> duplicate production_date check
-> insert daily_production_logs
-> insert daily_profile_details
-> dispatch predict_wip task to Celery
-> return 202 Accepted
```

Initial status:

```text
PROCESSING
```

If Celery dispatch succeeds, the worker processes the prediction asynchronously.

If Celery dispatch fails, the log is marked as:

```text
FAILED
```

### POST /predict/batch

The endpoint receives:

```text
items: list[PredictRequest]
```

It performs:

```text
validate duplicate production_date inside batch
-> process each item independently
-> insert accepted production dates
-> dispatch one Celery task per accepted date
-> return per-date result
```

Possible item results:

| Result | Meaning |
|---|---|
| `ACCEPTED` | Row was inserted and Celery task was dispatched |
| `DUPLICATE` | Production date already exists in database |
| `FAILED` | Row was inserted but Celery dispatch failed |

Batch endpoint uses partial success behavior.

Example:

```text
12 items submitted
10 accepted
2 duplicate
0 failed
```

### GET /status/{task_id}

This endpoint returns:

```text
task_id
status
production_date
total_output_ton
estimasi_wip_total
estimasi_prime
profile-level predicted_wip_ton
```

### POST /adapter/preview

The endpoint receives one CSV file upload.

It performs:

```text
file extension validation
-> file size validation
-> CSV parsing
-> format detection
-> column mapping
-> value normalization
-> row filtering
-> PredictRequest validation
-> returns normalized_payloads and adapter issues
```

The endpoint is read-only:

```text
no database insert
no Celery dispatch
no prediction execution
```

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
DRAFT -> RECONCILED (reserved for future reconciliation)
ANOMALY -> RECONCILED (reserved for future reconciliation)
```

Status meaning:

| Status | Meaning |
|---|---|
| `PROCESSING` | Request has been accepted and Celery task should process it |
| `DRAFT` | Prediction completed successfully |
| `ANOMALY` | Predicted WIP exceeds total production output |
| `FAILED` | Task dispatch, prediction, or stale processing failure |
| `RECONCILED` | Reserved for future actual CSV reconciliation |

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

The adapter skips as non-blocking INFO:

```text
Shutdown rows
footer rows
TOTAL rows
blank artifact rows
#REF! artifact rows
```

The adapter may warn but still allow prediction:

```text
optional feature defaulted to 0
energy total mismatch
valid CSV with minor non-blocking issues
```

The database enforces:

```text
production_date unique
profile_name != Shutdown
production_ton >= 0
raw_material_ton >= 0
predicted_wip_ton >= 0 or NULL
actual_wip_ton >= 0 or NULL
```

---

## Current Verified Flows

### Single Prediction Flow

The following end-to-end flow has been verified:

```text
POST /predict
-> FastAPI inserted data into PostgreSQL
-> Celery task predict_wip was dispatched automatically
-> Celery worker loaded pipeline.pkl
-> Celery predicted WIP per profile
-> Celery updated PostgreSQL
-> GET /status/{task_id} returned DRAFT status and predicted_wip_ton values
```

Example verified result:

| Production Date | Status | Total Output | Estimated WIP | Estimated Prime |
|---|---|---:|---:|---:|
| 2026-01-02 | DRAFT | 1251.82 | 364.55 | 887.27 |
| 2026-01-03 | DRAFT | 1251.82 | 364.55 | 887.27 |

Example profile-level prediction:

| Profile | Production Ton | Predicted WIP |
|---|---:|---:|
| IWF 250x125 | 771.72 | 186.28 |
| IWF 200x100 | 480.10 | 178.27 |

### Sweeper Flow

Manual stale-row test was verified:

```text
create PROCESSING row
-> manually move updated_at to older than timeout
-> run sweeper
-> row status changed to FAILED
```

Automatic scheduler test was verified:

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

Current stable sweeper config:

```env
SWEEPER_ENABLED=true
SWEEPER_INTERVAL_SECONDS=60
PROCESSING_TIMEOUT_MINUTES=10
```

### Adapter Preview Flow

Verified raw GYS default company files:

| File | Detected Format | Status | Valid | Accepted Rows | Accepted Days | Warning | Error |
|---|---|---|---:|---:|---:|---:|---:|
| November 2025 raw GYS | `gys_lsm_daily_prod_report` | `VALID` | true | 17 | 12 | 0 | 0 |
| December 2025 raw GYS | `gys_lsm_daily_prod_report` | `VALID` | true | 7 | 5 | 0 | 0 |

Verified canonical CSV examples:

| File | Detected Format | Status | Valid | Notes |
|---|---|---|---:|---|
| `gys_dummy.csv` | `canonical_process_csv_v1` | `WARNING` | true | Some optional features defaulted to 0 |
| `dataset_completed - new_completed_wip_ton.csv` | `canonical_process_csv_v1` | `WARNING` | true | 99 accepted rows, 1 energy mismatch warning |
| `janjan.csv` | `canonical_process_csv_v1` | `INVALID` | false | Missing required columns: `availables_hrs`, `material_pcs`, `production_pcs`, `total_hrs` |

---

## Runtime Services

Current runtime dependencies:

| Service | Purpose |
|---|---|
| PostgreSQL | Main persistent database |
| Redis | Celery broker and result backend |
| FastAPI | API gateway |
| Celery Worker | Background ML inference worker |
| APScheduler | In-process scheduled sweeper job |

Local runtime commands:

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

### Check Alembic Current Revision

```powershell
cd backend
.\venv\Scripts\alembic.exe current
```

Expected current revision:

```text
f3c9a2d8b741
```

### Check Registered FastAPI Routes

```powershell
cd backend
.\venv\Scripts\python.exe -B -c "from app.main import app; [print(route.path) for route in app.routes]"
```

Implemented business routes:

```text
/health
/predict
/predict/batch
/status/{task_id}
/adapter/preview
```

---

## Environment Variables

Backend environment file:

```text
backend/.env
```

Important variables:

```env
BACKEND_PORT=8000
SECRET_KEY=backendskripsi
MODEL_ARTIFACT_PATH=ml_training/artifacts/wip_final_jan_oct_extra_trees/pipeline.pkl

POSTGRES_USER=skripsi_ardy
POSTGRES_PASSWORD=ardy12345
POSTGRES_DB=predictive_waste
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379

SWEEPER_ENABLED=true
SWEEPER_INTERVAL_SECONDS=60
PROCESSING_TIMEOUT_MINUTES=10
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

## Dependencies

Important backend dependencies:

```text
fastapi
uvicorn
sqlalchemy
alembic
psycopg2-binary
celery
redis
pydantic
pydantic-settings
pandas
numpy
scikit-learn
xgboost
joblib
python-dotenv
httpx
apscheduler
python-multipart
```

`python-multipart` is required for CSV upload via FastAPI `UploadFile`.

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
```

The system does not yet support:

```text
actual WIP reconciliation upload
automatic database update from adapter preview without user confirmation
frontend CSV preview UI
frontend batch submit UI
full Dockerized FastAPI/Celery/frontend app services
```

---

## Known Limitations

Current technical limitations:

```text
Reconciliation endpoint is not implemented yet.
Automated pytest tests are not implemented yet.
Frontend is not integrated yet.
FastAPI, Celery, and frontend are not yet containerized as app services.
Adapter submit flow still requires frontend or client to call /predict/batch after preview.
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
Phase 6 - Frontend Next.js Integration
```

Frontend goals:

```text
CSV upload page
adapter preview table
accepted/skipped/warning/error summary
batch submit to /predict/batch
status polling via /status/{task_id}
dashboard for prediction results
basic role separation for QA/QC and PPIC if needed
```

Before or during frontend work, recommended supporting work:

```text
update technical documentation
add endpoint usage examples
add minimal backend tests for adapter and batch routes
prepare demo CSV files for happy path and warning path
```

---

## Summary

Current backend status:

```text
FastAPI Core: working
Database Schema: working
Alembic Migration: working
Celery Worker: working
ML Artifact Loading: working
Async Prediction Flow: working
Sweeper & Fault Tolerance: working
CSV Adapter Preview: working
Batch Prediction Endpoint: implemented
```

The project is ready to proceed to:

```text
technical documentation finalization
frontend implementation
```
