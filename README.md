# ChainNetra (चेन-नेत्र) 👁️
### Real-Time Cryptocurrency Fraud Attribution & Automated VASP Identification Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)](https://react.dev/)
[![Cytoscape](https://img.shields.io/badge/Cytoscape.js-3.28-EA580C?style=flat-square)](https://js.cytoscape.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4-F7931E?style=flat-square&logo=scikit-learn)](https://scikit-learn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

> **One-Line Mission**: Turn a days-long expert tracing task into a minutes-long automated one so proceeds of cybercrime can be frozen at exchanges before they disappear.

---

## 📸 Architecture & Overview

![ChainNetra Architecture](docs/architecture.svg)

ChainNetra ("Netra" = Eye) is an automated blockchain forensics command room tailored for Law Enforcement Agencies (LEAs), State Cyber Cells, and Financial Intelligence Units (FIU-IND). Taking reported suspect cryptocurrency addresses from victim complaints (via simulated NCRP / SAHYOG feeds), ChainNetra automatically traces multi-chain fund flows, isolates intermediary layering burner wallets, identifies the nearest Virtual Asset Service Provider (VASP / Exchange) deposit address, predicts laundering typologies via ML, automates freeze notices, and certifies evidence with cryptographic hash chains.

---

## ⚡ Key Capabilities

- **Automated First-VASP-Hit Tracing**: Priority-queue graph traversal keyed by tainted value exploring multi-chain transfers to identify cash-out exchanges in seconds.
- **Taint Propagation Models**: Haircut (proportional allocation), FIFO (first-in first-out), and Poison (full contamination) models.
- **Explainable Attribution & Heuristics**: Mathematical confidence scoring ($0.45 \cdot W_{label} + 0.30 \cdot E_{strength} + 0.15 \cdot C_{cluster} - 0.02 \cdot Hops$) citing exchange sweep patterns and cluster heuristics.
- **Cross-Chain Bridge Analytics**: Heuristic matching across Tron, Ethereum, BSC, Polygon, and Arbitrum tracking bridge deposits, release transactions, and DEX router swaps.
- **AI / ML Risk & Typology Engine**: Random Forest wallet role classification, Isolation Forest anomaly scoring, and weighted rule matching across 7 fraud typologies (Pig-butchering, Task fraud, Sextortion, Ransomware, Phishing drainers, Darknet, Layering syndicates).
- **Syndicate Convergence (Case Linking)**: Interactive evidence board linking disparate victim complaints across states converging onto shared collector clusters.
- **Statutory Freeze Notice Composer**: Auto-populated freeze requests with transaction hashes, SLA countdowns, and multi-stage approval workflows (Draft $\rightarrow$ Supervisor Approval $\rightarrow$ Outbound Dispatch $\rightarrow$ Frozen).
- **Court-Ready PDF Reports & QR Verification**: A4 PDF investigation summaries with canonical JSON snapshots, SHA-256 integrity digests, and a public `/verify` portal.
- **Cryptographic Hash-Chained Audit Log**: Every investigative action is linked in a tamper-evident hash chain (`prev_hash` + `entry_hash`), preventing internal evidence tampering.
- **Dual Operating Modes**:
  - `DEMO MODE`: Fully functional offline deterministic dataset seeded with 6 realistic cybercrime scenarios, 65 historic cases, and 8 VASPs.
  - `LIVE MODE`: Connects to public blockchain RPCs and explorers (TronGrid, Etherscan family, Blockstream Esplora) with automatic caching and circuit-breaker fallback.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Cytoscape.js (`cytoscape-fcose`), Recharts, Framer Motion, Driver.js, Zustand, TanStack Query |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2 (WAL mode SQLite, Postgres-ready), NetworkX, Native WebSockets |
| **Intelligence & ML** | Scikit-learn (RandomForest, IsolationForest), NumPy, Pandas, Joblib |
| **Evidence & Integrity** | ReportLab (A4 PDF), QRCode, SHA-256 Hash Chaining, HMAC-SHA256 Webhooks |

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Git

### Option A: Single-Command Bootstrap (Windows / Linux / macOS)

```bash
# Clone the repository
git clone https://github.com/sscodings/SIH_2.git
cd SIH_2

# Setup backend
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\pip install -r requirements.txt
# Linux/macOS: source venv/bin/activate && pip install -r requirements.txt

# Seed deterministic dataset & train ML models
python -m app.db.seed
python -m app.ml.train

# Start backend server (Port 8000)
# Windows:
powershell -Command "$env:PYTHONPATH='.'; .\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
# Linux/macOS:
PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

In a second terminal:
```bash
# Setup and start frontend (Port 5173)
cd frontend
npm install
npm run dev
```

Open **`http://127.0.0.1:5173`** in your browser.

---

### Option B: Docker Compose

```bash
docker-compose up --build
```
- Frontend UI: `http://localhost:5173`
- Backend API Docs: `http://localhost:8000/docs`

---

## 🔐 Demo Credentials

In Demo Mode, pre-seeded accounts are provided on the login screen:
- **Investigator**: `investigator@demo` / `demo123` (Tracing, Cases, Reports)
- **Supervisor**: `supervisor@demo` / `demo123` (Freeze Approval, Analytics, Audits)
- **Administrator**: `admin@demo` / `demo123` (Label Management, API Keys, System Settings)

---

## 🧪 Testing

Run backend engine tests covering taint models, confidence formulas, address validators, audit log integrity, and end-to-end First-VASP-Hit tracing:

```bash
cd backend
.\venv\Scripts\pytest tests/
```

---

## ⚖️ Limitations & Production Roadmap

- **Attribution Inference**: Address attribution constitutes mathematical and behavioral evidence-based inference, not absolute legal proof.
- **Mixer / Privacy Coins**: Tracing through privacy pools uses probabilistic denomination and time-delta matching with explicit confidence caveats.
- **Enterprise Scaling**: For production deployments handling nationwide scale, SQLite seamlessly transitions to PostgreSQL + ClickHouse / Neo4j via SQLAlchemy, and WebSockets integrate with Apache Kafka for millions of real-time transactions.

---

## 📄 License
This project is licensed under the MIT License. Developed for Smart India Hackathon (SIH).
