import os
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse, unquote, urlencode

import aiofiles

from app.core.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class FileHandler:
    """첨부파일 처리 클래스"""
    
    def __init__(self, download_dir: str = "./downloads"):
        """
        FileHandler 초기화
        
        Args:
            download_dir: 파일 다운로드 디렉토리 (기본값: ./downloads)
        """
        self.download_dir = download_dir
        self._ensure_download_dir()
        self.supabase_client = get_supabase_client()
    
    def _ensure_download_dir(self) -> None:
        """다운로드 디렉토리가 존재하는지 확인하고 없으면 생성"""
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            logger.info(f"다운로드 디렉토리 생성: {self.download_dir}")
    
    async def download_file(self, session, file_url: str, filename: Optional[str] = None) -> Optional[Tuple[bytes, str]]:
        """
        파일 다운로드
        
        Args:
            session: HTTP 세션 (EclassSession 인스턴스)
            file_url: 파일 URL
            filename: 파일명 (None인 경우 URL에서 추출)
            
        Returns:
            Tuple[bytes, str]: (파일 데이터, 파일명) 튜플 또는 None
        """
        try:
            logger.info(f"파일 다운로드 시작: {file_url}")
            
            # 세션을 통해 파일 다운로드
            response = await session.get(file_url)
            
            # 파일명이 제공되지 않은 경우 URL에서 추출
            if not filename:
                # Content-Disposition 헤더에서 파일명 추출 시도
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'filename=' in content_disposition:
                    match = re.search(r'filename=["\']?([^"\']+)["\']?', content_disposition)
                    if match:
                        filename = unquote(match.group(1))
                    else:
                        filename = content_disposition.split('filename=')[1].split(';')[0].strip('"\'')
                
                # 헤더에서 파일명을 찾을 수 없으면 URL에서 추출
                if not filename:
                    parsed_url = urlparse(file_url)
                    path = parsed_url.path
                    filename = unquote(os.path.basename(path))
                    
                    # URL에서도 파일명을 추출할 수 없으면 기본 파일명 사용
                    if not filename or '.' not in filename:
                        filename = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"파일 다운로드 완료: {filename}")
            return (response.content, filename)
        
        except Exception as e:
            logger.error(f"파일 다운로드 중 오류 발생: {e}")
            return None
    
    async def save_file(self, file_data: bytes, filename: str, subdirectory: str = "") -> str:
        """
        파일 저장
        
        Args:
            file_data: 파일 데이터
            filename: 파일명
            subdirectory: 하위 디렉토리 (기본값: "")
            
        Returns:
            str: 저장된 파일 경로
        """
        try:
            # 하위 디렉토리 경로 생성
            save_dir = self.download_dir
            if subdirectory:
                save_dir = os.path.join(self.download_dir, subdirectory)
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
            
            # 파일명에서 유효하지 않은 문자 제거
            safe_filename = self._sanitize_filename(filename)
            
            # 전체 파일 경로
            file_path = os.path.join(save_dir, safe_filename)
            
            # 파일이 이미 존재하면 이름 변경
            if os.path.exists(file_path):
                base_name, ext = os.path.splitext(safe_filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_filename = f"{base_name}_{timestamp}{ext}"
                file_path = os.path.join(save_dir, safe_filename)
            
            # 파일 비동기 저장
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_data)
            
            logger.info(f"파일 저장 완료: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"파일 저장 중 오류 발생: {e}")
            return ""
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        파일명에서 유효하지 않은 문자 제거
        
        Args:
            filename: 원본 파일명
            
        Returns:
            str: 유효한 파일명
        """
        # 파일 시스템에서 유효하지 않은 문자 제거
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # 파일명이 너무 길면 잘라내기 (255자 제한)
        if len(filename) > 255:
            base_name, ext = os.path.splitext(filename)
            filename = base_name[:255-len(ext)] + ext
        
        return filename
    
    async def upload_to_supabase(self, file_path: str, course_id: str, source_type: str, article_id: str) -> Optional[str]:
        """
        로컬 파일을 Supabase Storage에 업로드
        
        Args:
            file_path: 로컬 파일 경로
            course_id: 강의 ID
            source_type: 소스 타입 (notices, assignments, lecture_materials 등)
            article_id: 게시글 ID
            
        Returns:
            Optional[str]: 업로드된 파일의 URL 또는 None
        """
        try:
            # 파일명 추출
            filename = os.path.basename(file_path)
            
            # 스토리지 경로 설정
            storage_path = f"courses/{course_id}/{source_type}/{article_id}/{filename}"
            
            logger.info(f"Supabase Storage에 업로드 시작: {storage_path}")
            
            # 파일 읽기
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # 스토리지 버킷 (기본적으로 'files' 사용)
            bucket_name = "files"
            
            # 파일 업로드
            result = self.supabase_client.storage.from_(bucket_name).upload(
                storage_path,
                file_data,
                {"content-type": "application/octet-stream", "upsert": True}
            )
            
            if result and isinstance(result, dict) and result.get('Key'):
                # 파일의 공개 URL 생성
                file_url = self.supabase_client.storage.from_(bucket_name).get_public_url(storage_path)
                logger.info(f"Supabase Storage 업로드 성공: {file_url}")
                return file_url
            else:
                logger.error("Supabase Storage 업로드 실패")
                return None
                
        except Exception as e:
            logger.error(f"Supabase Storage 업로드 중 오류 발생: {e}")
            return None
    
    async def download_attachments(self, session, item_data: Dict[str, Any], course_id: str) -> List[Dict[str, Any]]:
        """
        첨부파일 다운로드 및 Supabase 업로드
        
        Args:
            session: HTTP 세션 (EclassSession 인스턴스)
            item_data: 게시글 데이터 (공지사항, 강의자료 등)
            course_id: 강의 ID
            
        Returns:
            List[Dict[str, Any]]: 다운로드 및 업로드 결과 목록
        """
        results = []
        
        # 첨부파일 정보가 없으면 빈 목록 반환
        attachments = item_data.get('attachments', [])
        if not attachments:
            return results
        
        # 소스 유형 결정
        source_type = None
        if 'type' in item_data:
            source_type = item_data['type']
        elif 'source_type' in item_data:
            source_type = item_data['source_type']
            
        if not source_type:
            # 항목의 키를 기반으로 소스 유형 추론
            if 'title' in item_data and 'content' in item_data:
                if 'due_date' in item_data or 'assignment_id' in item_data:
                    source_type = 'assignments'
                elif 'author' in item_data:
                    source_type = 'notices'
                else:
                    source_type = 'lecture_materials'
        
        # 소스 ID 결정
        article_id = None
        if 'article_id' in item_data and item_data['article_id']:
            article_id = item_data['article_id']
        elif 'id' in item_data and item_data['id']:
            article_id = item_data['id']
        elif 'assignment_id' in item_data and item_data['assignment_id']:
            article_id = item_data['assignment_id']
        
        if not article_id or not source_type:
            logger.error(f"소스 타입 또는 ID를 결정할 수 없습니다: {source_type}, {article_id}")
            return []
        
        # 강의실 접근 (세션 갱신)
        course_url = await session.access_course(course_id)
        if not course_url:
            logger.error(f"강의실 접근 실패: {course_id}")
            return []
        
        # 디렉토리 경로
        subdirectory = f"{course_id}/{source_type}/{article_id}"
        
        # 각 첨부파일 처리
        for attachment in attachments:
            file_name = attachment.get('name', '')
            file_url = attachment.get('url', '')
            
            if not file_url:
                logger.warning(f"첨부파일 URL이 없습니다: {attachment}")
                continue
            
            # URL이 상대 경로면 절대 경로로 변환
            if not file_url.startswith('http'):
                file_url = f"https://eclass.seoultech.ac.kr{file_url}"
            
            # 파일 다운로드
            download_result = await self.download_file(session, file_url, file_name)
            if not download_result:
                results.append({
                    'name': file_name,
                    'url': file_url,
                    'success': False,
                    'error': '파일 다운로드 실패',
                    'timestamp': datetime.now().isoformat()
                })
                continue
                
            file_data, file_name = download_result
            
            # 파일 로컬 저장
            saved_path = await self.save_file(file_data, file_name, subdirectory)
            if not saved_path:
                results.append({
                    'name': file_name,
                    'url': file_url,
                    'success': False,
                    'error': '파일 저장 실패',
                    'timestamp': datetime.now().isoformat()
                })
                continue
            
            # Supabase에 업로드
            storage_url = await self.upload_to_supabase(saved_path, course_id, source_type, article_id)
            
            result = {
                'name': file_name,
                'original_url': file_url,
                'local_path': saved_path,
                'success': storage_url is not None,
                'timestamp': datetime.now().isoformat()
            }
            
            if storage_url:
                result['storage_url'] = storage_url
                result['storage_provider'] = 'supabase'
                logger.info(f"첨부파일 처리 성공: {file_name}")
            else:
                result['error'] = 'Supabase 업로드 실패'
                logger.error(f"첨부파일 Supabase 업로드 실패: {file_name}")
            
            results.append(result)
        
        return results
