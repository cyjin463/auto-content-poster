"""
환경 변수 및 설정 관리
"""
import os
from pathlib import Path


def load_env_file(env_path: str = None):
    """
    .env 파일에서 환경 변수 로드
    
    Args:
        env_path: .env 파일 경로 (None이면 프로젝트 루트에서 자동 검색)
    """
    if env_path is None:
        # 현재 파일 기준으로 프로젝트 루트 찾기
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent  # src/core -> src -> project_root
        env_path = project_root / '.env'
    else:
        env_path = Path(env_path)
    
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and value:
                        os.environ[key] = value


def get_project_root() -> Path:
    """프로젝트 루트 디렉토리 경로 반환"""
    return Path(__file__).parent.parent.parent

