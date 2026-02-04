본 문서는 프로젝트의 데이터 정합성을 유지하기 위해 작성되었습니다.</br>
**⚠️ 보안 주의: 사용자 원본 이미지는 절대 저장하지 않습니다.**

---

## 1. Collection: `analyses`
*사용자 표정 분석 실시간 로그*

| Field | Type | Description |
| :--- | :--- | :--- |
| `session_id` | `string` | 세션 고유 ID |
| `emotion_label` | `string` | 판정된 감정 (smile, sad, surprise 등) |
| `emotion_score` | `number` | 감정의 강도 (0~100) |
| `timestamp` | `timestamp` | 기록 시간 (서버 타임스탬프) |

---

## 2. Collection: `results`
*최종 유사도 분석 결과*

| Field | Type | Description |
| :--- | :--- | :--- |
| `session_id` | `string` | 해당 분석 세션 ID |
| `top_matches` | `array` | 상위 3명 리스트 (금/은/동) |
| └ `rank` | `string` | 순위 (gold, silver, bronze) |
| └ `celeb_id` | `string` | 연예인 고유 ID (c_001 형식 추천) |
| └ `celeb_name` | `string` | 연예인 이름 (표시용) |
| └ `similarity` | `number` | 코사인 유사도 점수 (0~100) |
| `created_at` | `timestamp` | 결과 생성 시간 |