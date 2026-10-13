# ECOG–Karnofsky Performance Status Mapper

Reference tool for mapping between **Eastern Cooperative Oncology Group (ECOG)** performance-status grades and **Karnofsky Performance Status (KPS)** scores using the comparison published by the ECOG-ACRIN Cancer Research Group.

The crosswalk is **not** a validated exact patient-level conversion. It cannot establish clinical-trial eligibility, predict prognosis, or replace a direct assessment of functional status.

## Main application

Open the repository's `index.html` in a modern browser for a standalone, dependency-free interface. A deployed GitHub Pages URL will be added after live verification.

- Compare ECOG 0–5 to grouped KPS scores.
- Compare valid KPS deciles (0–100) to an ECOG reference grade.
- Upload a UTF-8 CSV with an `ecog` or `kps` column; download the locally converted results.
- Review score descriptions and the underlying reference comparison.

**Privacy:** The static browser app performs calculations and CSV processing locally in JavaScript. It does not send input values or files to a server. Use de-identified data and safeguard any files you subsequently export or share.

## Reference crosswalk

| ECOG grade | KPS values |
| --- | --- |
| 0 | 90, 100 |
| 1 | 70, 80 |
| 2 | 50, 60 |
| 3 | 30, 40 |
| 4 | 10, 20 |
| 5 | 0 |

The published table is only one of several comparisons. The grouped categories are **not unique equivalents** and cannot substitute for actual patient observation.

Source: [ECOG-ACRIN Performance Status Scale](https://ecog-acrin.org/resources/ecog-performance-status/). Oken MM et al. *Toxicity and response criteria of the Eastern Cooperative Oncology Group.* Am J Clin Oncol. 1982;5(6):649–655. ECOG Performance Status Scale developed by the Eastern Cooperative Oncology Group, now the ECOG-ACRIN Cancer Research Group.

## Python / CLI

Requires Python 3.10 or later.

```bash
git clone https://github.com/abusuraihsakhri/ecog-karnofsky-mapper.git
cd ecog-karnofsky-mapper
python -m pip install -e ".[dev]"
python ecog_karnofsky.py single --ecog 2
python ecog_karnofsky.py single --kps 40
python ecog_karnofsky.py batch -i sample.csv -o results.csv
python -m pytest -q
```

Python callers can use `map_ecog_to_kps(grade)`, `map_kps_to_ecog(score)`, or `calculate_metrics(ecog=...)` / `calculate_metrics(kps=...)` from `ecog_karnofsky`. Input ranges and increments are validated; missing or contradictory scale inputs raise `ValueError`. Batch input requires exactly one populated scale per row. Output generation is atomic and escapes spreadsheet-formula prefixes in exported source fields.

## REST API (optional)

```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

- `GET /` — standalone browser page
- `GET /health` — health status
- `GET /api/mapping` — published reference table
- `POST /api/map` — `{"ecog": 2}` or `{"kps": 60}`, not both
- `GET /docs` and `GET /openapi.json` — FastAPI-generated documentation

The older `cli.py audit`, `chat`, `batch`, and `/api/audit` routes are retained for backward compatibility **as non-clinical demonstrations**. Their generic thresholds, synthetic recommendations and mock-language output are not ECOG/KPS decision support or verified standards conformance.

For the legacy audit simulator, `AUDIT_SECRET_KEY` must be provided for stable HMAC signing across restarts. Its in-memory trail is not a persistent audit service. The regex-based identifier filter is not a HIPAA-compliant de-identification system and cannot guarantee absence of protected health information. Do not send real patient identifiers into the legacy audit or public endpoints.

## Technology, tests and deployment

- Browser: HTML, CSS and JavaScript; no JavaScript dependencies or external runtime. Runs on GitHub Pages without Python or a backend.
- Server: Python, FastAPI, Pydantic and Uvicorn, with optional Docker support.
- Tests: Pytest for clinical groups, API input validation, CSV safety, and legacy audit integrity; GitHub Actions verifies Python 3.10–3.12 and JavaScript syntax.
- Browsers: Current versions of Chrome, Firefox, Safari and Edge. Local downloads and Clipboard API availability depend on browser permissions and context.
- License: [MIT](LICENSE).
