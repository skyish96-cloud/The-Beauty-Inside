# Scoring Rules - 점수 규칙

## 개요
닮은 연예인 매칭 점수 계산 및 표정 분석 규칙입니다.

---

## 표정 분석

### 지원 표정
| 표정 | 영문 | 설명 |
|------|------|------|
| 무표정 | neutral | 기본 표정 |
| 웃음 | smile | 밝은 미소 |
| 슬픔 | sad | 슬픈 표정 |
| 놀람 | surprise | 놀란 표정 |

### 표정 감지 임계값
| 표정 | 임계값 | 설명 |
|------|--------|------|
| smile | 0.30 | 웃음으로 판정되는 최소 점수 |
| sad | 0.25 | 슬픔으로 판정되는 최소 점수 |
| surprise | 0.35 | 놀람으로 판정되는 최소 점수 |
| neutral | 기본값 | 다른 표정 점수가 낮을 때 |

### 블렌드쉐이프 가중치

#### Smile (웃음)
| 블렌드쉐이프 | 가중치 |
|-------------|--------|
| mouthSmileLeft | 0.30 |
| mouthSmileRight | 0.30 |
| cheekSquintLeft | 0.15 |
| cheekSquintRight | 0.15 |
| eyeSquintLeft | 0.05 |
| eyeSquintRight | 0.05 |

#### Sad (슬픔)
| 블렌드쉐이프 | 가중치 |
|-------------|--------|
| mouthFrownLeft | 0.25 |
| mouthFrownRight | 0.25 |
| browDownLeft | 0.15 |
| browDownRight | 0.15 |
| browInnerUp | 0.20 |

#### Surprise (놀람)
| 블렌드쉐이프 | 가중치 |
|-------------|--------|
| browOuterUpLeft | 0.20 |
| browOuterUpRight | 0.20 |
| eyeWideLeft | 0.15 |
| eyeWideRight | 0.15 |
| jawOpen | 0.15 |
| mouthOpen | 0.15 |

---

## 유사도 계산

### 코사인 유사도
두 얼굴 임베딩 벡터 간의 유사도를 계산합니다.

```
similarity = (A · B) / (||A|| × ||B||)
```

- 결과 범위: -1 ~ 1
- 1에 가까울수록 유사

### 점수 스케일링

원본 유사도(0~1)를 사용자 표시 점수(50~99)로 변환합니다.

#### Power Scale (기본)
```python
score = 50 + (similarity ^ 0.7) × 49
```

특징:
- 낮은 유사도를 상대적으로 높게 표시
- 사용자 경험 개선

#### 백분위 맵
| 유사도 | 표시 점수 |
|--------|----------|
| 30% | 50점 |
| 50% | 70점 |
| 70% | 85점 |
| 80% | 90점 |
| 90% | 95점 |
| 100% | 99점 |

---

## 품질 검사

### 임계값 설정
| 항목 | 임계값 | 설명 |
|------|--------|------|
| 최소 얼굴 크기 | 80px | 가로/세로 최소 크기 |
| 흐림 임계값 | 100 | Laplacian variance 기준 |
| 최소 밝기 | 40 | 0-255 스케일 |
| 최대 밝기 | 250 | 0-255 스케일 |
| 최대 얼굴 수 | 1명 | 단일 사용자만 허용 |

### 품질 플래그
| 플래그 | 설명 |
|--------|------|
| is_blurry | 이미지 흐림 |
| is_dark | 이미지 어두움 |
| is_bright | 이미지 밝음 |
| face_size_ok | 얼굴 크기 적절 |
| face_centered | 얼굴 중앙 위치 |

---

## 순위 결정

### Top-K 선정
1. 표정별 후보 필터링 (선택)
2. 코사인 유사도 계산
3. 유사도 내림차순 정렬
4. 최소 유사도 임계값(0.4) 적용
5. 상위 3명 선정

### 등급
| 순위 | 등급 | 색상 |
|------|------|------|
| 1위 | Gold (금) | #FFD700 |
| 2위 | Silver (은) | #C0C0C0 |
| 3위 | Bronze (동) | #CD7F32 |

---

## 설정 파라미터

### 환경 변수
```env
# 얼굴 분석
FACE_DETECTION_CONFIDENCE=0.7
FACE_EMBEDDING_MODEL=Facenet512
FACE_DETECTOR_BACKEND=retinaface

# 품질 검사
MIN_FACE_SIZE=80
BLUR_THRESHOLD=100
BRIGHTNESS_MIN=40
BRIGHTNESS_MAX=250

# 랭킹
TOP_K=3
SIMILARITY_THRESHOLD=0.4
```
