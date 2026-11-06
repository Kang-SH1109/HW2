# MLOps and deployment runbook

## Pipeline

`python -m src.mlops_pipeline` downloads the pinned public CSV, removes duplicate normalized messages, redacts URL/e-mail/phone patterns, and creates exactly 30 tuning and 70 final-evaluation rows under `mlops_data/`. Candidate choice uses only 3-fold F1 on the tuning set. The 70-row evaluation set is read only once after selection.

Two candidate attempts are limited to:

1. NFKC/lower-case/redaction plus character TF-IDF `(2, 6)` and Logistic Regression `C=1.0`.
2. The same preprocessing/vectorizer with `C=2.0`.

The legacy comparison uses character TF-IDF `(2, 5)` without the new normalization. `artifacts/model_comparison.json` records metrics, confusion matrices, false negatives, cross-validation choice, and whether the final model was replaced.

## CI/CD

The Ubuntu job runs the pipeline and pytest, builds the Docker image, pushes `latest` and `sha-<7 characters>` tags, and verifies model loading. The Windows self-hosted job logs into Docker Hub with the existing secrets, checks the current service, starts an independent PowerShell monitor, pulls the exact SHA image, performs backup-and-rollback container replacement, and validates `/api/health` before success.

The monitor sends fixed spam/normal POST requests every second and writes UTF-8 JSONL records for `pre`, `deploying`, and `post` phases. It continues for 30 seconds after a successful replacement. A Markdown summary is written to `GITHUB_STEP_SUMMARY`; logs, summaries, and model comparison JSON are uploaded with `if: always()`.

The workflow claims no absolute zero-downtime guarantee. It reports only the observed request window, including missing responses and request gaps.
