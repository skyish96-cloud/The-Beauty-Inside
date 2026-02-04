from app.infra.firestore.client import db
from datetime import datetime

# 1. 실시간 분석 로그 저장 (Collection: analyses)
def save_analysis_log(session_id: str, label: str, score: float):
    doc_ref = db.collection("analyses").document()
    doc_ref.set({
        "session_id": session_id,
        "emotion_label": label,
        "emotion_score": score,
        "timestamp": datetime.utcnow()
    })

# 2. 최종 결과 저장 (Collection: results)
def save_final_result(session_id: str, matches: list):
    doc_ref = db.collection("results").document()
    doc_ref.set({
        "session_id": session_id,
        "top_matches": matches,
        "created_at": datetime.utcnow()
    })