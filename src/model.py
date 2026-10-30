import csv, json, logging
from datetime import datetime, timezone
from pathlib import Path
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from .config import ARTIFACTS, DATA_PATH, MODEL_PATH, METRICS_PATH, MODEL_VERSION

log = logging.getLogger(__name__)

def load_data(path=DATA_PATH):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    labels = {r.get("label", "").strip() for r in rows}
    if not rows or labels != {"spam", "normal"} or any(not r.get("text", "").strip() for r in rows):
        raise ValueError("데이터에는 비어 있지 않은 text와 spam/normal label이 필요합니다.")
    return [r["text"].strip() for r in rows], [r["label"].strip() for r in rows]

def train_and_evaluate(output_model=MODEL_PATH, output_metrics=METRICS_PATH):
    texts, labels = load_data()
    x_train, x_test, y_train, y_test = train_test_split(texts, labels, test_size=.25, random_state=42, stratify=labels)
    pipeline = Pipeline([("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(2, 5), sublinear_tf=True)), ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42))])
    pipeline.fit(x_train, y_train); pred = pipeline.predict(x_test)
    cm = confusion_matrix(y_test, pred, labels=["normal", "spam"])
    metrics = {"model_version": MODEL_VERSION, "trained_at_utc": datetime.now(timezone.utc).isoformat(), "dataset": "data/messages.csv", "dataset_source": "프로젝트가 직접 작성한 검증용 한국어 예시 데이터(공개 데이터셋 아님)", "dataset_rows": len(texts), "train_rows": len(x_train), "test_rows": len(x_test), "accuracy": round(float(accuracy_score(y_test, pred)), 4), "precision_spam": round(float(precision_score(y_test, pred, pos_label="spam", zero_division=0)), 4), "recall_spam": round(float(recall_score(y_test, pred, pos_label="spam", zero_division=0)), 4), "f1_spam": round(float(f1_score(y_test, pred, pos_label="spam", zero_division=0)), 4), "confusion_matrix_labels": ["normal", "spam"], "confusion_matrix": cm.tolist(), "data_note": "표본이 작고 예시 데이터이므로 실제 운영 성능을 대표하거나 보장하지 않습니다."}
    output_model, output_metrics = Path(output_model), Path(output_metrics); ARTIFACTS.mkdir(exist_ok=True)
    joblib.dump(pipeline, output_model); output_metrics.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("model trained: %s", metrics); return metrics

def load_model(path=MODEL_PATH):
    path = Path(path)
    if not path.exists(): raise FileNotFoundError("모델 파일이 없습니다. 먼저 python -m src.train 을 실행하세요.")
    try:
        loaded = joblib.load(path)
        if not hasattr(loaded, "predict_proba") or not hasattr(loaded, "classes_"): raise ValueError("분류 모델 형식이 아닙니다.")
        return loaded
    except Exception as exc: raise RuntimeError("모델 파일이 손상되었거나 현재 패키지와 호환되지 않습니다.") from exc
