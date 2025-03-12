import pytest
from bs4 import BeautifulSoup

from app.services.eclass_parser import EclassParser


class TestEclassParser:
    """EclassParser 테스트"""

    @pytest.fixture
    def parser(self):
        """EclassParser 인스턴스 생성"""
        return EclassParser()

    @pytest.fixture
    def course_html(self):
        """강의 목록 HTML 샘플"""
        return """
        <html>
        <body>
            <div class="main-content">
                <ul class="lecCourse">
                    <li style="background: url('/ilos/images/co_bg.png');">
                        <span>월 12:00-13:00</span>
                        <em class="sub_open" kj="KJ12345">컴퓨터공학개론(CSE101)</em>
                    </li>
                    <li style="background: url('/ilos/images/co_bg.png');">
                        <span>화 15:00-16:30</span>
                        <em class="sub_open" kj="KJ67890">운영체제(CSE301)</em>
                    </li>
                </ul>
            </div>
        </body>
        </html>
        """

    @pytest.fixture
    def menu_html(self):
        """강의 메뉴 HTML 샘플"""
        return """
        <html>
        <body>
            <div class="course-menu">
                <ul>
                    <li id="st_plan" class="course_menu_item">
                        <a href="/ilos/st/course/plan_form.acl">강의계획서</a>
                    </li>
                    <li id="st_lecture_material" class="course_menu_item">
                        <a href="/ilos/st/course/lecture_material_list.acl">강의자료실</a>
                    </li>
                    <li id="st_notice" class="course_menu_item">
                        <a href="/ilos/st/course/notice_list.acl">공지사항</a>
                    </li>
                    <li id="st_report" class="course_menu_item">
                        <a href="/ilos/st/course/report_list.acl">과제</a>
                    </li>
                </ul>
            </div>
        </body>
        </html>
        """

    @pytest.fixture
    def notice_list_html(self):
        """공지사항 목록 HTML 샘플"""
        return """
        <html>
        <body>
            <table>
                <tr style="cursor: pointer;" onclick="pageMove('/ilos/st/course/notice_view_form.acl?ARTL_NUM=12345')">
                    <td>1</td>
                    <td>2023-01-15</td>
                    <td>
                        <a class="site-link">
                            <div>중간고사 안내</div>
                            <div class="subjt_bottom">
                                <span>홍길동 교수</span>
                                <span>조회수 50</span>
                            </div>
                        </a>
                    </td>
                    <td></td>
                    <td>2023-01-15</td>
                </tr>
                <tr style="cursor: pointer;" onclick="pageMove('/ilos/st/course/notice_view_form.acl?ARTL_NUM=12346')">
                    <td>2</td>
                    <td>2023-01-18</td>
                    <td>
                        <a class="site-link">
                            <div>수업 휴강 안내</div>
                            <div class="subjt_bottom">
                                <span>홍길동 교수</span>
                                <span>조회수 45</span>
                            </div>
                        </a>
                    </td>
                    <td></td>
                    <td>2023-01-18</td>
                </tr>
            </table>
        </body>
        </html>
        """

    @pytest.fixture
    def material_list_html(self):
        """강의자료 목록 HTML 샘플"""
        return """
        <html>
        <body>
            <table>
                <tr style="cursor: pointer;" onclick="pageMove('/ilos/st/course/lecture_material_view_form.acl?ARTL_NUM=23456')">
                    <td>1</td>
                    <td class="left">
                        <div class="subjt_top">1주차 강의자료</div>
                        <div class="subjt_bottom">
                            <span>홍길동 교수</span>
                        </div>
                        <img class="download_icon" src="/ilos/images/download.png">
                    </td>
                    <td class="number">2023-01-10</td>
                </tr>
                <tr style="cursor: pointer;" onclick="pageMove('/ilos/st/course/lecture_material_view_form.acl?ARTL_NUM=23457')">
                    <td>2</td>
                    <td class="left">
                        <div class="subjt_top">2주차 강의자료</div>
                        <div class="subjt_bottom">
                            <span>홍길동 교수</span>
                        </div>
                    </td>
                    <td class="number">2023-01-17</td>
                </tr>
            </table>
        </body>
        </html>
        """

    @pytest.fixture
    def assignment_list_html(self):
        """과제 목록 HTML 샘플"""
        return """
        <html>
        <body>
            <table class="table_topic">
                <tr>
                    <th>번호</th>
                    <th>제목</th>
                    <th>작성자</th>
                    <th>시작일</th>
                    <th>마감일</th>
                    <th>상태</th>
                    <th>제출여부</th>
                </tr>
                <tr onclick="pageMove('/ilos/st/course/report_view_form.acl?ARTL_NUM=34567')">
                    <td>1</td>
                    <td>과제 1</td>
                    <td>홍길동 교수</td>
                    <td>2023-01-15</td>
                    <td>2023-01-22</td>
                    <td>진행중</td>
                    <td>미제출</td>
                </tr>
                <tr onclick="pageMove('/ilos/st/course/report_view_form.acl?ARTL_NUM=34568')">
                    <td>2</td>
                    <td>과제 2</td>
                    <td>홍길동 교수</td>
                    <td>2023-01-22</td>
                    <td>2023-01-29</td>
                    <td>진행중</td>
                    <td>미제출</td>
                </tr>
            </table>
        </body>
        </html>
        """

    def test_parse_courses(self, parser, course_html):
        """강의 목록 파싱 테스트"""
        courses = parser.parse_courses(course_html)
        
        assert len(courses) == 2
        assert courses[0]["id"] == "KJ12345"
        assert courses[0]["name"] == "컴퓨터공학개론"
        assert courses[0]["code"] == "CSE101"
        assert courses[0]["time"] == "월 12:00-13:00"
        
        assert courses[1]["id"] == "KJ67890"
        assert courses[1]["name"] == "운영체제"
        assert courses[1]["code"] == "CSE301"
        assert courses[1]["time"] == "화 15:00-16:30"

    def test_parse_course_menus(self, parser, menu_html):
        """강의 메뉴 파싱 테스트"""
        menus = parser.parse_course_menus(menu_html)
        
        assert len(menus) == 4
        assert "plan" in menus
        assert menus["plan"]["name"] == "강의계획서"
        assert menus["plan"]["url"] == "/ilos/st/course/plan_form.acl"
        
        assert "lecture_material" in menus
        assert menus["lecture_material"]["name"] == "강의자료실"
        assert menus["lecture_material"]["url"] == "/ilos/st/course/lecture_material_list.acl"
        
        assert "notice" in menus
        assert menus["notice"]["name"] == "공지사항"
        assert menus["notice"]["url"] == "/ilos/st/course/notice_list.acl"
        
        assert "assignment" in menus
        assert menus["assignment"]["name"] == "과제"
        assert menus["assignment"]["url"] == "/ilos/st/course/report_list.acl"

    def test_parse_notice_list(self, parser, notice_list_html):
        """공지사항 목록 파싱 테스트"""
        notices = parser.parse_notice_list(notice_list_html)
        
        assert len(notices) == 2
        assert notices[0]["number"] == "1"
        assert notices[0]["article_id"] == "12345"
        assert notices[0]["title"] == "중간고사 안내"
        assert notices[0]["author"] == "홍길동 교수"
        assert notices[0]["date"] == "2023-01-15"
        assert notices[0]["views"] == "50"
        assert notices[0]["url"] == "https://eclass.seoultech.ac.kr/ilos/st/course/notice_view_form.acl?ARTL_NUM=12345"
        
        assert notices[1]["number"] == "2"
        assert notices[1]["article_id"] == "12346"
        assert notices[1]["title"] == "수업 휴강 안내"
        assert notices[1]["author"] == "홍길동 교수"
        assert notices[1]["date"] == "2023-01-18"
        assert notices[1]["views"] == "45"
        assert notices[1]["url"] == "https://eclass.seoultech.ac.kr/ilos/st/course/notice_view_form.acl?ARTL_NUM=12346"

    def test_parse_material_list(self, parser, material_list_html):
        """강의자료 목록 파싱 테스트"""
        materials = parser.parse_material_list(material_list_html)
        
        assert len(materials) == 2
        assert materials[0]["article_id"] == "23456"
        assert materials[0]["title"] == "1주차 강의자료"
        assert materials[0]["author"] == "홍길동 교수"
        assert materials[0]["date"] == "2023-01-10"
        assert materials[0]["url"] == "https://eclass.seoultech.ac.kr/ilos/st/course/lecture_material_view_form.acl?ARTL_NUM=23456"
        assert materials[0]["has_attachment"] == True
        
        assert materials[1]["article_id"] == "23457"
        assert materials[1]["title"] == "2주차 강의자료"
        assert materials[1]["author"] == "홍길동 교수"
        assert materials[1]["date"] == "2023-01-17"
        assert materials[1]["url"] == "https://eclass.seoultech.ac.kr/ilos/st/course/lecture_material_view_form.acl?ARTL_NUM=23457"
        assert materials[1]["has_attachment"] == False

    def test_parse_assignment_list(self, parser, assignment_list_html):
        """과제 목록 파싱 테스트"""
        assignments = parser.parse_assignment_list(assignment_list_html)
        
        assert len(assignments) == 2
        assert assignments[0]["assignment_id"] == "34567"
        assert assignments[0]["title"] == "과제 1"
        assert assignments[0]["start_date"] == "2023-01-15"
        assert assignments[0]["end_date"] == "2023-01-22"
        assert assignments[0]["status"] == "진행중"
        assert assignments[0]["url"] == "https://eclass.seoultech.ac.kr/ilos/st/course/report_view_form.acl?ARTL_NUM=34567"
        
        assert assignments[1]["assignment_id"] == "34568"
        assert assignments[1]["title"] == "과제 2"
        assert assignments[1]["start_date"] == "2023-01-22"
        assert assignments[1]["end_date"] == "2023-01-29"
        assert assignments[1]["status"] == "진행중"
        assert assignments[1]["url"] == "https://eclass.seoultech.ac.kr/ilos/st/course/report_view_form.acl?ARTL_NUM=34568"

    def test_extract_url_from_onclick(self, parser):
        """onclick 속성에서 URL 추출 테스트"""
        onclick = "pageMove('/ilos/st/course/notice_view_form.acl?ARTL_NUM=12345')"
        url = parser._extract_url_from_onclick(onclick)
        assert url == "https://eclass.seoultech.ac.kr/ilos/st/course/notice_view_form.acl?ARTL_NUM=12345"
        
        onclick = "pageMove('/ilos/st/course/report_view_form.acl?ARTL_NUM=34567')"
        url = parser._extract_url_from_onclick(onclick)
        assert url == "https://eclass.seoultech.ac.kr/ilos/st/course/report_view_form.acl?ARTL_NUM=34567"
        
        onclick = ""
        url = parser._extract_url_from_onclick(onclick)
        assert url == ""

    def test_extract_article_id(self, parser):
        """URL에서 게시글 ID 추출 테스트"""
        url = "https://eclass.seoultech.ac.kr/ilos/st/course/notice_view_form.acl?ARTL_NUM=12345"
        article_id = parser._extract_article_id(url)
        assert article_id == "12345"
        
        url = "https://eclass.seoultech.ac.kr/ilos/st/course/report_view_form.acl?ARTL_NUM=34567"
        article_id = parser._extract_article_id(url)
        assert article_id == "34567"
        
        url = "https://eclass.seoultech.ac.kr/ilos/st/course/notice_list.acl"
        article_id = parser._extract_article_id(url)
        assert article_id is None
        
        url = ""
        article_id = parser._extract_article_id(url)
        assert article_id is None
