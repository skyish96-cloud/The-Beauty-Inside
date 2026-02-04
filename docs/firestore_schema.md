# Firestore Schema - 데이터베이스 구조

## 개요
Firebase Firestore를 사용한 분석 결과 저장 스키마입니다.

> **참고**: 원본 사용자 이미지는 저장하지 않습니다 (프라이버시 정책)

---

## 컬렉션 구조

### 1. sessions
세션 정보 저장

```
/sessions/{session_id}
```

#### 필드
| 필드 | 타입 | 설명 |
|------|------|------|
| session_id | string | 세션 고유 ID |
| created_at | timestamp | 생성 시각 |
| status | string | 상태 (active, completed, expired) |
| client_info | map | 클라이언트 정보 (선택) |

#### 예시
```json
{
  "session_id": "sess_20240115_a1b2c3d4",
  "created_at": "2024-01-15T10:30:00Z",
  "status": "completed",
  "client_info": {
    "user_agent": "Mozilla/5.0...",
    "platform": "web"
  }
}
```

---

### 2. analyses
분석 결과 저장

```
/analyses/{analysis_id}
```

#### 필드
| 필드 | 타입 | 설명 |
|------|------|------|
| analysis_id | string | 분석 고유 ID |
| session_id | string | 연결된 세션 ID |
| created_at | timestamp | 분석 시각 |
| detected_expression | string | 감지된 표정 |
| expression_confidence | number | 표정 신뢰도 (0-1) |
| quality_flags | map | 품질 플래그 |
| analysis_time_ms | number | 분석 시간 (ms) |

#### 예시
```json
{
  "analysis_id": "anal_a1b2c3d4e5f6",
  "session_id": "sess_20240115_a1b2c3d4",
  "created_at": "2024-01-15T10:30:05Z",
  "detected_expression": "smile",
  "expression_confidence": 0.92,
  "quality_flags": {
    "is_blurry": false,
    "is_dark": false,
    "is_bright": false,
    "face_size_ok": true,
    "face_centered": true
  },
  "analysis_time_ms": 1234
}
```

---

### 3. results
매칭 결과 저장

```
/results/{result_id}
```

#### 필드
| 필드 | 타입 | 설명 |
|------|------|------|
| result_id | string | 결과 고유 ID |
| analysis_id | string | 연결된 분석 ID |
| session_id | string | 연결된 세션 ID |
| created_at | timestamp | 생성 시각 |
| matches | array | 매칭 결과 배열 |

#### matches 배열 요소
| 필드 | 타입 | 설명 |
|------|------|------|
| celeb_id | string | 연예인 ID |
| celeb_name | string | 연예인 이름 |
| similarity_score | number | 유사도 점수 (0-100) |
| rank | number | 순위 (1, 2, 3) |
| expression | string | 매칭된 표정 |

#### 예시
```json
{
  "result_id": "rslt_a1b2c3d4e5f6",
  "analysis_id": "anal_a1b2c3d4e5f6",
  "session_id": "sess_20240115_a1b2c3d4",
  "created_at": "2024-01-15T10:30:05Z",
  "matches": [
    {
      "celeb_id": "celeb_001",
      "celeb_name": "아이유",
      "similarity_score": 87.5,
      "rank": 1,
      "expression": "smile"
    },
    {
      "celeb_id": "celeb_002",
      "celeb_name": "수지",
      "similarity_score": 82.3,
      "rank": 2,
      "expression": "smile"
    },
    {
      "celeb_id": "celeb_003",
      "celeb_name": "태연",
      "similarity_score": 78.1,
      "rank": 3,
      "expression": "smile"
    }
  ]
}
```

---

## ID 형식

### 세션 ID
```
sess_{YYYYMMDD}_{random8}
예: sess_20240115_a1b2c3d4
```

### 분석 ID
```
anal_{random12}
예: anal_a1b2c3d4e5f6
```

### 결과 ID
```
rslt_{random12}
예: rslt_a1b2c3d4e5f6
```

---

## 인덱스 설정

### 복합 인덱스
1. `analyses` - session_id + created_at (내림차순)
2. `results` - session_id + created_at (내림차순)

### 단일 인덱스
- `sessions.created_at`
- `sessions.status`

---

## 보안 규칙

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // 읽기 전용 (인증된 사용자)
    match /sessions/{sessionId} {
      allow read: if request.auth != null;
      allow write: if false; // 서버만 쓰기 가능
    }
    
    match /analyses/{analysisId} {
      allow read: if request.auth != null;
      allow write: if false;
    }
    
    match /results/{resultId} {
      allow read: if request.auth != null;
      allow write: if false;
    }
  }
}
```

---

## 데이터 보존 정책

| 컬렉션 | 보존 기간 | 설명 |
|--------|----------|------|
| sessions | 30일 | 비활성 세션 자동 삭제 |
| analyses | 90일 | 분석 기록 보관 |
| results | 90일 | 매칭 결과 보관 |

> **주의**: 사용자 이미지, 얼굴 임베딩 등 개인 정보는 저장하지 않습니다.
