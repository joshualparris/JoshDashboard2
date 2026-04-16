# JoshDashboard2

This repository contains the legacy HTML dashboard server for JoshProfile, intended to run locally at `http://localhost:8765/dashboard.html`.

## Run locally

1. Copy the `processed/` data directory from the main JoshProfile project into this repository root.
2. Install dependencies if needed (standard Python library only).
3. Run:

```bash
python dashboard.py
```

4. Open `http://localhost:8765/dashboard.html`.

## Notes

- The dashboard server also serves `/`.
- The main dashboard HTML is generated dynamically from `processed/source_coverage.json` and related output files.
