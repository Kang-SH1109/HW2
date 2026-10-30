# AI 스팸 문자 탐지

로컬 Windows 환경에서 실행하는 FastAPI + scikit-learn 기반 예제 앱입니다. TF-IDF 문자 n-gram과 Logistic Regression을 사용해 문자 메시지를 `spam` 또는 `normal`로 분류합니다.

## 실행 방법

PowerShell에서 프로젝트 폴더로 이동한 뒤 다음 명령어를 차례대로 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.train
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

브라우저에서 다음 주소를 엽니다.

http://127.0.0.1:8000

### 상태 확인

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

### 서버 종료

서버가 실행 중인 터미널에서 `Ctrl+C`를 누릅니다.

포트 사용 여부는 다음 명령어로 확인할 수 있습니다.

```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
```

서버 종료 후 같은 명령어에서 결과가 나오지 않으면 포트가 해제된 것입니다.

## 학습과 한계

`src.train`은 UTF-8 CSV 파일을 읽고 stratified hold-out 방식으로 데이터를 분리한 뒤 모델과 `artifacts/metrics.json`을 저장합니다. 테스트 데이터는 학습에 사용하지 않습니다.

현재 `data/messages.csv`는 공개 데이터셋이 아니라 프로젝트에서 직접 작성한 24건의 검증용 예시 데이터입니다. 따라서 학습 결과는 실제 서비스의 성능을 대표하지 않습니다. 공개 데이터셋을 사용할 때는 해당 데이터셋의 라이선스와 개인정보 처리 조건을 확인해야 합니다.

평가 지표에는 accuracy, spam precision/recall/F1, confusion matrix가 포함됩니다.

모델 파일이 없거나 손상된 경우 서버는 `/api/health`에서 `model_loaded: false`를 반환하고, 예측 요청에는 HTTP 503을 반환합니다.

## 테스트

PowerShell에서 다음 명령어를 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

현재 확인한 테스트 항목은 API 상태, 빈 입력, 최대 길이 초과, 예측 응답 형식입니다.

자동 모델 교체 승인 및 롤백 기능과 실제 공개 데이터셋을 이용한 검증은 구현하지 않았습니다.
