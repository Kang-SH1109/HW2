import json, logging
from .model import train_and_evaluate

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
if __name__ == "__main__":
    print(json.dumps(train_and_evaluate(), ensure_ascii=False, indent=2))
