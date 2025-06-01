# course_id를 데이터베이스 정수 ID로 변환하는 임시 해결책

def convert_course_id_to_db_id(course_id: str) -> int:
    """
    eClass course_id (A2025114608541001)를 데이터베이스 정수 ID로 변환
    실제로는 courses 테이블에서 course_id로 조회해서 id를 가져와야 함
    """
    # 간단한 해싱 또는 매핑 로직
    # 실제로는 데이터베이스에서 조회해야 함
    
    # 예시: course_id의 마지막 몇 자리를 정수로 변환
    if course_id.startswith('A'):
        # A2025114608541001 -> 541001 같은 방식
        return int(course_id[-6:]) if len(course_id) > 6 else hash(course_id) % 1000000
    
    return int(course_id) if course_id.isdigit() else hash(course_id) % 1000000

# 사용 예시:
# db_course_id = convert_course_id_to_db_id("A2025114608541001")
# print(db_course_id)  # 541001