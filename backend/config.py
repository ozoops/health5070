import os

# Fly.io 배포 환경에서는 /data 디렉토리를 사용하고, 로컬에서는 프로젝트 루트를 기준으로 합니다.
if os.environ.get('APP_ENV') == 'production':
    # 배포 환경: /data 디렉토리 사용
    data_dir = '/data'
else:
    # 로컬 환경: 프로젝트의 루트 디렉토리
    # 이 파일의 위치(backend/config.py)에서 두 단계 상위로 이동합니다.
    data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 영구 저장이 필요한 디렉토리 경로들
UPLOAD_DIR = os.path.join(data_dir, 'uploaded_videos')
FAISS_INDEX_DIR = os.path.join(data_dir, 'faiss_index')
GENERATED_VIDEOS_DIR = os.path.join(data_dir, 'generated_videos')
DB_PATH = os.path.join(data_dir, 'health_dongA.db')

# 애플리케이션 시작 시 디렉토리들이 존재하는지 확인하고 없으면 생성
def initialize_directories():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
    os.makedirs(GENERATED_VIDEOS_DIR, exist_ok=True)

# 이 함수는 애플리케이션의 메인 시작점에서 한 번 호출되어야 합니다.
# 예: app.py 또는 main streamlit 파일
