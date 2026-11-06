"""Reproducible public-data selection, model comparison, and final training."""
import csv
import json
import random
import re
import unicodedata
import urllib.request
from datetime import datetime, timezone

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.metrics import make_scorer
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

from .config import ARTIFACTS, ML_DATA_DIR, MODEL_PATH, MODEL_VERSION, PUBLIC_DATASET, PUBLIC_DATASET_COMMIT

SOURCE_URL = f"https://huggingface.co/datasets/{PUBLIC_DATASET}/resolve/{PUBLIC_DATASET_COMMIT}/smishing.csv"
RANDOM_SEED = 20261106
PER_CLASS = 500
TUNING_ROWS = 300
EVALUATION_ROWS = 700


def normalize_text(text):
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = re.sub(r"(?:https?://|www\.)\S+|\b(?:[\w-]+\.)+(?:kr|com|net|org|ly)\S*", " URL ", text)
    text = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", " EMAIL ", text)
    text = re.sub(r"(?:01[016789][- ]?\d{3,4}[- ]?\d{4}|\b\d{2,4}[- ]\d{3,4}[- ]\d{4}\b)", " PHONE ", text)
    return re.sub(r"\s+", " ", text).strip()


def download_source():
    ML_DATA_DIR.mkdir(exist_ok=True)
    source = ML_DATA_DIR / "source.csv"
    if not source.exists():
        urllib.request.urlretrieve(SOURCE_URL, source)
    return source


def prepare_data():
    candidates, seen = [], set()
    with download_source().open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            label = {"정상": "normal", "스미싱": "spam"}.get((row.get("label") or "").strip())
            text = normalize_text(row.get("content"))
            if not label or not text or text in seen:
                continue
            seen.add(text); candidates.append((label, text))
    rng = random.Random(RANDOM_SEED); rng.shuffle(candidates)
    by_label = {"normal": [], "spam": []}
    for label, text in candidates:
        if len(by_label[label]) < PER_CLASS: by_label[label].append((label, text))
    if any(len(rows) < PER_CLASS for rows in by_label.values()):
        raise RuntimeError(f"공개 데이터에서 라벨별 {PER_CLASS}건을 확보하지 못했습니다.")
    selected = by_label["normal"] + by_label["spam"]; rng.shuffle(selected)
    tuning, evaluation = selected[:TUNING_ROWS], selected[TUNING_ROWS:TUNING_ROWS + EVALUATION_ROWS]
    for path, rows in ((ML_DATA_DIR / "tuning.csv", tuning), (ML_DATA_DIR / "evaluation.csv", evaluation)):
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream); writer.writerow(["label", "text"]); writer.writerows(rows)
    metadata = {"dataset": PUBLIC_DATASET, "commit": PUBLIC_DATASET_COMMIT, "source_url": SOURCE_URL,
                "license": "CC BY-NC-SA 4.0", "selection_seed": RANDOM_SEED, "selected_rows": PER_CLASS * 2,
                "class_counts": {"normal": PER_CLASS, "spam": PER_CLASS}, "tuning_rows": TUNING_ROWS,
                "evaluation_rows": EVALUATION_ROWS, "tuning_isolated_from_evaluation": True,
                "preprocessing": "Unicode NFKC, lower-case, URL/email/phone redaction, whitespace normalization",
                "deduplicated_rows": len(candidates), "created_at_utc": datetime.now(timezone.utc).isoformat()}
    (ML_DATA_DIR / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return tuning, evaluation, metadata


def legacy_pipeline():
    return Pipeline([("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(2, 5), sublinear_tf=True)),
                     ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42))])


def improved_pipeline(attempt):
    params = {"C": 1.0 if attempt == 1 else 2.0, "max_iter": 1500, "class_weight": "balanced", "random_state": 42}
    return Pipeline([("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(2, 6), min_df=1, sublinear_tf=True)),
                     ("classifier", LogisticRegression(**params))])


def evaluate(pipeline, train_rows, evaluation):
    x_train, y_train = zip(*[(text, label) for label, text in train_rows])
    x_eval, y_eval = zip(*[(text, label) for label, text in evaluation])
    pipeline.fit(x_train, y_train); predictions = pipeline.predict(x_eval)
    return {"accuracy": round(float(accuracy_score(y_eval, predictions)), 4),
            "precision_spam": round(float(precision_score(y_eval, predictions, pos_label="spam", zero_division=0)), 4),
            "recall_spam": round(float(recall_score(y_eval, predictions, pos_label="spam", zero_division=0)), 4),
            "f1_spam": round(float(f1_score(y_eval, predictions, pos_label="spam", zero_division=0)), 4),
            "confusion_matrix_labels": ["normal", "spam"],
            "confusion_matrix": confusion_matrix(y_eval, predictions, labels=["normal", "spam"]).tolist()}


def run_pipeline():
    tuning, evaluation, metadata = prepare_data()
    x_tune, y_tune = zip(*[(text, label) for label, text in tuning])
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_SEED)
    spam_f1 = make_scorer(f1_score, pos_label="spam", zero_division=0)
    cv_scores = {f"attempt_{i}": round(float(cross_val_score(improved_pipeline(i), x_tune, y_tune, cv=cv, scoring=spam_f1).mean()), 4) for i in (1, 2)}
    chosen = 1 if cv_scores["attempt_1"] >= cv_scores["attempt_2"] else 2
    baseline = evaluate(legacy_pipeline(), tuning, evaluation)
    improved = evaluate(improved_pipeline(chosen), tuning, evaluation)
    comparison = {"model_version": MODEL_VERSION, "baseline": baseline, "improved": improved,
                  "selected_attempt": chosen, "tuning_cv_f1": cv_scores,
                  "false_negative_baseline": baseline["confusion_matrix"][1][0],
                  "false_negative_improved": improved["confusion_matrix"][1][0], "dataset": metadata,
                  "decision": "replace" if (improved["f1_spam"] >= baseline["f1_spam"] and improved["accuracy"] >= baseline["accuracy"]) else "keep-baseline"}
    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS / "model_comparison.json").write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    final_model = improved_pipeline(chosen) if comparison["decision"] == "replace" else legacy_pipeline()
    final_model.fit(x_tune, y_tune)
    import joblib
    joblib.dump(final_model, MODEL_PATH)
    (ARTIFACTS / "model_metadata.json").write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(comparison, ensure_ascii=False, indent=2)); return comparison


if __name__ == "__main__":
    run_pipeline()
