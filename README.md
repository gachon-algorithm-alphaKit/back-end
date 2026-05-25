# AlphaKit Backend

이 프로젝트는 Django와 SQLite를 기반으로 구성된 백엔드 서버입니다.
주어진 SQL 쿼리 구조를 바탕으로 앱 모델이 생성되어 있으며, 관리자 페이지를 통해 테이블 구조를 시각적으로 확인하고 데이터를 관리할 수 있습니다.

## 프로젝트 스펙
- **Python 환경**: 가상 환경(`venv`)
- **웹 프레임워크**: Django (최신 안정 버전)
- **추가 라이브러리**: Django REST Framework 등 호환성에 맞춘 라이브러리 사용
- **데이터베이스**: SQLite (`db.sqlite3`)

## 서버 실행 방법

1. **가상 환경 활성화**
   ```bash
   # Windows (PowerShell)
   .\venv\Scripts\Activate.ps1
   # Windows (CMD)
   .\venv\Scripts\activate.bat
   # macOS/Linux
   source venv/bin/activate
   ```

2. **종속성 라이브러리 설치 (필요시)**
   ```bash
   pip install -r requirements.txt
   ```

3. **Django 서버 실행**
   ```bash
   python manage.py runserver
   ```
   서버가 정상적으로 실행되면 `http://127.0.0.1:8000/` 에서 확인할 수 있습니다.

## 관리자 페이지 (Admin) 접속
- **주소**: `http://127.0.0.1:8000/admin`
- **관리자 아이디**: `admin`
- **관리자 비밀번호**: `admin`

로그인 후 `core` 앱에 등록된 모든 모델(`School`, `Place`, `Student`, `Professor`, `Course`, `StudentCourse`, `StudyRoom`, `Reservation`, `Scholarship`, `ScholarshipHistory`, `LostItemPost`, `Comment`)의 데이터를 조회하고 추가/수정/삭제 할 수 있습니다.

## 모델 구조
`./design/database_creation_query.sql` 파일을 기반으로 Django의 `core/models.py`에 다음 12개의 모델이 정의되어 있습니다.
- School, Place, Student, Professor, Course, StudentCourse, StudyRoom, Reservation, Scholarship, ScholarshipHistory, LostItemPost, Comment
각 모델 간의 외래 키(Foreign Key) 관계도 원본 SQL 구조와 동일하게 매핑되었습니다.
