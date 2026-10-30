# AI 스팸 문자 탐지

로컬 Windows에서 실행하는 FastAPI + scikit-learn 예제 앱입니다. TF-IDF 문자 n-gram과 Logistic Regression으로 `spam`/`normal`을 분류합니다.

## 실행

PowerShell에서 프로젝트 폴더로 이동한 뒤:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.train
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

브라우저: http://127.0.0.1:8000

상태 확인: `Invoke-RestMethod http://127.0.0.1:8000/api/health`

종료: 서버 창에서 `Ctrl+C`. 포트 확인: `Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue`. 종료 후 같은 명령 결과가 없으면 포트가 해제된 것입니다.

## 학습과 한계

`src.train`은 UTF-8 CSV를 읽고 stratified hold-out으로 분리한 뒤 모델, `artifacts/metrics.json`을 저장합니다. 테스트 데이터는 학습에 사용하지 않습니다. 현재 `data/messages.csv`는 공개 데이터셋이 아니라 프로젝트가 직접 작성한 24건 검증용 예시 데이터입니다. 따라서 학습 결과는 실제 서비스 성능을 대표하지 않습니다. 공개 데이터셋을 사용할 때는 별도 라이선스와 개인정보 처리 조건을 확인해야 합니다.

평가에는 accuracy, spam precision/recall/F1, confusion matrix가 포함됩니다. 모델 파일이 없거나 손상되면 서버는 `/api/health`에서 `model_loaded: false`를 반환하고 예측 요청은 503을 반환합니다.

## 테스트

```powershell
.\\.venv\\Scripts\\python.exe -m pytest -q
```

현재 확인한 테스트는 API 상태, 빈 입력, 최대 길이 초과, 예측 응답 형식입니다. 자동 모델 교체 승인/롤백과 실제 공개 데이터셋 검증은 구현하지 않았습니다.
