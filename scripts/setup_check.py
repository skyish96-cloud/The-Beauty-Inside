#!/usr/bin/env python3
"""
Firebase 설정 및 연결 검증 도구

용도:
  1. Python 환경 확인
  2. 의존성 설치 확인
  3. 서비스 키 파일 경로 설정 확인
  4. Firebase 초기화 상태 확인
  5. Firestore 연결 테스트
"""

import sys
import os
from pathlib import Path
import traceback

# Backend 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.logger import get_logger
from app.core.config import settings
from app.infra.firestore.client import (
    is_firebase_enabled, 
    _get_credentials_path, 
    init_firebase, 
    firestore_manager
)

logger = get_logger(__name__)

class Color:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


class SetupChecker:
    """설정 및 연결 검증"""
    
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def print_header(self, title: str):
        print(f"\n{Color.BOLD}{Color.BLUE}{'=' * 80}{Color.RESET}")
        print(f"{Color.BOLD}{Color.BLUE}  {title}{Color.RESET}")
        print(f"{Color.BOLD}{Color.BLUE}{'=' * 80}{Color.RESET}\n")
    
    def check_pass(self, name: str, details: str = ""):
        self.passed.append(name)
        msg = f"{Color.GREEN}✓{Color.RESET} {name}"
        if details:
            msg += f"\n    {details}"
        print(msg)
    
    def check_fail(self, name: str, details: str = ""):
        self.failed.append(name)
        msg = f"{Color.RED}✗{Color.RESET} {name}"
        if details:
            msg += f"\n    {details}"
        print(msg)
    
    def check_warning(self, name: str, details: str = ""):
        self.warnings.append(name)
        msg = f"{Color.YELLOW}⚠{Color.RESET} {name}"
        if details:
            msg += f"\n    {details}"
        print(msg)
    
    def run(self):
        """모든 검사 실행"""
        self.check_python_version()
        self.check_dependencies()
        self.check_config_settings()
        self.check_credentials_path()
        self.check_firebase_init()
        self.check_firestore_connection()
        self.print_summary()
    
    def check_python_version(self):
        """Python 버전 확인"""
        self.print_header("1️⃣  Python 환경")
        
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info >= (3, 9):
            self.check_pass("Python 버전", f"v{version}")
        else:
            self.check_fail("Python 버전", f"v{version} (3.9+ 필요)")
    
    def check_dependencies(self):
        """의존성 확인"""
        self.print_header("2️⃣  의존성 확인")
        
        dependencies = [
            ("firebase-admin", "firebase_admin"),
            ("pydantic", "pydantic"),
            ("pydantic-settings", "pydantic_settings"),
            ("numpy", "numpy"),
        ]
        
        for package_name, import_name in dependencies:
            try:
                __import__(import_name)
                self.check_pass(f"{package_name} 설치됨")
            except ImportError:
                self.check_fail(f"{package_name} 미설치", 
                               f"실행: pip install {package_name}")
    
    def check_config_settings(self):
        """설정 확인"""
        self.print_header("3️⃣  설정값 확인")
        
        print("현재 설정값:")
        print(f"  • firebase_credentials_path: {settings.firebase_credentials_path}")
        print(f"  • firebase_project_id: {settings.firebase_project_id}")
        print()
        
        if settings.firebase_project_id:
            self.check_pass("Firebase Project ID", 
                           f"'{settings.firebase_project_id}'")
        else:
            self.check_warning("Firebase Project ID 미설정",
                              "env 파일 확인 또는 자동 감지 진행 중")
        
        if settings.firebase_credentials_path:
            self.check_pass("Credentials Path 설정",
                           f"'{settings.firebase_credentials_path}'")
        else:
            self.check_warning("Credentials Path 미설정",
                              "자동 감지 시도")
    
    def check_credentials_path(self):
        """서비스 키 파일 경로 확인"""
        self.print_header("4️⃣  서비스 키 파일")
        
        cred_path = _get_credentials_path()
        
        if cred_path:
            print(f"찾은 경로: {Color.BOLD}{cred_path}{Color.RESET}\n")
            
            if os.path.exists(cred_path):
                file_size = os.path.getsize(cred_path)
                self.check_pass("파일 존재",
                               f"{file_size:,} bytes")
                
                # 파일 유효성 확인
                try:
                    with open(cred_path, 'r') as f:
                        content = f.read()
                        if '"type": "service_account"' in content:
                            self.check_pass("파일 형식", "유효한 서비스 계정 키")
                        else:
                            self.check_warning("파일 형식",
                                              "서비스 계정 키로 보이지 않음")
                except Exception as e:
                    self.check_fail("파일 읽기", str(e))
            else:
                self.check_fail("파일 존재 확인 실패",
                               f"경로는 찾았으나 파일이 없음")
        else:
            self.check_fail("파일 감지 실패",
                           "backend/serviceAccountKey.json 확인\n"
                           "또는 FIREBASE_CREDENTIALS_PATH 환경변수 설정")
    
    def check_firebase_init(self):
        """Firebase 초기화 확인"""
        self.print_header("5️⃣  Firebase 초기화")
        
        try:
            enabled = is_firebase_enabled()
            print(f"Firebase 활성화: {Color.BOLD}{enabled}{Color.RESET}\n")
            
            if enabled:
                self.check_pass("활성화 상태", "자동 감지 또는 설정값")
                
                try:
                    init_firebase()
                    self.check_pass("초기화 완료", "Firebase Admin SDK 준비됨")
                except Exception as e:
                    self.check_fail("초기화 실패", str(e))
            else:
                self.check_fail("미활성화",
                               "서비스 키를 찾을 수 없거나\n"
                               "FIREBASE_PROJECT_ID가 미설정")
        except Exception as e:
            self.check_fail("상태 확인 실패", str(e))
            traceback.print_exc()
    
    def check_firestore_connection(self):
        """Firestore 연결 확인"""
        self.print_header("6️⃣  Firestore 연결")
        
        try:
            print(f"Manager.enabled: {Color.BOLD}{firestore_manager.enabled}{Color.RESET}\n")
            
            if firestore_manager.enabled:
                self.check_pass("Manager 활성화됨")
                
                # 클라이언트 접근
                client = firestore_manager.client
                
                if client:
                    self.check_pass("클라이언트 접근 성공",
                                   f"타입: {type(client).__name__}")
                    
                    # 컬렉션 조회 시도
                    try:
                        collections = list(client.collections())
                        if collections:
                            coll_names = [c.id for c in collections[:5]]
                            self.check_pass("컬렉션 조회 성공",
                                           f"샘플: {coll_names}")
                        else:
                            self.check_warning("컬렉션 조회",
                                              "Firestore가 비어있거나 권한 제한")
                    except Exception as e:
                        self.check_warning("컬렉션 조회", f"{e}")
                else:
                    self.check_fail("클라이언트 None",
                                   "활성화되었지만 클라이언트 반환 실패")
            else:
                self.check_fail("Manager 미활성화",
                               "Firebase가 활성화되지 않음")
        
        except Exception as e:
            self.check_fail("연결 테스트 실패", str(e))
            traceback.print_exc()
    
    def print_summary(self):
        """검사 결과 요약"""
        self.print_header("📊 결과 요약")
        
        total = len(self.passed) + len(self.failed) + len(self.warnings)
        
        print(f"{Color.GREEN}✓ 통과{Color.RESET}:  {len(self.passed)}/{total}")
        print(f"{Color.RED}✗ 실패{Color.RESET}:  {len(self.failed)}/{total}")
        print(f"{Color.YELLOW}⚠ 경고{Color.RESET}:  {len(self.warnings)}/{total}\n")
        
        if self.failed:
            print(f"{Color.RED}❌ 실패한 항목:{Color.RESET}")
            for item in self.failed:
                print(f"  • {item}")
        
        if self.warnings:
            print(f"\n{Color.YELLOW}⚠️  경고 항목:{Color.RESET}")
            for item in self.warnings:
                print(f"  • {item}")
        
        # 최종 상태
        print(f"\n{Color.BOLD}최종 상태:{Color.RESET}")
        if self.failed:
            print(f"{Color.RED}❌ Firebase 연결 불가{Color.RESET}")
            print(f"\n실패 항목을 해결한 후 다시 시도해주세요.")
        else:
            print(f"{Color.GREEN}✅ Firebase 준비 완료!{Color.RESET}")
            print(f"\n동기화 명령어:")
            print(f"  python scripts/sync_celeb_embeddings_simple.py")
            print(f"  python scripts/sync_celeb_embeddings_from_firebase.py")
            print(f"  python scripts/manage_embeddings.py")


def main():
    """메인 함수"""
    print(f"\n{Color.BOLD}{Color.BLUE}Firebase 설정 검증 도구{Color.RESET}")
    print(f"The Beauty Inside Project\n")
    
    checker = SetupChecker()
    checker.run()
    
    if checker.failed:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
