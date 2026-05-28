# AlphaKit Backend

AlphaKit 백엔드 서버 프로젝트입니다. 가천대학교 등 대학교 환경에 맞춘 다양한 캠퍼스 기능(수강신청 시간표, 장학금, 캠퍼스 맵, 커뮤니티, 스터디룸 예약 등)을 제공하는 REST API 서버입니다.

## 🛠 기술 스택

- **언어**: Python 3.x
- **웹 프레임워크**: Django 6.x
- **API 프레임워크**: Django REST Framework (DRF)
- **인증**: JWT (djangorestframework-simplejwt)
- **데이터베이스**: SQLite (`db.sqlite3`)

## 💡 주요 기능 및 모델 구조

본 프로젝트는 `core/models/` 내에 세분화된 모듈로 데이터베이스 모델을 관리합니다.

- **사용자 (Users)**: 학생(`Student`), 교수(`Professor`) 등 사용자 정보 및 인증
- **수강 및 시간표 (Courses & Wishlist)**: 개설 강의(`Course`), 강의 찜하기(Wishlist) 및 수강 관련 데이터
- **캠퍼스 맵 (Campus)**: 학교 건물(`Place`), 도보 이동 가능 경로(`CampusEdge`), 건물 별칭(`PlaceAlias`) 등 최단거리 길찾기를 위한 그래프 데이터 구조
- **장학금 (Scholarships)**: 교내외 장학금 정보(`Scholarship`) 및 수혜 내역(`ScholarshipHistory`)
- **스터디룸 (Rooms)**: 스터디룸(`StudyRoom`) 및 예약(`Reservation`) 내역 관리
- **커뮤니티 (Community)**: 분실물 게시판(`LostItemPost`), 댓글(`Comment`) 등

## 🚀 프로젝트 설정 및 실행 방법

1. **가상 환경 생성 및 활성화**
   ```bash
   python -m venv venv
   
   # Windows (PowerShell)
   .\venv\Scripts\Activate.ps1
   # Windows (CMD)
   .\venv\Scripts\activate.bat
   # macOS/Linux
   source venv/bin/activate
   ```

2. **패키지 설치**
   ```bash
   pip install -r requirements.txt
   ```

3. **데이터베이스 마이그레이션**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **캠퍼스 맵 초기 데이터 생성 (선택)**
   가천대학교 캠퍼스의 건물 및 이동 가능 경로(Edge) 데이터를 DB에 주입하려면 아래 스크립트를 실행하세요.
   ```bash
   python populate_campus.py
   ```

5. **서버 실행**
   ```bash
   python manage.py runserver
   ```
   서버가 실행되면 `http://127.0.0.1:8000/` 에서 접속할 수 있습니다.

## 📡 주요 API 엔드포인트

API는 JSON 형식으로 통신하며, 일부 API는 Bearer 토큰(JWT) 인증이 필요합니다.

- **Auth & Users**
  - `POST /api/students/login`: 학생 로그인 및 JWT 토큰 발급
  - `GET /api/students/info`: 로그인한 학생 정보 조회 (Token 필요)

- **Courses & Wishlist**
  - `GET /api/courses/`: 전체 강의 목록 조회
  - `GET /api/wishlist/`: 찜한 강의 목록 조회 (Token 필요)
  - `POST /api/wishlist/toggle/`: 강의 찜하기/취소 토글 (Token 필요)
  - `DELETE /api/wishlist/remove/<id>/`: 찜한 강의 삭제 (Token 필요)

- **Campus Map**
  - `GET /api/campus/graph/`: 캠퍼스 건물 및 경로(Edge) 그래프 데이터 조회

- **Scholarships**
  - `GET /api/scholarships/`: 장학금 목록 조회

*(자세한 API 스펙은 소스코드의 `core/urls.py` 및 `core/api/` 디렉터리의 각 뷰 함수를 참고하세요.)*

## 🔒 관리자 페이지 (Admin)

- **접속 주소**: `http://127.0.0.1:8000/admin`
- 기본적으로 설정된 관리자 계정(예: `admin` / `admin`)으로 로그인하면 모델에 등록된 모든 데이터를 시각적으로 조회하고 추가/수정/삭제할 수 있습니다. 관리자 계정이 없다면 `python manage.py createsuperuser` 명령어로 생성하세요.
