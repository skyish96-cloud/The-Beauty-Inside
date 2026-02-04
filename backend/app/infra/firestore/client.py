import os
from firebase_admin import credentials, initialize_app

# 현재 파일(client.py) 위치에서 세 칸 위로 올라가면 backend 폴더입니다.
base_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(base_dir, "..", "..", "..", "serviceAccountKey.json")

cred = credentials.Certificate(json_path)
initialize_app(cred)