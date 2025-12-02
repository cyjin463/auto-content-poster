"""
SQLite 데이터베이스 관리
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path


class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 프로젝트 루트 기준으로 데이터베이스 경로 설정 (data/ 폴더)
            from src.core.config import get_project_root
            project_root = get_project_root()
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)  # data 폴더가 없으면 생성
            db_path = str(data_dir / "keywords.db")
        self.db_path = db_path
        self._init_db()
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """데이터베이스 초기화"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 키워드 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id TEXT PRIMARY KEY,
                keyword TEXT NOT NULL UNIQUE,
                is_active INTEGER DEFAULT 1,
                last_checked TEXT,
                last_posted TEXT,
                notion_page_id TEXT,
                parent_keyword_id TEXT,
                learning_level TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_keyword_id) REFERENCES keywords(id)
            )
        """)
        
        # 기존 테이블에 컬럼 추가 (없는 경우)
        try:
            cursor.execute("ALTER TABLE keywords ADD COLUMN parent_keyword_id TEXT")
        except sqlite3.OperationalError:
            pass  # 이미 존재하는 경우
        
        try:
            cursor.execute("ALTER TABLE keywords ADD COLUMN learning_level TEXT")
        except sqlite3.OperationalError:
            pass  # 이미 존재하는 경우
        
        # 포스트 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                keyword_id TEXT NOT NULL,
                search_results TEXT,
                status TEXT DEFAULT 'draft',
                notion_page_id TEXT,
                notion_page_url TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                published_at TEXT,
                language TEXT DEFAULT 'korean',
                FOREIGN KEY (keyword_id) REFERENCES keywords(id)
            )
        """)
        
        # language 컬럼 추가 (기존 테이블에 없는 경우)
        try:
            cursor.execute("ALTER TABLE posts ADD COLUMN language TEXT DEFAULT 'korean'")
        except sqlite3.OperationalError:
            pass  # 이미 존재하는 경우
        
        # 학습용 캐시 테이블 (최근 포스트 저장)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                language TEXT NOT NULL,
                post_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                cached_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(language, post_id),
                FOREIGN KEY (post_id) REFERENCES posts(id)
            )
        """)
        
        # 언어별 인덱스 추가 (빠른 조회용)
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_learning_cache_language ON learning_cache(language, cached_at DESC)")
        except sqlite3.OperationalError:
            pass
        
        conn.commit()
        conn.close()
    
    def get_keyword_learning_path(self, keyword_id: str) -> List[str]:
        """키워드의 학습 경로 조회 (부모부터 현재까지)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        path = []
        current_id = keyword_id
        
        # 최대 10단계까지 추적 (무한 루프 방지)
        for _ in range(10):
            cursor.execute("SELECT keyword, parent_keyword_id FROM keywords WHERE id = ?", (current_id,))
            row = cursor.fetchone()
            
            if not row:
                break
            
            path.insert(0, row['keyword'])
            
            if not row['parent_keyword_id']:
                break
            
            current_id = row['parent_keyword_id']
        
        conn.close()
        return path
    
    def get_recent_posts_for_keyword(self, keyword_id: str, limit: int = 5) -> List[Dict]:
        """키워드의 최근 포스팅 목록 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, content, created_at 
            FROM posts 
            WHERE keyword_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (keyword_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_recent_posts_by_language(self, language: str = 'korean', limit: int = 4, exclude_keyword_id: str = None) -> List[Dict]:
        """언어별 최근 포스팅 목록 조회 (현재 키워드 제외)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if exclude_keyword_id:
            cursor.execute("""
                SELECT title, content, created_at, keyword_id 
                FROM posts 
                WHERE language = ? AND keyword_id != ?
                ORDER BY created_at DESC 
                LIMIT ?
            """, (language, exclude_keyword_id, limit))
        else:
            cursor.execute("""
                SELECT title, content, created_at, keyword_id 
                FROM posts 
                WHERE language = ?
                ORDER BY created_at DESC 
                LIMIT ?
            """, (language, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_cached_posts_for_learning(self, language: str = 'korean', limit: int = 2) -> List[Dict]:
        """학습용 캐시된 포스트 조회 (Notion 참조 없음)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, content, cached_at 
            FROM learning_cache 
            WHERE language = ?
            ORDER BY cached_at DESC 
            LIMIT ?
        """, (language, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'title': row['title'],
                'content': row['content'],
                'created_at': row['cached_at']  # 호환성을 위해 created_at으로도 제공
            }
            for row in rows
        ]
    
    def update_learning_cache(self, post_id: str, language: str, title: str, content: str):
        """학습용 캐시 업데이트 (언어별 최근 2건 유지)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 해당 언어의 기존 캐시 확인
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM learning_cache 
            WHERE language = ?
        """, (language,))
        
        count = cursor.fetchone()['count']
        
        # 이미 존재하는 포스트면 업데이트, 없으면 추가
        cursor.execute("""
            INSERT OR REPLACE INTO learning_cache (language, post_id, title, content, cached_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (language, post_id, title, content))
        
        # 언어별 최대 2건만 유지 (가장 오래된 것 삭제)
        if count >= 2:
            cursor.execute("""
                DELETE FROM learning_cache 
                WHERE language = ? 
                AND id NOT IN (
                    SELECT id FROM learning_cache 
                    WHERE language = ? 
                    ORDER BY cached_at DESC 
                    LIMIT 2
                )
            """, (language, language))
        
        conn.commit()
        conn.close()
        
        print(f"  💾 학습용 캐시 업데이트 완료 ({language}, 최근 2건 유지)")
    
    def get_recent_posts_for_parent_keywords(self, keyword_id: str, limit: int = 10) -> List[Dict]:
        """부모 키워드들의 최근 포스팅 조회"""
        learning_path = self.get_keyword_learning_path(keyword_id)
        
        if len(learning_path) <= 1:
            return []
        
        # 부모 키워드들 찾기 (현재 키워드 제외)
        conn = self._get_connection()
        cursor = conn.cursor()
        
        parent_keywords = learning_path[:-1]  # 마지막(현재) 제외
        
        placeholders = ','.join(['?'] * len(parent_keywords))
        cursor.execute(f"""
            SELECT p.title, p.content, p.created_at, k.keyword
            FROM posts p
            JOIN keywords k ON p.keyword_id = k.id
            WHERE k.keyword IN ({placeholders})
            ORDER BY p.created_at DESC
            LIMIT ?
        """, (*parent_keywords, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def add_keyword(self, keyword: str, category: Optional[str] = None, notion_page_id: Optional[str] = None, parent_keyword_id: Optional[str] = None, learning_level: Optional[str] = None, is_active: bool = True, sequence_number: Optional[int] = None) -> str:
        """키워드 추가"""
        import uuid
        keyword_id = str(uuid.uuid4())
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 테이블 구조 확인
        cursor.execute("PRAGMA table_info(keywords)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        # 기본 필드
        fields = ["id", "keyword", "is_active"]
        values = [keyword_id, keyword, 1 if is_active else 0]
        
        # 선택적 필드 추가
        if 'notion_page_id' in columns and notion_page_id:
            fields.append("notion_page_id")
            values.append(notion_page_id)
        
        if 'parent_keyword_id' in columns and parent_keyword_id:
            fields.append("parent_keyword_id")
            values.append(parent_keyword_id)
        
        if 'learning_level' in columns and learning_level:
            fields.append("learning_level")
            values.append(learning_level)
        
        if 'sequence_number' in columns and sequence_number is not None:
            fields.append("sequence_number")
            values.append(sequence_number)
        
        placeholders = ','.join(['?'] * len(values))
        field_names = ','.join(fields)
        
        try:
            cursor.execute(f"""
                INSERT INTO keywords ({field_names})
                VALUES ({placeholders})
            """, values)
            conn.commit()
            return keyword_id
        except sqlite3.IntegrityError:
            raise ValueError(f"키워드 '{keyword}'는 이미 존재합니다.")
        finally:
            conn.close()
    
    def list_keywords(self) -> List[Dict]:
        """키워드 목록 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                k.*,
                COUNT(p.id) as posts_count,
                MAX(p.created_at) as last_posted
            FROM keywords k
            LEFT JOIN posts p ON k.id = p.keyword_id
            GROUP BY k.id
            ORDER BY k.created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row['id'],
                'keyword': row['keyword'],
                'is_active': bool(row['is_active']),
                'last_checked': row['last_checked'],
                'last_posted': row['last_posted'],
                'notion_page_id': row['notion_page_id'],
                'posts_count': row['posts_count'],
            }
            for row in rows
        ]
    
    def get_keyword_by_name(self, keyword: str) -> Optional[Dict]:
        """키워드명으로 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM keywords WHERE keyword = ?", (keyword,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row['id'],
                'keyword': row['keyword'],
                'is_active': bool(row['is_active']),
                'last_checked': row['last_checked'],
                'last_posted': row['last_posted'],
                'notion_page_id': row['notion_page_id'],
            }
        return None
    
    def get_active_keywords(self) -> List[Dict]:
        """활성 키워드 목록"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM keywords WHERE is_active = 1")
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row['id'],
                'keyword': row['keyword'],
                'is_active': bool(row['is_active']),
                'last_checked': row['last_checked'],
                'last_posted': row['last_posted'],
                'notion_page_id': row['notion_page_id'],
            }
            for row in rows
        ]
    
    def get_first_active_keyword(self) -> Optional[Dict]:
        """첫 번째 활성 키워드만 조회 (하나만)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM keywords 
            WHERE is_active = 1 
            ORDER BY created_at ASC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row['id'],
                'keyword': row['keyword'],
                'is_active': bool(row['is_active']),
                'last_checked': row['last_checked'],
                'last_posted': row['last_posted'],
                'notion_page_id': row['notion_page_id'],
            }
        return None
    
    def delete_keyword_by_name(self, keyword: str) -> bool:
        """키워드 삭제"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM keywords WHERE keyword = ?", (keyword,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    def toggle_keyword(self, keyword: str) -> Optional[Dict]:
        """키워드 활성화/비활성화"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT is_active FROM keywords WHERE keyword = ?", (keyword,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        new_status = 0 if row['is_active'] else 1
        cursor.execute(
            "UPDATE keywords SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE keyword = ?",
            (new_status, keyword)
        )
        conn.commit()
        conn.close()
        
        return {'is_active': bool(new_status)}
    
    def check_duplicate_post(self, keyword_id: str, title: str) -> bool:
        """중복 포스트 체크 (제목 기준)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 오늘 생성된 포스트 중 동일한 제목이 있는지 확인
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM posts 
            WHERE keyword_id = ? 
            AND title = ? 
            AND date(created_at) = ?
        """, (keyword_id, title, today))
        
        row = cursor.fetchone()
        conn.close()
        
        return row['count'] > 0
    
    def check_duplicate_content(self, keyword_id: str, content_hash: str) -> bool:
        """중복 콘텐츠 체크 (내용 해시 기준)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 오늘 생성된 포스트 중 동일한 내용 해시가 있는지 확인
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM posts 
            WHERE keyword_id = ? 
            AND content LIKE ?
            AND date(created_at) = ?
        """, (keyword_id, f'%{content_hash[:50]}%', today))
        
        row = cursor.fetchone()
        conn.close()
        
        return row['count'] > 0
    
    def create_post(self, keyword_id: str, title: str, content: str, 
                   search_results: List[Dict], status: str = 'draft', language: str = 'korean') -> str:
        """포스트 생성 (중복 체크 포함)"""
        import uuid
        import hashlib
        
        # 중복 체크
        if self.check_duplicate_post(keyword_id, title):
            raise ValueError(f"중복 포스트: '{title}' 제목의 포스트가 이미 오늘 생성되었습니다.")
        
        # 내용 해시 기반 중복 체크
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        if self.check_duplicate_content(keyword_id, content[:100]):  # 내용 시작 부분으로 체크
            raise ValueError("중복 포스트: 유사한 내용의 포스트가 이미 오늘 생성되었습니다.")
        
        post_id = str(uuid.uuid4())
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO posts (id, keyword_id, title, content, search_results, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (post_id, keyword_id, title, content, json.dumps(search_results), status))
        
        conn.commit()
        conn.close()
        
        return post_id
    
    def update_keyword_last_checked(self, keyword_id: str):
        """키워드 마지막 확인 시간 업데이트 (한국 시간 KST 기준)"""
        from datetime import timezone, timedelta
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 한국 시간(KST, UTC+9) 기준으로 현재 시간 저장
        kst = timezone(timedelta(hours=9))
        now_kst = datetime.now(kst)
        timestamp_str = now_kst.isoformat()
        
        cursor.execute("""
            UPDATE keywords 
            SET last_checked = ?, updated_at = ?
            WHERE id = ?
        """, (timestamp_str, timestamp_str, keyword_id))
        
        conn.commit()
        conn.close()
    
    def update_keyword_last_posted(self, keyword_id: str):
        """키워드 마지막 포스팅 시간 업데이트 (한국 시간 KST 기준)"""
        from datetime import timezone, timedelta
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 한국 시간(KST, UTC+9) 기준으로 현재 시간 저장
        kst = timezone(timedelta(hours=9))
        now_kst = datetime.now(kst)
        timestamp_str = now_kst.isoformat()
        
        cursor.execute("""
            UPDATE keywords 
            SET last_posted = ?, updated_at = ?
            WHERE id = ?
        """, (timestamp_str, timestamp_str, keyword_id))
        
        conn.commit()
        conn.close()
    
    def get_keyword_last_posted(self, keyword_id: str) -> Optional[datetime]:
        """키워드 마지막 포스팅 시간 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT last_posted FROM keywords WHERE id = ?", (keyword_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row and row['last_posted']:
            return datetime.fromisoformat(row['last_posted'])
        return None
    
    def get_draft_posts(self) -> List[Dict]:
        """draft 상태 포스트 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*, k.keyword, k.notion_page_id
            FROM posts p
            JOIN keywords k ON p.keyword_id = k.id
            WHERE p.status = 'draft'
            ORDER BY p.created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row['id'],
                'title': row['title'],
                'content': row['content'],
                'keyword': row['keyword'],
                'keyword_id': row['keyword_id'],
                'parent_page_id': row['notion_page_id'],
                'created_at': row['created_at'],
            }
            for row in rows
        ]
    
    def update_post_published(self, post_id: str, notion_page_id: str, notion_page_url: str):
        """포스트를 published 상태로 업데이트"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE posts 
            SET status = 'published',
                notion_page_id = ?,
                notion_page_url = ?,
                published_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (notion_page_id, notion_page_url, post_id))
        
        conn.commit()
        conn.close()

