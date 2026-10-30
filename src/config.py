from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "messages.csv"
ARTIFACTS = ROOT / "artifacts"
MODEL_PATH = ARTIFACTS / "spam_model.joblib"
METRICS_PATH = ARTIFACTS / "metrics.json"
MAX_MESSAGE_LENGTH = 2000
MODEL_VERSION = "0.3.0-example-data"
