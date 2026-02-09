"""
Firebase 연예인 임베딩 동기화 - 통합 관리 스크립트

여러 시나리오를 지원:
  1. 초기 로드: Firebase → 로컬 파일 생성
  2. 증분 동기화: 로컬 유지 + Firebase 새로운 데이터만 추가
  3. 검증: 로컬 데이터 무결성 확인
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import csv
import numpy as np
import argparse

# Backend 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.infra.firestore.client import firestore_manager, init_firebase
from app.infra.celeb_store.paths import celeb_paths
from app.core.logger import get_logger

logger = get_logger(__name__)


class CelebEmbeddingSyncManager:
    """연예인 임베딩 동기화 관리자"""
    
    def __init__(self, mode: str = "sync"):
        """
        mode:
          - "sync": 전체 동기화 (덮어쓰기)
          - "merge": 병합 (로컬 유지)
          - "validate": 검증만 수행
        """
        self.mode = mode
        self.firebase_data: Dict = {}
        self.local_celebs: Dict = {}
        self.local_images: Dict = {}
    
    def print_header(self, title: str):
        """헤더 출력"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80 + "\n")
    
    def print_step(self, num: int, title: str):
        """스텝 출력"""
        print(f"[{num}] {title}")
    
    def print_success(self, msg: str, indent: int = 0):
        """성공 메시지"""
        prefix = "  " * indent
        print(f"{prefix}✓ {msg}")
    
    def print_error(self, msg: str, indent: int = 0):
        """에러 메시지"""
        prefix = "  " * indent
        print(f"{prefix}✗ {msg}")
    
    def print_info(self, msg: str, indent: int = 0):
        """정보 메시지"""
        prefix = "  " * indent
        print(f"{prefix}→ {msg}")
    
    # ===== Firebase 연결 =====
    
    def init_firebase_connection(self) -> bool:
        """Firebase 연결 초기화"""
        self.print_step(1, "Firebase 연결 중...")
        
        try:
            init_firebase()
            db = firestore_manager.client
            if db is None:
                raise Exception("Firestore 객체가 None")
            self.print_success("Firebase 연결 성공")
            return True
        except Exception as e:
            self.print_error(f"Firebase 연결 실패: {e}")
            return False
    
    # ===== Firebase 데이터 수집 =====
    
    def fetch_from_firebase(self) -> bool:
        """Firebase에서 모든 연예인 임베딩 데이터 수집"""
        self.print_step(2, "Firebase에서 연예인 데이터 수집 중...")
        
        try:
            db = firestore_manager.client
            if db is None:
                raise Exception("Firestore 연결 없음")
            
            collection = db.collection("celeb_embeddings")
            docs = list(collection.stream())
            
            if not docs:
                self.print_error("Firebase에 데이터가 없습니다")
                return False
            
            count = 0
            for doc in docs:
                count += 1
                celeb_id = doc.id
                data = doc.to_dict()
                
                # 메타 정보 추출
                self.firebase_data[celeb_id] = {
                    "name": data.get("name", ""),
                    "gender": data.get("gender"),
                    "birth_year": data.get("birth_year"),
                    "agency": data.get("agency"),
                    "image_path": data.get("image_path"),
                    "expression": data.get("expression", "neutral"),
                }
                
                # 임베딩 벡터 추출
                if "embedding" in data:
                    emb = data["embedding"]
                    if isinstance(emb, list):
                        self.firebase_data[celeb_id]["embedding"] = np.array(emb, dtype=np.float32)
                    elif isinstance(emb, np.ndarray):
                        self.firebase_data[celeb_id]["embedding"] = emb.astype(np.float32)
                
                if count % 200 == 0:
                    self.print_info(f"{count}명 수집 중...", indent=1)
            
            self.print_success(f"총 {count}명의 연예인 데이터 수집 완료")
            return True
            
        except Exception as e:
            self.print_error(f"Firebase 쿼리 실패: {e}")
            return False
    
    # ===== 로컬 데이터 로드 =====
    
    def load_local_files(self) -> bool:
        """로컬 CSV 파일 로드 (이미 존재하는 경우)"""
        self.print_step(3, "로컬 데이터 로드 중...")
        
        loaded = False
        
        # celebs.csv 로드
        if celeb_paths.celebs_csv.exists():
            try:
                with open(celeb_paths.celebs_csv, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        celeb_id = row.get("celeb_id", "")
                        self.local_celebs[celeb_id] = row
                self.print_info(f"celebs.csv: {len(self.local_celebs)}명", indent=1)
                loaded = True
            except Exception as e:
                self.print_error(f"celebs.csv 로드 실패: {e}", indent=1)
        else:
            self.print_info("celebs.csv 없음 (신규 생성)", indent=1)
        
        # images.csv 로드
        if celeb_paths.images_csv.exists():
            try:
                with open(celeb_paths.images_csv, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        celeb_id = row.get("celeb_id", "")
                        expr = row.get("expression", "neutral")
                        key = (celeb_id, expr)
                        self.local_images[key] = row
                self.print_info(f"images.csv: {len(self.local_images)}개", indent=1)
                loaded = True
            except Exception as e:
                self.print_error(f"images.csv 로드 실패: {e}", indent=1)
        else:
            self.print_info("images.csv 없음 (신규 생성)", indent=1)
        
        if not loaded:
            self.print_info("로컬 파일 없음 (초기 생성 모드)", indent=1)
        
        return True
    
    # ===== 병합 =====
    
    def merge_data(self) -> bool:
        """Firebase 데이터와 로컬 데이터 병합"""
        self.print_step(4, "데이터 병합 중...")
        
        merged_celebs = dict(self.local_celebs)
        merged_images = dict(self.local_images)
        
        new_celebs = 0
        new_images = 0
        updated_celebs = 0
        
        for celeb_id, fb_data in self.firebase_data.items():
            # Mode에 따라 처리
            if celeb_id not in merged_celebs:
                # 새로운 연예인
                merged_celebs[celeb_id] = {
                    "celeb_id": celeb_id,
                    "celeb_name": fb_data.get("name", celeb_id),
                    "name": fb_data.get("name", celeb_id),
                    "gender": fb_data.get("gender", ""),
                    "birth_year": fb_data.get("birth_year", ""),
                    "agency": fb_data.get("agency", "")
                }
                new_celebs += 1
            elif self.mode == "sync":
                # 동기화 모드: 기존 데이터 업데이트
                merged_celebs[celeb_id].update({
                    "gender": fb_data.get("gender", ""),
                    "birth_year": fb_data.get("birth_year", ""),
                    "agency": fb_data.get("agency", "")
                })
                updated_celebs += 1
            # merge 모드: 기존 데이터 유지
            
            # 이미지 데이터 추가
            expr = fb_data.get("expression", "neutral")
            key = (celeb_id, expr)
            if key not in merged_images:
                merged_images[key] = {
                    "celeb_id": celeb_id,
                    "image_path": fb_data.get("image_path", f"famous/{celeb_id}_{expr}.jpg"),
                    "expression": expr
                }
                new_images += 1
        
        self.print_info(f"신규 연예인: {new_celebs}명", indent=1)
        if updated_celebs > 0:
            self.print_info(f"업데이트된 연예인: {updated_celebs}명", indent=1)
        self.print_info(f"신규 이미지: {new_images}개", indent=1)
        self.print_success(f"최종: {len(merged_celebs)}명, {len(merged_images)}개 이미지")
        
        self.local_celebs = merged_celebs
        self.local_images = merged_images
        return True
    
    # ===== 파일 저장 =====
    
    def save_files(self) -> bool:
        """병합된 데이터를 파일로 저장"""
        self.print_step(5, "파일 저장 중...")
        
        try:
            # celebs.csv 저장
            self._save_celebs_csv()
            self.print_success("celebs.csv 저장 완료")
            
            # images.csv 저장
            self._save_images_csv()
            self.print_success("images.csv 저장 완료")
            
            # 임베딩 벡터 저장
            self._save_embeddings()
            self.print_success("임베딩 벡터 저장 완료")
            
            return True
        except Exception as e:
            self.print_error(f"파일 저장 실패: {e}")
            return False
    
    def _save_celebs_csv(self):
        """celebs.csv 저장"""
        fieldnames = ["celeb_id", "celeb_name", "name", "gender", "birth_year", "agency"]
        
        with open(celeb_paths.celebs_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, restval="")
            writer.writeheader()
            
            for celeb_id in sorted(self.local_celebs.keys()):
                row = self.local_celebs[celeb_id]
                writer.writerow({
                    "celeb_id": row.get("celeb_id", celeb_id),
                    "celeb_name": row.get("celeb_name", row.get("name", celeb_id)),
                    "name": row.get("name", celeb_id),
                    "gender": row.get("gender", ""),
                    "birth_year": row.get("birth_year", ""),
                    "agency": row.get("agency", "")
                })
    
    def _save_images_csv(self):
        """images.csv 저장"""
        fieldnames = ["celeb_id", "image_path", "expression"]
        
        with open(celeb_paths.images_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, restval="")
            writer.writeheader()
            
            for (celeb_id, expr) in sorted(self.local_images.keys()):
                row = self.local_images[(celeb_id, expr)]
                writer.writerow({
                    "celeb_id": row.get("celeb_id", celeb_id),
                    "image_path": row.get("image_path", ""),
                    "expression": row.get("expression", expr)
                })
    
    def _save_embeddings(self):
        """임베딩 벡터를 numpy 파일로 저장"""
        celeb_ids = sorted(self.local_celebs.keys())
        embeddings_list = []
        missing_count = 0
        
        for celeb_id in celeb_ids:
            if celeb_id in self.firebase_data and self.firebase_data[celeb_id].get("embedding") is not None:
                embeddings_list.append(self.firebase_data[celeb_id]["embedding"])
            else:
                # 임베딩 없으면 영벡터
                embeddings_list.append(np.zeros(512, dtype=np.float32))
                missing_count += 1
        
        embeddings = np.array(embeddings_list, dtype=np.float32)
        ids = np.array(celeb_ids, dtype=object)
        
        np.save(str(celeb_paths.embeddings_npy), embeddings)
        np.save(str(celeb_paths.ids_npy), ids)
        
        self.print_info(f"embed.npy: {embeddings.shape} {embeddings.dtype}", indent=1)
        self.print_info(f"ids.npy: {ids.shape}", indent=1)
        
        if missing_count > 0:
            self.print_info(f"⚠ {missing_count}명의 임베딩 누락 (영벡터 사용)", indent=1)
    
    # ===== 검증 =====
    
    def validate(self) -> bool:
        """로컬 데이터 검증"""
        self.print_step(6, "데이터 검증 중...")
        
        errors = []
        warnings = []
        
        try:
            # celebs.csv 검증
            if celeb_paths.celebs_csv.exists():
                with open(celeb_paths.celebs_csv, 'r', encoding='utf-8') as f:
                    celebs_count = sum(1 for _ in f) - 1  # 헤더 제외
                self.print_info(f"celebs.csv: {celebs_count}명", indent=1)
            
            # images.csv 검증
            if celeb_paths.images_csv.exists():
                with open(celeb_paths.images_csv, 'r', encoding='utf-8') as f:
                    images_count = sum(1 for _ in f) - 1  # 헤더 제외
                self.print_info(f"images.csv: {images_count}개", indent=1)
            
            # embed.npy 검증
            if celeb_paths.embeddings_npy.exists():
                embeddings = np.load(str(celeb_paths.embeddings_npy))
                self.print_info(f"embed.npy: {embeddings.shape} {embeddings.dtype}", indent=1)
                
                if embeddings.shape[1] != 512:
                    errors.append(f"임베딩 차원 오류: {embeddings.shape[1]} (예상: 512)")
            
            # ids.npy 검증
            if celeb_paths.ids_npy.exists():
                ids = np.load(str(celeb_paths.ids_npy), allow_pickle=True)
                self.print_info(f"ids.npy: {ids.shape}", indent=1)
            
            if errors:
                for err in errors:
                    self.print_error(err, indent=1)
                return False
            
            if warnings:
                for warn in warnings:
                    self.print_info(f"⚠ {warn}", indent=1)
            
            self.print_success("검증 완료 (오류 없음)")
            return True
            
        except Exception as e:
            self.print_error(f"검증 실패: {e}", indent=1)
            return False
    
    # ===== 메인 실행 =====
    
    def run(self) -> bool:
        """전체 동기화 실행"""
        self.print_header(f"Firebase 연예인 임베딩 동기화 ({self.mode.upper()} 모드)")
        
        # 1. Firebase 연결
        if not self.init_firebase_connection():
            return False
        
        # 2. Firebase 데이터 수집
        if not self.fetch_from_firebase():
            return False
        
        # 3. 로컬 데이터 로드 (merge 모드일 때만)
        if self.mode in ["merge", "sync"]:
            if not self.load_local_files():
                return False
        
        # 4. 병합
        if not self.merge_data():
            return False
        
        # 5. 파일 저장
        if not self.save_files():
            return False
        
        # 6. 검증
        if not self.validate():
            return False
        
        # 완료
        self.print_header("✓ 동기화 완료!")
        print(f"📊 최종 결과:")
        print(f"  • 연예인: {len(self.local_celebs)}명")
        print(f"  • 이미지: {len(self.local_images)}개")
        print(f"  • 임베딩 벡터: {len(self.firebase_data)}명")
        print(f"  • 저장 위치: {celeb_paths.data_root}\n")
        
        return True


def main():
    """메인 진입점"""
    parser = argparse.ArgumentParser(
        description="Firebase 연예인 임베딩 동기화",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python manage_embeddings.py --mode sync        # 전체 동기화
  python manage_embeddings.py --mode merge       # 병합 (기존 유지)
  python manage_embeddings.py --mode validate    # 검증만
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["sync", "merge", "validate"],
        default="sync",
        help="동기화 모드 (기본값: sync)"
    )
    
    args = parser.parse_args()
    
    manager = CelebEmbeddingSyncManager(mode=args.mode)
    success = manager.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
