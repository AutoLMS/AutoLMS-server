import json
import os
from typing import List, Dict, Any
from datetime import datetime

class TestDataService:
    """테스트 데이터를 사용하는 임시 서비스"""
    
    def __init__(self):
        self.data_file = "test_data/eclass_test_data.json"
        self._data = None
    
    def _load_data(self) -> Dict[str, Any]:
        """테스트 데이터 로드"""
        if self._data is None:
            try:
                if os.path.exists(self.data_file):
                    with open(self.data_file, "r", encoding="utf-8") as f:
                        self._data = json.load(f)
                else:
                    # 기본 빈 데이터
                    self._data = {
                        "user_id": "1ae6fcaa-c18d-40a7-83bb-56715689b47c",
                        "timestamp": datetime.now().isoformat(),
                        "courses": [],
                        "course_details": {}
                    }
            except Exception as e:
                print(f"테스트 데이터 로드 실패: {e}")
                self._data = {
                    "user_id": "1ae6fcaa-c18d-40a7-83bb-56715689b47c",
                    "timestamp": datetime.now().isoformat(),
                    "courses": [],
                    "course_details": {}
                }
        return self._data
    
    def get_courses(self, user_id: str) -> List[Dict[str, Any]]:
        """강의 목록 조회"""
        data = self._load_data()
        courses = data.get("courses", [])
        
        # Course 모델 형식으로 변환
        result = []
        for course in courses:
            result.append({
                "id": course.get("id"),
                "name": course.get("name"),
                "code": course.get("code"),
                "time": course.get("time"),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
        
        return result
    
    def get_notices(self, user_id: str, course_id: str) -> List[Dict[str, Any]]:
        """공지사항 조회"""
        data = self._load_data()
        course_details = data.get("course_details", {})
        
        if course_id in course_details:
            notices = course_details[course_id].get("notices", [])
            
            # Notice 모델 형식으로 변환
            result = []
            for i, notice in enumerate(notices):
                result.append({
                    "id": i + 1,
                    "article_id": notice.get("article_id"),
                    "course_id": course_id,
                    "title": notice.get("title"),
                    "content": None,  # 상세 내용은 별도 API에서
                    "author": notice.get("author"),
                    "date": notice.get("date"),
                    "views": notice.get("views", 0),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "attachments": []
                })
            return result
        
        return []
    
    def get_materials(self, user_id: str, course_id: str) -> List[Dict[str, Any]]:
        """강의자료 조회"""
        data = self._load_data()
        course_details = data.get("course_details", {})
        
        if course_id in course_details:
            materials = course_details[course_id].get("materials", [])
            
            # Material 모델 형식으로 변환
            result = []
            for i, material in enumerate(materials):
                result.append({
                    "id": i + 1,
                    "article_id": material.get("article_id"),
                    "course_id": course_id,
                    "title": material.get("title"),
                    "content": None,  # 상세 내용은 별도 API에서
                    "author": material.get("author"),
                    "date": material.get("date"),
                    "views": 0,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "attachments": []
                })
            return result
        
        return []
    
    def get_assignments(self, user_id: str, course_id: str) -> List[Dict[str, Any]]:
        """과제 조회"""
        data = self._load_data()
        course_details = data.get("course_details", {})
        
        if course_id in course_details:
            assignments = course_details[course_id].get("assignments", [])
            
            # Assignment 모델 형식으로 변환
            result = []
            for i, assignment in enumerate(assignments):
                result.append({
                    "id": i + 1,
                    "article_id": assignment.get("assignment_id", str(i + 1)),
                    "course_id": course_id,
                    "title": assignment.get("title"),
                    "content": None,
                    "due_date": assignment.get("due_date"),
                    "status": assignment.get("status"),
                    "submission_status": assignment.get("submission_status"),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "attachments": []
                })
            return result
        
        return []
    
    def get_course_by_id(self, user_id: str, course_id: str) -> Dict[str, Any]:
        """특정 강의 조회"""
        courses = self.get_courses(user_id)
        for course in courses:
            if course["id"] == course_id:
                return course
        return None
