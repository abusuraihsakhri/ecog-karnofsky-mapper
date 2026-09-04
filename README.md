# Ecog Karnofsky Mapper

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Standards:** CAP / CLSI / ISO

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)

---

## What It Does

ECOG & Karnofsky Performance Status Mapper bidirectionally maps and validates oncologic functional performance scales with clinical trial eligibility. It provides:

- Single-case evaluation via CLI
- Batch CSV processing
- Multi-worker consensus with specialized agents
- HMAC-SHA256 tamper-evident audit trail
- Zero-PHI outbound guard
- FastAPI REST API with health and metrics endpoints

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/ecog-karnofsky-mapper.git
cd ecog-karnofsky-mapper

# Install dependencies
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Requirements
- Python 3.10+
- fastapi >= 0.111.0
- uvicorn >= 0.30.0
- pydantic >= 2.7.0

---

## Usage

### CLI — Single Case Evaluation
```bash
python ecog_karnofsky.py single --v1 14.5 --v2 4.2 --v3 1.8
```

### CLI — Batch CSV Processing
```bash
python ecog_karnofsky.py batch -i sample.csv -o results.csv
```

### CLI — Enterprise Supervisor (agents system)
```bash
# Run a single audit task
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch process records
python cli.py batch -i sample.csv -o results.csv

# Verify audit trail integrity
python cli.py verify-audit

# Chat with supervisor
python cli.py chat "Explain the scoring methodology"
```

### REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

Or with Docker:
```bash
docker-compose up --build
```

### API Endpoints
| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/health` | GET | Health check |
| `/metrics` | GET | Operational metrics |
| `/api/audit` | POST | Submit task for evaluation |
| `/api/chat` | POST | Query supervisory chat |
| `/api/audit/logs` | GET | Retrieve audit trail |

---

## Input Data Schema

### Single Evaluation
| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `--v1` | float | 10.0 | Primary parameter |
| `--v2` | float | 5.0 | Secondary parameter |
| `--v3` | float | 2.0 | Tertiary parameter |

### Batch CSV
| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Patient identifier | Required |
| `v1` | Primary measurement | Required |
| `v2` | Secondary measurement | Required |
| `v3` | Tertiary measurement | Required |

---

## Security

- **Zero-PHI Outbound Guard:** AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
- **HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation
- **Input Validation:** Numeric inputs validated against NaN/Inf injection
- **Audit Secret Key:** Configure via `AUDIT_SECRET_KEY` environment variable (required for persistent audit integrity)

---

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest -v --cov=agents --cov=ecog_karnofsky
```

---

## Project Structure

```
ecog-karnofsky-mapper/
├── agents/                  # Enterprise multi-agent system
│   ├── api.py              # FastAPI REST server
│   ├── base.py             # Security, PHI guard, audit trail
│   ├── models.py           # Pydantic data models
│   ├── supervisor.py       # Master orchestrator
│   ├── workers.py          # Specialized evaluation workers
│   ├── llm_factory.py      # LLM provider factory
│   ├── metrics.py          # Prometheus metrics collector
│   ├── learning.py         # Bayesian calibration engine
│   └── streamer.py         # WebSocket telemetry broadcaster
├── tests/                  # Test suite
├── web/                    # Operations console (HTML)
├── cli.py                  # Enterprise CLI entry point
├── ecog_karnofsky.py       # Core scoring algorithm & CLI
├── enrichment.py           # Enrichment feature engines
├── simulator.py            # High-throughput stress simulator
├── pyproject.toml          # Project metadata & dependencies
├── Dockerfile              # Container build
└── docker-compose.yml      # Container orchestration
```

---

## Container Deployment

```bash
# Build and run with Docker
docker build -t ecog-karnofsky-mapper .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key ecog-karnofsky-mapper

# Or use docker-compose
AUDIT_SECRET_KEY=your-secret-key docker-compose up --build
```
