# Intelligent Financial Fraud Detection Platform

A distributed web application for managing and monitoring financial transactions, with a machine-learning model that scores every transaction for fraud risk and a human review workflow for ambiguous cases.

> **Project status: work in progress** (last updated 2026-11-01).
> The data model, API contract, architecture and the **machine-learning part are complete and tested**. The Spring Boot backend, the Angular frontend and the Docker setup are still being built. See [Progress](#progress) for the exact state.

This is a **portfolio / learning project**. It uses fictional accounts and a synthetic dataset. It is not a production banking system (see [Limitations](#limitations)).

---

## Table of contents

1. [Progress](#progress)
2. [Architecture](#architecture)
3. [Tech stack](#tech-stack)
4. [How a transaction is decided](#how-a-transaction-is-decided)
5. [Machine-learning component](#machine-learning-component)
6. [Design decisions](#design-decisions)
7. [Data model](#data-model)
8. [API](#api)
9. [Repository structure](#repository-structure)
10. [Getting started](#getting-started)
11. [Testing](#testing)
12. [Limitations](#limitations)
13. [Roadmap](#roadmap)

---

## Progress

Status legend: ✅ done · 🚧 in progress · ⏳ planned. Percentages are rough estimates by effort.

| Level | Milestone | Status | Progress |
|---|---|---|---|
| M0 | Scoping, C4 architecture, database schema, API contract | ✅ Done | `██████████` 100 % |
| M1 | ML: data exploration, training, evaluation, model selection, robustness checks, model export | ✅ Done | `██████████` 100 % |
| M2 | ML scoring service (FastAPI) with automated tests | 🚧 In progress | `█████░░░░░` 50 % |
| M3 | Backend core (Spring Boot): JWT auth, transactions, scoring client with timeout, decision engine | ⏳ Planned | `░░░░░░░░░░` 0 % |
| M4 | Review workflow, notifications, repeated-block convocations, email verification | ⏳ Planned | `░░░░░░░░░░` 0 % |
| M5 | Frontend (Angular): login, transactions, analyst queue | ⏳ Planned | `░░░░░░░░░░` 0 % |
| M6 | Docker Compose, end-to-end tests, demo video | ⏳ Planned | `░░░░░░░░░░` 0 % |

**Feature checklist**

| Feature | Status |
|---|---|
| Fraud-scoring model (Random Forest) trained, evaluated and exported | ✅ |
| Model robustness check against training/serving skew | ✅ |
| Unit tests for feature engineering and the model | ✅ |
| Scoring REST API (`/predict`, `/health`) | 🚧 |
| JWT authentication and role-based access (client / analyst / admin) | ⏳ |
| Transaction creation, scoring and automatic decision | ⏳ |
| Manual review queue for analysts | ⏳ |
| In-app notifications (polling) | ⏳ |
| Convocation rules for repeated blocked transactions | ⏳ |
| Email verification and convocation emails (Mailpit in development) | ⏳ |
| One-command startup with Docker Compose | ⏳ |

---

## Architecture

The system is a **polyglot, service-oriented architecture**: each component uses the technology best suited to its job.

```text
[ Web client (Angular) ]
          │  HTTPS / REST (JSON) + JWT
          ▼
[ Business backend (Spring Boot, modular monolith) ] ── JDBC ──> [ PostgreSQL ]
          │                         │
          │ REST (JSON), timeout 3 s │ SMTP (async)
          ▼                         ▼
[ Scoring service (FastAPI) ]   [ SMTP server (Mailpit in dev) ]
          │
          ▼
   [ ML model (joblib) ]
```

- **Angular** only talks to Spring Boot. The scoring service is never exposed to the client.
- **Spring Boot** is the single entry point: authentication, business rules, persistence, decisions.
- **FastAPI** is a stateless scoring service. It loads the model once at startup and does not access the database.
- The model is **trained offline** (`train.py`) and exported as a single scikit-learn `Pipeline`, so training and serving apply identical transformations.

C4 diagrams (context and containers) are in [`docs/`](docs/): `c4-1-context.png` and `c4-2-containers.png` (PlantUML sources included).

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Angular |
| Backend | Java, Spring Boot, Spring Security (JWT), Spring Data JPA |
| Database | PostgreSQL |
| Scoring service | Python, FastAPI, Pydantic, Uvicorn |
| Machine learning | scikit-learn, pandas, NumPy, joblib |
| Testing | pytest (ML service); JUnit planned for the backend |
| Dev tooling | Docker Compose, Mailpit (test SMTP), PlantUML (C4 and ER diagrams) |

---

## How a transaction is decided

Every transaction receives a **risk score between 0 and 1**. Two configurable thresholds turn it into a decision:

| Risk score | Status | What happens |
|---|---|---|
| < 0.40 | `APPROVED` | Executed automatically |
| 0.40 – 0.75 | `PENDING_REVIEW` | An analyst decides; balances are untouched until approval |
| > 0.75 | `BLOCKED` | Blocked automatically |

An analyst's decision produces `APPROVED_BY_ANALYST` or `REJECTED_BY_ANALYST`, and is stored with the analyst's identity, timestamp and comment (audit trail).

**If the scoring service is unavailable** (timeout, error, service down), the transaction is neither approved nor blocked blindly: it goes to `PENDING_REVIEW` with `scoringStatus = UNAVAILABLE`, and is re-scored later by a scheduled job.

**Repeated blocks trigger a convocation.** If a client accumulates too many blocked or rejected transactions inside a sliding window, a convocation to a branch is created and their accounts move to `UNDER_REVIEW` (new transactions then go straight to manual review):

| Window | Blocked / rejected transactions |
|---|---|
| 7 days | 3 |
| 30 days | 5 |
| 60 days | 7 |
| 180 days | 12 |
| 365 days | 20 |

Rules are configuration-driven, so thresholds can change without code changes.

---

## Machine-learning component

### Dataset

[PaySim](https://www.kaggle.com/datasets/ealaxi/paysim1): a **synthetic** mobile-money transaction log (6,362,620 rows, 8,213 frauds = **0.129 %**). The CSV is not versioned (about 470 MB); see [Getting started](#getting-started).

Findings from the exploration (`explore.py`):

- Fraud only occurs in `TRANSFER` (0.77 % of transfers) and `CASH_OUT` (0.18 %); the other types contain none.
- Fraudulent amounts are much larger (mean ≈ 1.47 M vs ≈ 178 k; median ≈ 441 k vs ≈ 75 k).
- A transaction that empties the origin account is about **125× more likely** to be fraud (0.53 % vs 0.0042 %), yet 99.5 % of emptying transactions are legitimate: no single rule is enough, which is why a model is used.
- `isFlaggedFraud` (output of an older rule system) is excluded to avoid leakage, as are account identifiers and `step`.

### Training protocol

1. Stratified 80/20 train/test split **before** any resampling, so the test set keeps the real 0.129 % fraud rate (1,272,524 rows, 1,643 frauds).
2. Undersampling of the **training set only**: all 6,570 frauds + 10 legitimate transactions per fraud (72,270 rows).
3. A scikit-learn `Pipeline`: feature engineering, one-hot encoding of the transaction type, then the model.
4. Two models compared: logistic regression (baseline) and Random Forest (200 trees, `max_depth=12`, `min_samples_leaf=5`).
5. Evaluation with precision, recall, F1 and **AUC-PR** (accuracy is meaningless at 0.129 % fraud: predicting "never fraud" scores 99.87 %).

### Model selection

| Model | AUC-PR | AUC-ROC |
|---|---|---|
| Logistic regression | 0.6904 | 0.9931 |
| **Random Forest** | **0.9986** | 0.9993 |

AUC-ROC makes both models look almost equal; AUC-PR, which ignores the millions of easy legitimate transactions, shows the real gap. The Random Forest dominates the baseline at every threshold: fraud is a *combination* of conditions (type, large amount, emptied account) that a linear model cannot express.

### Training/serving skew (found and fixed)

The first model used the post-transaction balances (`newbalanceOrig`, `newbalanceDest`). In PaySim these are sometimes inconsistent for frauds, which the model exploited. In this application the backend **computes** those balances, so they are always consistent and that signal would never appear.

Simulating production conditions showed the effect: recall at threshold 0.90 fell from 0.994 to 0.491. A second check showed that zeroing the destination balance for non-transfer types, as the application does, produced about 50,000 false alerts at threshold 0.40.

**Final model (v2)** therefore:

- uses only inputs the application can supply faithfully: `type`, `amount`, `oldbalanceOrg`, `oldbalanceDest`;
- derives `isAccountEmptied`, `amountToBalanceRatio`, `destWasEmpty` from them;
- applies the business rule "no internal destination account outside `TRANSFER`" **inside the Pipeline**, so training, evaluation and serving always behave identically.

### Final results (v2, held-out test set, real fraud rate)

AUC-PR **0.9976**

| Threshold | Precision | Recall | False positives | Missed frauds |
|---|---|---|---|---|
| 0.20 | 0.917 | 0.998 | 148 | 4 |
| **0.40** | 0.981 | 0.998 | 31 | 4 |
| 0.50 | 0.995 | 0.998 | 9 | 4 |
| **0.75** | 0.999 | 0.998 | 1 | 4 |
| 0.90 | 0.999 | 0.998 | 1 | 4 |

The 0.40 / 0.75 thresholds were chosen from this table and verified under production-like conditions.

### Scoring service API (FastAPI)

```http
POST /predict
{ "type": "TRANSFER", "amount": 9500.0, "oldbalanceOrg": 9500.0, "oldbalanceDest": 0.0 }

200 → { "score": 0.97, "modelVersion": "1.0.0" }
422 → invalid input      503 → model not loaded
```

`GET /health` returns `{ "status": "ok", "model_loaded": true, "modelVersion": "1.0.0" }`. The service can require an `X-API-Key` header (environment variable `ML_API_KEY`). Interactive documentation is served at `/docs`.

---

## Design decisions

| Decision | Reasoning |
|---|---|
| **Modular monolith, not microservices** | One developer, bounded scope; microservices would add network and deployment complexity without benefit. The ML service is already a natural separate boundary. |
| **No API gateway** | Spring Boot is the only service exposed. A gateway would be added if the backend were split. |
| **Synchronous scoring call, not a callback** | Scoring takes milliseconds, timeouts are trivial to handle, and the scoring service stays stateless and unaware of the backend. A message queue would only make sense for slow or high-volume scoring. |
| **Polling for notifications, no WebSocket** | Simple, works with JWT unchanged; SSE is the noted upgrade path. |
| **Unavailable scoring → manual review** | Auto-approving lets an attacker exploit outages; auto-blocking penalises every customer during an outage. |
| **Risk score hidden from clients** | Exposing it would let a fraudster probe for the threshold. Only analysts and admins see it. |
| **Model and rules in one Pipeline** | Guarantees identical behaviour in training and serving. |
| **Contract-first API design** | OpenAPI definitions in `docs/` before implementation. |

---

## Data model

PostgreSQL schema in [`docs/schema.sql`](docs/schema.sql), diagram in [`docs/db-erd.png`](docs/db-erd.png).

| Table | Purpose |
|---|---|
| `users` | Clients, analysts, admins (BCrypt password hashes, roles, status) |
| `email_verifications` | Verification tokens (single use, expiring) |
| `accounts` | Fictional accounts with balances, optimistic locking (`version`) |
| `transactions` | Amount, type, balance snapshot, risk score, model version, features snapshot, status |
| `transaction_reviews` | Analyst decisions (one final decision per transaction) |
| `convocations` | Branch convocations (one active per client, enforced by a partial unique index) |
| `notifications` | In-app notifications |

Money is stored as `NUMERIC(15,2)`. Each transaction stores the score, the model version and the exact features sent, for audit and future retraining.

---

## API

- Backend (Spring Boot, consumed by Angular): [`docs/api-backend.yaml`](docs/api-backend.yaml), OpenAPI 3
- Scoring service (FastAPI, internal only): [`docs/api-ml-service.yaml`](docs/api-ml-service.yaml), OpenAPI 3

The backend contract is the design reference; once implemented, the live Swagger UI is generated from the code.

---

## Repository structure

```text
fraud-detection-platform/
├── frontend/                 # Angular (planned)
├── backend/                  # Spring Boot (planned)
├── ml-service/
│   ├── app/
│   │   ├── features.py       # shared feature engineering (used by training AND serving)
│   │   ├── schemas.py        # Pydantic request/response models
│   │   ├── predictor.py      # loads the model once, exposes predict()
│   │   └── main.py           # FastAPI routes
│   ├── data/raw/             # PaySim CSV (not versioned)
│   ├── models/               # model.joblib, model_metadata.json
│   ├── tests/                # pytest
│   ├── explore.py            # data exploration
│   ├── train.py              # training, evaluation, export
│   └── requirements.txt
├── docs/                     # C4, ER diagram, SQL schema, OpenAPI contracts
├── docker-compose.yml        # planned
└── README.md
```

---

## Getting started

Only the ML component is runnable today. Backend, frontend and Docker Compose will be documented as they are completed.

**Prerequisites:** Python 3.11+.

```bash
cd ml-service
python -m venv venv
source venv/bin/activate          # Windows PowerShell: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**1. Get the dataset.** Download PaySim from [Kaggle](https://www.kaggle.com/datasets/ealaxi/paysim1) and place `PS_20174392719_1491204439457_log.csv` in `ml-service/data/raw/`. It is git-ignored.

**2. Train and export the model.**

```bash
python train.py
```

This evaluates the models and writes `models/model.joblib` and `models/model_metadata.json`.

**3. Run the scoring service.**

```bash
uvicorn app.main:app --reload --port 8000
```

Open <http://localhost:8000/docs> for the interactive documentation. To require an API key, set `ML_API_KEY` before starting.

> Use the same scikit-learn and pandas versions for training and serving. A `.joblib` file must be loaded with the version that created it; versions are pinned in `requirements.txt`.

---

## Testing

```bash
cd ml-service
python -m pytest -v
```

| Test area | What it verifies |
|---|---|
| Feature engineering | Emptied-account flag, zero-balance safety, destination rule outside `TRANSFER`, input not mutated |
| Model | Score in [0, 1], deterministic output, no effect of the destination balance outside `TRANSFER` |
| API | Health, valid prediction, input validation (422), API-key enforcement |

Backend and end-to-end tests are planned (decision thresholds and their boundary cases, convocation windows, scoring timeout).

---

## Limitations

- **Synthetic data.** PaySim frauds follow regular patterns, so the near-perfect metrics do **not** reflect what real banking data would give.
- **Scores are not calibrated probabilities.** Undersampling inflates them; they are relative risk scores and the thresholds were chosen empirically.
- **The review band is almost empty on PaySim.** Scores are very separated: in the test set, 0.40–0.75 contains about 30 legitimate transactions and no fraud. On real, messier data that band would matter far more.
- **4 frauds are missed** (scores below 0.20) in the test set.
- **Not a banking product.** All accounts are fictional; there is no real KYC, no real banking integration, and the project makes no regulatory-compliance claim. Real-world use would require identity verification, anti-money-laundering controls and a security audit.
- **Token storage** in `localStorage` (planned) is exposed to XSS; an HttpOnly cookie would be safer.

---

## Roadmap

1. Finish the FastAPI service and its tests (M2).
2. Spring Boot core: authentication, transactions, scoring client with timeout, decision engine (M3).
3. Review workflow, notifications, convocations, email verification (M4).
4. Angular frontend (M5).
5. Docker Compose, end-to-end tests, demo video (M6).

**Possible improvements:** gradient boosting and SHAP explanations, retraining from analyst decisions (feedback loop), drift monitoring, SSE for real-time alerts, a message queue for high-volume scoring, refresh tokens.

---

## Author
Youssef ben othmen  · [www.linkedin.com/in/youssef-ben-othmen-463b99331] · [https://github.com/Youssef-dev15]

