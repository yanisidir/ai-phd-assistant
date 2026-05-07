# README.md — AI PhD Assistant

````markdown
# AI PhD Assistant

AI PhD Assistant is an automated platform designed to discover, filter, score and track PhD opportunities in physics and related scientific fields.

The project currently focuses on:
- particle physics
- astroparticle physics
- detector instrumentation
- nuclear physics
- AI for physics
- theoretical physics

The system automatically scrapes PhD offers, filters irrelevant positions, scores them according to a customizable research profile, stores results in SQLite, and provides a Streamlit interface for tracking applications.

---

# Features

## Automated scraping

Current integrated sources:
- InspireHEP
- Academic Positions

The scrapers:
- retrieve recent PhD offers
- clean HTML descriptions
- remove duplicates
- reject expired offers
- filter postdocs/faculty positions

---

## Smart filtering

The pipeline automatically removes:
- postdoctoral positions
- faculty positions
- research associate jobs
- irrelevant offers

Only relevant PhD/doctoral opportunities are kept.

---

## Profile-based scoring

Offers are scored using:
- customizable interests
- negative interests
- keyword weighting

The profile is stored in:

```text
data/profile.json
````

No hardcoded scientific keywords remain in the scoring logic.

---

## SQLite storage

The database automatically stores:

* title
* source
* laboratory
* deadline
* description
* score
* decision
* application status
* links
* timestamps

Automatic schema migration is supported.

---

## Application tracking

Supported statuses:

* to_apply
* applied
* rejected
* accepted

Statuses persist even after re-scraping.

---

## Streamlit dashboard

The interface allows:

* filtering by source
* filtering by status
* filtering by decision
* viewing detailed descriptions
* updating application status
* tracking relevant opportunities

---

# Project structure

```text
ai-phd-assistant/
│
├── app/
│   └── streamlit_app.py
│
├── data/
│   ├── offers.db
│   └── profile.json
│
├── processing/
│   ├── parser.py
│   └── scorer.py
│
├── scrapers/
│   ├── crawl4ai_inspirehep.py
│   └── crawl4ai_academic_positions.py
│
├── main.py
├── view_db.py
└── requirements.txt
```

---

# Installation

## Clone repository

```bash
git clone <repo_url>
cd ai-phd-assistant
```

---

## Create virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

---

## Install dependencies

```bash
pip install -r requirements.txt
```

---

# Usage

## Run scraping pipeline

```bash
python main.py
```

---

## View database

```bash
python view_db.py
```

---

## Launch Streamlit interface

```bash
streamlit run app/streamlit_app.py
```

---

# Scoring system

Current scoring thresholds:

| Score | Decision   |
| ----- | ---------- |
| >= 60 | candidater |
| 30–59 | a_verifier |
| < 30  | ignorer    |

Low-score offers are automatically removed unless:

* status = applied
* status = accepted

---

# Current status

Implemented:

* stable scraping pipeline
* filtering system
* SQLite persistence
* automatic migration
* Streamlit interface
* profile-based scoring
* application tracking
* cleanup of irrelevant offers

Removed:

* Ollama
* LLM scoring
* automatic email generation

The project currently runs fully without LLM dependencies.

---

# Future improvements

## Short term

* export CSV/PDF
* additional sources
* favorites system

## Mid term

* embeddings-based matching
* notifications
* recommendation engine

## Long term

* automatic CV ↔ offer matching
* cover letter generation
* full scientific application assistant

---

# License

MIT License

```
```
