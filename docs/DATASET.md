# MLOps 데이터 출처와 분리 규칙

## 출처

- Dataset: `jmjmjm3/kor-smishing-message`
- Fixed revision: `4bd585dd3fc21223ef25de88c86049cb67d8c92f`
- URL: https://huggingface.co/datasets/jmjmjm3/kor-smishing-message
- License stated by the dataset card: CC BY-NC-SA 4.0
- Original labels: `정상` and `스미싱`

The pipeline maps these labels to `normal` and `spam`. The source is downloaded only by the reproducible MLOps pipeline; the raw dataset is not committed to this repository.

## Selection and privacy checks

The pipeline uses a fixed seed (`20261106`), removes duplicate normalized messages, and selects 500 messages per class. It redacts URLs, e-mail addresses, and phone-number patterns before writing the derived data. The selected 1,000 records are split once into:

- 300 tuning records (150 normal, 150 spam)
- 700 final evaluation records (350 normal, 350 spam)

The evaluation file is generated under `mlops_data/` and is ignored by Git. It is never read during candidate selection or parameter tuning. The final evaluation is run once after the candidate is selected by 3-fold F1 cross-validation on the 30 tuning records.

## Reproduction

```powershell
python -m src.mlops_pipeline
```

Generated files include `mlops_data/metadata.json`, `mlops_data/tuning.csv`, `mlops_data/evaluation.csv`, `artifacts/model_comparison.json`, and the final `artifacts/spam_model.joblib`. These generated files are not source-controlled.

The dataset card notes that the data can contain inappropriate or political content. This project uses only a small, redacted derived sample and does not claim that the sample represents production traffic.
