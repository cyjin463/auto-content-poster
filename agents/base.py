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
    
    # 클래스 레벨에서 API 키 목록과 현재 인덱스 관리
    _api_keys = []
    _current_key_index = 0
    _keys_initialized = False
    
    @classmethod
    def _initialize_api_keys(cls):
        """API 키 목록 초기화 (GROQ_API_KEY, GROQ_API_KEY_1만 지원)"""
        if cls._keys_initialized:
            return
        
        # GROQ_API_KEY와 GROQ_API_KEY_1만 사용
        keys = []
        primary_key = os.getenv("GROQ_API_KEY")
        if primary_key:
            keys.append(primary_key)
        
        # GROQ_API_KEY_1만 추가
        key1 = os.getenv("GROQ_API_KEY_1")
        if key1:
            keys.append(key1)
        
        cls._api_keys = keys
        cls._keys_initialized = True
        
        if keys:
            key_info = "GROQ_API_KEY"
            if len(keys) > 1:
                key_info += " + GROQ_API_KEY_1"
            print(f"  🔑 Groq API 키 {len(keys)}개 로드됨 ({key_info})")
    
    @classmethod
    def _get_next_api_key(cls) -> Optional[str]:
        """다음 사용 가능한 API 키 가져오기 (순환)"""
        cls._initialize_api_keys()
        
        if not cls._api_keys:
            return None
        
        # 현재 인덱스의 키 반환 후 다음으로 이동
        key = cls._api_keys[cls._current_key_index]
        cls._current_key_index = (cls._current_key_index + 1) % len(cls._api_keys)
        return key
    
    @classmethod
    def _reset_key_index(cls):
        """키 인덱스를 처음으로 리셋"""
        cls._current_key_index = 0
    
    def __init__(self, name: str, model: str = "llama-3.3-70b-versatile", require_api_key: bool = True):
        self.name = name
        self.model = model
        
        if require_api_key:
            self._initialize_api_keys()
            if not self._api_keys:
                raise ValueError(f"{self.name}: GROQ_API_KEY 환경 변수가 설정되지 않았습니다.")
        else:
            self.api_key = None
    
    def _call_groq(self, messages: List[Dict[str, str]], response_format: Optional[Dict] = None, max_retries: int = None) -> str:
        """Groq API 호출 (여러 키 순환 사용)"""
        import requests
        
        self._initialize_api_keys()
        
        if not self._api_keys:
            raise ValueError("GROQ_API_KEY가 설정되지 않았습니다.")
        
        # max_retries가 None이면 키 개수만큼 시도 (최대 2개: GROQ_API_KEY, GROQ_API_KEY_1)
        if max_retries is None:
            max_retries = min(len(self._api_keys), 2)  # 최대 2개 키만 시도
        
        last_error = None
        tried_keys = set()
        
        # 키 인덱스 초기화 (매 호출마다 처음부터 시작)
        self._reset_key_index()
        
        # 최대 재시도 횟수만큼 다른 키로 시도
        for attempt in range(max_retries):
            # 사용 가능한 키 찾기 (순서대로: GROQ_API_KEY 먼저, 그 다음 GROQ_API_KEY_1)
            api_key = None
            
            # 첫 번째 키부터 시도
            if len(self._api_keys) > 0 and self._api_keys[0] not in tried_keys:
                api_key = self._api_keys[0]
                tried_keys.add(api_key)
            elif len(self._api_keys) > 1 and self._api_keys[1] not in tried_keys:
                api_key = self._api_keys[1]
                tried_keys.add(api_key)
            
            if not api_key:
                # 모든 키를 시도했지만 실패
                break
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
            }
            
            if response_format:
                payload["response_format"] = response_format
            
            try:
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                
                if response.ok:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                
                # Rate Limit 체크
                error_text = response.text
                if "rate_limit" in error_text.lower() or "Rate limit" in error_text or response.status_code == 429:
                    # Rate Limit이면 다음 키로 시도
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("error", {}).get("message", error_text)
                    
                    # 다음 키가 있는지 확인
                    has_next_key = False
                    if len(self._api_keys) > attempt + 1:
                        has_next_key = True
                    
                    if has_next_key:
                        current_key_name = "GROQ_API_KEY" if attempt == 0 else f"GROQ_API_KEY_1"
                        next_key_name = "GROQ_API_KEY_1" if attempt == 0 else None
                        print(f"  ⚠️  {current_key_name} Rate Limit 감지")
                        if next_key_name:
                            print(f"  🔄 {next_key_name}로 전환 시도 중... (시도 {attempt + 1}/{max_retries})")
                    else:
                        print(f"  ⚠️  모든 API 키 Rate Limit 감지 (시도 {attempt + 1}/{max_retries})")
                        print(f"  ⏭️  다음날 재시도 예정")
                    
                    last_error = Exception(f"Groq API Rate Limit: {error_msg}")
                    continue
                else:
                    # 다른 종류의 에러는 즉시 실패
                    raise Exception(f"Groq API 오류: {error_text}")
            
            except Exception as e:
                # 네트워크 에러 등은 다음 키로 시도
                if "Rate limit" in str(e) or "rate_limit" in str(e).lower():
                    # 다음 키가 있는지 확인
                    has_next_key = False
                    if len(self._api_keys) > attempt + 1:
                        has_next_key = True
                    
                    if has_next_key:
                        current_key_name = "GROQ_API_KEY" if attempt == 0 else f"GROQ_API_KEY_1"
                        next_key_name = "GROQ_API_KEY_1" if attempt == 0 else None
                        print(f"  ⚠️  {current_key_name} Rate Limit 감지")
                        if next_key_name:
                            print(f"  🔄 {next_key_name}로 전환 시도 중... (시도 {attempt + 1}/{max_retries})")
                    else:
                        print(f"  ⚠️  모든 API 키 Rate Limit 감지 (시도 {attempt + 1}/{max_retries})")
                        print(f"  ⏭️  다음날 재시도 예정")
                    
                    last_error = e
                    continue
                else:
                    raise
        
        # 모든 키가 실패한 경우
        if last_error:
            raise last_error
        else:
            raise Exception("모든 Groq API 키가 사용 불가능합니다.")
    
    @abstractmethod
    def process(self, input_data: Any) -> Dict[str, Any]:
        """에이전트 처리 로직 (하위 클래스에서 구현)"""
        pass
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """출력 검증 (선택적)"""
        return True

