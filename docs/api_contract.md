# API Contract - WebSocket 통신 규약

## 개요
Beauty Inside API는 WebSocket을 통해 실시간 얼굴 분석을 제공합니다.

## 엔드포인트
- **URL**: `ws://[host]:[port]/ws/analyze`
- **프로토콜**: WebSocket

---

## 메시지 타입

### 클라이언트 → 서버

#### 1. analyze_request
이미지 분석 요청

```json
{
  "type": "analyze_request",
  "image_data": "data:image/jpeg;base64,/9j/4AAQ...",
  "session_id": "sess_20240115_a1b2c3d4"  // 선택사항
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| type | string | O | "analyze_request" |
| image_data | string | O | Base64 인코딩된 이미지 (data URL 형식 지원) |
| session_id | string | X | 세션 ID (없으면 서버에서 생성) |

#### 2. ping
연결 상태 확인

```json
{
  "type": "ping"
}
```

---

### 서버 → 클라이언트

#### 1. analyze_progress
분석 진행 상태

```json
{
  "type": "analyze_progress",
  "session_id": "sess_20240115_a1b2c3d4",
  "step": "expression_analyzed",
  "progress_percent": 50,
  "message": "표정 분석 완료"
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| step | string | 현재 단계 (received, face_detected, expression_analyzed, embedding_extracted, matching, completed) |
| progress_percent | int | 진행률 (0-100) |
| message | string | 사용자 표시용 메시지 |

#### 2. analyze_result
분석 결과

```json
{
  "type": "analyze_result",
  "session_id": "sess_20240115_a1b2c3d4",
  "detected_expression": "smile",
  "expression_confidence": 0.92,
  "matches": [
    {
      "celeb_id": "celeb_001",
      "name": "아이유",
      "similarity_score": 87.5,
      "rank": 1,
      "expression": "smile",
      "image_url": "/celebs/images/smile/celeb_001.jpg"
    },
    {
      "celeb_id": "celeb_002",
      "name": "수지",
      "similarity_score": 82.3,
      "rank": 2,
      "expression": "smile",
      "image_url": "/celebs/images/smile/celeb_002.jpg"
    },
    {
      "celeb_id": "celeb_003",
      "name": "태연",
      "similarity_score": 78.1,
      "rank": 3,
      "expression": "smile",
      "image_url": "/celebs/images/smile/celeb_003.jpg"
    }
  ],
  "quality_flags": {
    "is_blurry": false,
    "is_dark": false,
    "is_bright": false,
    "face_size_ok": true,
    "face_centered": true
  },
  "analysis_time_ms": 1234,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 3. error
에러 응답

```json
{
  "type": "error",
  "session_id": "sess_20240115_a1b2c3d4",
  "error_code": "E101",
  "message": "얼굴이 감지되지 않았습니다.",
  "details": {}
}
```

#### 4. pong
핑 응답

```json
{
  "type": "pong",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 분석 단계 (AnalyzeStep)

| 단계 | 값 | 진행률 | 설명 |
|------|-----|--------|------|
| 수신 완료 | received | 10% | 이미지 수신 및 디코딩 |
| 얼굴 감지 | face_detected | 25% | 얼굴 감지 완료 |
| 표정 분석 | expression_analyzed | 40% | 표정 분석 완료 |
| 특징 추출 | embedding_extracted | 60% | 얼굴 임베딩 추출 |
| 매칭 중 | matching | 80% | 유사 연예인 매칭 |
| 완료 | completed | 100% | 분석 완료 |

---

## 사용 예시

### JavaScript
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/analyze');

ws.onopen = () => {
  // 이미지 전송
  const imageData = canvas.toDataURL('image/jpeg', 0.8);
  ws.send(JSON.stringify({
    type: 'analyze_request',
    image_data: imageData
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'analyze_progress':
      updateProgress(data.progress_percent, data.message);
      break;
    case 'analyze_result':
      showResults(data.matches);
      break;
    case 'error':
      showError(data.message);
      break;
  }
};
```

---

## 제한사항

- **이미지 크기**: 최대 10MB
- **타임아웃**: 30초
- **지원 형식**: JPEG, PNG, WebP
- **최소 해상도**: 100x100 픽셀
- **최대 해상도**: 4096x4096 픽셀
