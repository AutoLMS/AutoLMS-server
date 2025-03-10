# 리포지토리 패키지

from app.db.repositories.course_repository import CourseRepository
from app.db.repositories.notice_repository import NoticeRepository
from app.db.repositories.material_repository import MaterialRepository
from app.db.repositories.assignment_repository import AssignmentRepository
from app.db.repositories.attachment_repository import AttachmentRepository
from app.db.repositories.syllabus_repository import SyllabusRepository

# 리포지토리 인스턴스 생성
course_repository = CourseRepository()
notice_repository = NoticeRepository()
material_repository = MaterialRepository()
assignment_repository = AssignmentRepository()
attachment_repository = AttachmentRepository()
syllabus_repository = SyllabusRepository()
