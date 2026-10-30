from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)
def test_health():
    r=client.get('/api/health'); assert r.status_code==200; assert 'status' in r.json()
def test_empty_input():
    r=client.post('/api/predict',json={'text':'   '}); assert r.status_code in (422,503)
def test_too_long_input():
    r=client.post('/api/predict',json={'text':'a'*2001}); assert r.status_code==422

def test_predict_shape():
    with TestClient(app) as running:
        r = running.post('/api/predict', json={'text': '무료 경품 당첨 링크를 눌러 주세요.'})
        assert r.status_code == 200
        assert r.json()['label'] in {'spam', 'normal'}
        assert 0 <= r.json()['score'] <= 100
