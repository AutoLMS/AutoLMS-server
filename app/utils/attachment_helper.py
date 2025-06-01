"""
첨부파일 데이터 생성 헬퍼 함수

실제 Supabase attachments 테이블 스키마에 맞춰 데이터를 생성합니다.
"""
from typing import Dict, Any, Optional


def create_attachment_data(
    user_id: str,
    course_id: str,
    source_type: str,  # 'notices', 'lecture_materials', 'assignments'
    source_id: int,  # created record의 id
    file_name: str,
    original_url: str = "",
    storage_path: str = "",
    file_size: Optional[int] = None,
    file_type: Optional[str] = None,
    download_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    실제 Supabase attachments 테이블 스키마에 맞는 attachment 데이터 생성
    
    Args:
        user_id: 사용자 ID (UUID string)
        course_id: 강의 ID
        source_type: 소스 타입 ('notices', 'lecture_materials', 'assignments')
        source_id: 연결된 레코드의 ID (integer)
        file_name: 파일명
        original_url: 원본 URL (기본값: "")
        storage_path: 저장 경로 (기본값: "")
        file_size: 파일 크기 (기본값: None)
        file_type: 파일 타입 (기본값: None) 
        download_url: 다운로드 URL (기본값: None)
        
    Returns:
        Dict[str, Any]: Supabase attachments 테이블에 맞는 데이터
    """
    
    # source_type과 related_type 매핑
    related_type_mapping = {
        'notices': 'notices',
        'lecture_materials': 'materials',
        'assignments': 'assignments'
    }
    
    return {
        # 필수 필드들 (NOT NULL)
        'user_id': user_id,
        'course_id': course_id,
        'related_type': related_type_mapping.get(source_type, source_type),
        'related_id': source_id,
        'original_filename': file_name,
        'stored_filename': file_name,  # 기본적으로 original과 동일
        
        # 선택적 필드들 (nullable)
        'file_size': file_size,
        'file_type': file_type,
        'download_url': download_url,
        'storage_path': storage_path,
        'file_name': file_name,  # 호환성을 위해 유지
        'original_url': original_url,
        'source_id': str(source_id),  # 기존 코드 호환성을 위해 문자열로 변환
        'source_type': source_type,  # 기존 코드 호환성을 위해 유지
    }


def create_attachment_data_from_download_result(
    user_id: str,
    course_id: str,
    source_type: str,
    source_id: int,
    download_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    파일 다운로드 결과에서 attachment 데이터 생성
    
    Args:
        user_id: 사용자 ID
        course_id: 강의 ID
        source_type: 소스 타입
        source_id: 연결된 레코드의 ID
        download_result: file_handler.download_attachments의 결과
        
    Returns:
        Dict[str, Any]: attachment 데이터
    """
    return create_attachment_data(
        user_id=user_id,
        course_id=course_id,
        source_type=source_type,
        source_id=source_id,
        file_name=download_result.get("file_name", "Unknown"),
        original_url=download_result.get("original_url", ""),
        storage_path=download_result.get("storage_path", ""),
        # 추가 정보가 있으면 포함
        file_size=download_result.get("file_size"),
        file_type=download_result.get("content_type") or download_result.get("file_type"),
        download_url=download_result.get("download_url")
    )


def create_attachment_data_from_parsed_attachment(
    user_id: str,
    course_id: str,
    source_type: str,
    source_id: int,
    parsed_attachment: Dict[str, Any]
) -> Dict[str, Any]:
    """
    파싱된 첨부파일 정보에서 attachment 데이터 생성 (메타데이터만)
    
    Args:
        user_id: 사용자 ID
        course_id: 강의 ID
        source_type: 소스 타입
        source_id: 연결된 레코드의 ID
        parsed_attachment: parser에서 추출한 첨부파일 정보
        
    Returns:
        Dict[str, Any]: attachment 데이터
    """
    return create_attachment_data(
        user_id=user_id,
        course_id=course_id,
        source_type=source_type,
        source_id=source_id,
        file_name=parsed_attachment.get("name", "Unknown"),
        original_url=parsed_attachment.get("url", ""),
        storage_path="",  # 다운로드하지 않으므로 빈 값
    )
