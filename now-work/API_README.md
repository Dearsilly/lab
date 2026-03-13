# Essay Scoring API Documentation

## Flask-RESTful API Style

Flask-RESTful 是 Flask 的一个扩展，提供以下特性：
- **Resource-based**: 每个端点是一个 Resource 类
- **HTTP 方法映射**: GET/POST/PUT/DELETE 自动路由
- **请求解析**: 使用 RequestParser 自动验证和解析参数
- **响应格式化**: 统一的 JSON 响应

## Project Structure
```
now-work/
├── data/
│   └── training_set_rel3.tsv
├── output/
│   ├── best_model.pt
│   └── score_params.json
├── model.py              # 模型加载与预测
├── app.py                # Flask-RESTful API
├── requirements.txt
├── Dockerfile
└── API_README.md
```

## API Endpoints

### 1. Health Check
**GET** `/health`
```bash
curl http://localhost:5000/health
```
Response:
```json
{
  "status": "healthy",
  "device": "cuda",
  "model_loaded": true
}
```

### 2. Predict Essay Score
**POST** `/predict`
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"essay": "Your essay text here...", "essay_set": 1}'
```

Request body:
```json
{
  "essay": "Dear local newspaper, I believe that computers have...",
  "essay_set": 1  // Optional, must be 1-8
}
```

Response:
```json
{
  "predicted_score": 8.5,
  "essay_set": 1,
  "score_range": [2, 12]
}
```

### 3. Get Score Range for Specific Set
**GET** `/score-range/<essay_set>`
```bash
curl http://localhost:5000/score-range/1
```
Response:
```json
{
  "essay_set": 1,
  "score_range": [2, 12],
  "description": "Set 1 score range: 2-12"
}
```

### 4. Get All Score Ranges
**GET** `/score-ranges`
```bash
curl http://localhost:5000/score-ranges
```
Response:
```json
{
  "score_ranges": {
    "1": [2, 12],
    "2": [1, 6],
    "3": [0, 3],
    "4": [0, 3],
    "5": [0, 4],
    "6": [0, 4],
    "7": [2, 24],
    "8": [10, 60]
  }
}
```

## Running the API

### Option 1: Direct Python
```bash
pip install -r requirements.txt
python app.py
```

### Option 2: Docker
```bash
docker build -t essay-scorer .
docker run -p 5000:5000 essay-scorer
```

### Option 3: Gunicorn (Production)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Sample Client Code

### Python
```python
import requests

# Predict essay score
response = requests.post('http://localhost:5000/predict', json={
    'essay': 'Your essay text here...',
    'essay_set': 1
})
result = response.json()
print(f"Predicted score: {result['predicted_score']}")
```

### JavaScript (Node.js)
```javascript
const axios = require('axios');

const response = await axios.post('http://localhost:5000/predict', {
    essay: 'Your essay text here...',
    essay_set: 1
});
console.log(response.data);
```

## Error Handling

- **400 Bad Request**: Missing required fields or invalid essay_set
- **500 Internal Server Error**: Model prediction failed

Example error response:
```json
{
  "error": "Missing essay text"
}
```
