"""
기본 AI 에이전트 클래스
"""

import os
import json
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod


def load_env_file():
    """.env 파일에서 환경 변수 로드"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and value:
                        os.environ[key] = value


# .env 파일 로드
load_env_file()


class BaseAgent(ABC):
    """기본 AI 에이전트 클래스"""
    
    def __init__(self, name: str, model: str = "llama-3.3-70b-versatile", require_api_key: bool = True):
        self.name = name
        self.model = model
        
        if require_api_key:
            self.api_key = os.getenv("GROQ_API_KEY")
            if not self.api_key:
                raise ValueError(f"{self.name}: GROQ_API_KEY 환경 변수가 설정되지 않았습니다.")
        else:
            self.api_key = None
    
    def _call_groq(self, messages: List[Dict[str, str]], response_format: Optional[Dict] = None) -> str:
        """Groq API 호출"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
        }
        
        if response_format:
            payload["response_format"] = response_format
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if not response.ok:
            error_text = response.text
            raise Exception(f"Groq API 오류: {error_text}")
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    @abstractmethod
    def process(self, input_data: Any) -> Dict[str, Any]:
        """에이전트 처리 로직 (하위 클래스에서 구현)"""
        pass
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """출력 검증 (선택적)"""
        return True

