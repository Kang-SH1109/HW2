from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "messages.csv"
ARTIFACTS = ROOT / "artifacts"
MODEL_PATH = ARTIFACTS / "spam_model.joblib"
METRICS_PATH = ARTIFACTS / "metrics.json"
MAX_MESSAGE_LENGTH = 2000
MODEL_VERSION = "0.4.0-public100"
ML_DATA_DIR = ROOT / "mlops_data"
PUBLIC_DATASET = "jmjmjm3/kor-smishing-message"
PUBLIC_DATASET_COMMIT = "4bd585dd3fc21223ef25de88c86049cb67d8c92f"
