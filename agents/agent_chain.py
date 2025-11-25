"""
에이전트 체인: A2A 방식으로 여러 에이전트를 연결
"""

from typing import Dict, Any, List, Optional
from agents.search_agent import SearchAgent
from agents.validation_agent import SearchValidationAgent, ContentValidationAgent
from agents.fact_check_agent import FactCheckAgent, ContentRevisionAgent
from agents.content_agent import ContentGenerationAgent
from agents.posting_agent import PostingAgent


class AgentChain:
    """에이전트 체인 - A2A 방식"""
    
    def __init__(self):
        # 에이전트 초기화
        self.search_agent = SearchAgent()
        self.search_validation_agent = SearchValidationAgent()
        self.fact_check_agent = FactCheckAgent()
        self.content_agent = ContentGenerationAgent()
        self.content_validation_agent = ContentValidationAgent()
        self.content_revision_agent = ContentRevisionAgent()
        self.posting_agent = PostingAgent()
        
        # 실행 로그
        self.execution_log: List[Dict[str, Any]] = []
    
    def process(self, keyword: str, notion_page_id: Optional[str] = None, language: str = 'korean', skip_posting: bool = False) -> Dict[str, Any]:
        """
        전체 프로세스 실행:
        1. 검색 에이전트 → 검색 결과
        2. 검증 에이전트 → 검색 결과 검증
        3. 콘텐츠 생성 에이전트 → 콘텐츠 생성
        4. 검증 에이전트 → 콘텐츠 검증
        5. 포스팅 에이전트 → 노션 포스팅 준비
        """
        print(f"\n🚀 A2A 에이전트 체인 시작: '{keyword}'")
        print("=" * 60)
        
        try:
            # 1단계: 검색
            print("\n[1단계] 검색")
            search_result = self.search_agent.process({"keyword": keyword})
            self.execution_log.append({"step": "search", "result": search_result})
            
            if search_result["status"] != "success":
                return {
                    "status": "failed",
                    "step": "search",
                    "message": search_result.get("message", "검색 실패"),
                    "log": self.execution_log
                }
            
            # 2단계: 검색 결과 검증
            print("\n[2단계] 검색 결과 검증")
            validation_result = self.search_validation_agent.process(search_result)
            self.execution_log.append({"step": "search_validation", "result": validation_result})
            
            if not validation_result.get("is_valid", False):
                return {
                    "status": "failed",
                    "step": "validation",
                    "message": validation_result.get("reason", "검증 실패"),
                    "log": self.execution_log
                }
            
            # 2-1단계: 사실 확인 (검색 결과의 정확성 검증)
            print("\n[2-1단계] 사실 확인")
            fact_check_result = self.fact_check_agent.process(search_result)
            self.execution_log.append({"step": "fact_check", "result": fact_check_result})
            
            # 사실 확인 결과에 따라 필터링된 결과 사용
            validated_results = fact_check_result.get("filtered_results", validation_result["validated_results"])
            fact_check_issues = fact_check_result.get("issues", [])
            
            if fact_check_result.get("status") == "needs_review" and len(validated_results) == 0:
                return {
                    "status": "failed",
                    "step": "fact_check",
                    "message": "사실 확인 실패: 모든 검색 결과에 문제가 있습니다.",
                    "log": self.execution_log
                }
            
            # 3단계: 콘텐츠 생성
            print("\n[3단계] 콘텐츠 생성")
            content_input = {
                "keyword": keyword,
                "validated_results": validated_results,  # 사실 확인된 결과 사용
                "language": language,  # 언어 설정 전달
                "learning_story": True  # 학습 스토리 형식 활성화
            }
            content_result = self.content_agent.process(content_input)
            self.execution_log.append({"step": "content_generation", "result": content_result})
            
            if content_result["status"] != "success":
                return {
                    "status": "failed",
                    "step": "content_generation",
                    "message": "콘텐츠 생성 실패",
                    "log": self.execution_log
                }
            
            # 4단계: 콘텐츠 검증
            print("\n[4단계] 콘텐츠 검증")
            content_validation_input = {
                "keyword": keyword,
                "title": content_result["title"],
                "content": content_result["content"],
                "language": language  # 언어 설정 전달
            }
            content_validation_result = self.content_validation_agent.process(content_validation_input)
            self.execution_log.append({"step": "content_validation", "result": content_validation_result})
            
            # 검증 결과 및 사실 확인 이슈를 수정 에이전트에 전달
            content_to_revise = content_result["content"]
            revision_issues = []
            
            # 키워드/카테고리/출처/면책 섹션 분리 (수정 후 다시 추가하기 위해)
            import re
            footer_pattern = r'(\n\n## (?:참고 출처|References|카테고리|Category|관련 키워드|Related Keywords).*$)'
            footer_match = re.search(footer_pattern, content_to_revise, re.DOTALL)
            footer_section = footer_match.group(1) if footer_match else ""
            main_content = content_to_revise[:footer_match.start()] if footer_match else content_to_revise
            
            if content_validation_result.get("issues"):
                revision_issues.extend(content_validation_result["issues"])
            
            if fact_check_issues:
                revision_issues.extend(fact_check_issues)
            
            # 4-1단계: 콘텐츠 수정 (문제가 있는 경우)
            if revision_issues:
                print("\n[4-1단계] 콘텐츠 수정")
                revision_input = {
                    "content": main_content,  # 본문만 수정 (키워드/카테고리 제외)
                    "title": content_result["title"],
                    "issues": revision_issues,
                    "search_results": validated_results
                }
                revision_result = self.content_revision_agent.process(revision_input)
                self.execution_log.append({"step": "content_revision", "result": revision_result})
                
                if revision_result.get("status") == "revised":
                    content_to_revise = revision_result["revised_content"]
                    # 수정된 본문에 키워드/카테고리 섹션 다시 추가
                    if footer_section:
                        content_to_revise = content_to_revise + footer_section
                        print(f"  ✅ 콘텐츠 수정 완료 ({len(revision_result.get('revisions', []))}개 수정, 키워드/카테고리 섹션 유지)")
                    else:
                        print(f"  ✅ 콘텐츠 수정 완료 ({len(revision_result.get('revisions', []))}개 수정)")
                    # 수정된 콘텐츠로 업데이트
                    content_result["content"] = content_to_revise
                    content_result["revisions"] = revision_result.get("revisions", [])
            
            if not content_validation_result.get("is_valid", False) and not revision_issues:
                return {
                    "status": "failed",
                    "step": "content_validation",
                    "message": content_validation_result.get("reason", "콘텐츠 검증 실패"),
                    "log": self.execution_log,
                    "generated_content": content_result  # 검증 실패했지만 콘텐츠는 있음
                }
            
            # 5단계: 포스팅 (skip_posting이 False일 때만)
            posting_result = {
                "status": "skipped",
                "message": "포스팅 스킵됨 (auto_poster.py에서 처리)"
            }
            
            if not skip_posting:
                print("\n[5단계] 포스팅")
                posting_input = {
                    "title": content_result["title"],
                    "content": content_result["content"],
                    "parent_page_id": notion_page_id
                }
                
                # 환경 변수에서 parent_page_id 또는 database_id 가져오기
                import os
                env_parent_id = os.getenv("NOTION_PARENT_PAGE_ID")
                database_id = os.getenv("NOTION_DATABASE_ID")
                
                # notion_page_id가 없으면 환경 변수에서 가져오기
                if not posting_input["parent_page_id"] and env_parent_id:
                    posting_input["parent_page_id"] = env_parent_id
                
                # database_id도 전달 (있는 경우)
                if database_id:
                    posting_input["database_id"] = database_id
                
                posting_result = self.posting_agent.process(posting_input)
            else:
                print("\n[5단계] 포스팅 스킵됨 (auto_poster.py에서 처리)")
            
            self.execution_log.append({"step": "posting", "result": posting_result})
            
            print("\n" + "=" * 60)
            print("✅ A2A 에이전트 체인 완료!")
            
            return {
                "status": "success",
                "generated_content": content_result,
                "posting_info": posting_result,
                "quality_scores": {
                    "search_quality": validation_result.get("quality_score", 0),
                    "fact_accuracy": fact_check_result.get("accuracy_score", 0),
                    "content_quality": content_validation_result.get("quality_score", 0)
                },
                "revisions": content_result.get("revisions", []),
                "fact_check_issues": fact_check_issues,
                "log": self.execution_log
            }
            
        except Exception as e:
            print(f"\n❌ 에러 발생: {e}")
            self.execution_log.append({"step": "error", "error": str(e)})
            return {
                "status": "error",
                "message": str(e),
                "log": self.execution_log
            }

