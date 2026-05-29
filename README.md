# 🎓 AlphaKit Back-End

> **가천대학교 스마트 캠퍼스 도우미 앱** — AlphaKit의 Django REST API 백엔드

AlphaKit은 가천대학교 학생들을 위한 올인원 캠퍼스 서비스 앱입니다.  
e-Campus 연동 로그인, 강의 검색, 장학금 추천, 스터디룸 예약, 분실물 커뮤니티, 캠퍼스 길찾기 등의 기능을 제공합니다.

---

## 📑 목차

- [프로젝트 설정](#-프로젝트-설정)
- [실행 방법](#-실행-방법)
- [사용 라이브러리](#-사용-라이브러리)
- [파일 구조](#-파일-구조)
- [Data Model (ERD)](#-data-model)
- [API 명세](#-api-명세)
- [적용 알고리즘](#-적용-알고리즘)
- [인증 방식](#-인증-방식)
- [테스트](#-테스트)
- [로깅](#-로깅)

---

## ⚙️ 프로젝트 설정

| 항목 | 설정값 |
|------|--------|
| **프레임워크** | Django 6.0.5 + Django REST Framework 3.17.1 |
| **Python** | 3.x |
| **데이터베이스** | SQLite3 (`db.sqlite3`) |
| **인증** | JWT (Simple JWT — Access 1일 / Refresh 7일) |
| **미디어 저장** | `media/` 디렉토리 (프로필 이미지, 분실물 이미지) |
| **로깅** | 파일(`alphakit_backend.log`) + 콘솔 |
| **ALLOWED_HOSTS** | `["*"]` (개발 환경) |

---

## 🚀 실행 방법

### 1. 가상 환경 생성 및 활성화

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 데이터베이스 마이그레이션

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. (선택) 캠퍼스 초기 데이터 입력

```bash
python populate_campus.py
```

### 5. 개발 서버 실행

```bash
python manage.py runserver
# 또는 특정 포트 지정
python manage.py runserver 0.0.0.0:8000
```

### 6. 관리자 페이지 접근

```
http://localhost:8000/admin/
```

### 7. 테스트 실행

```bash
python manage.py test core
```

---

## 📦 사용 라이브러리

| 패키지 | 버전 | 용도 |
|--------|------|------|
| **Django** | 6.0.5 | 웹 프레임워크 |
| **djangorestframework** | 3.17.1 | REST API 구축 |
| **djangorestframework-simplejwt** | 5.5.1 | JWT 인증 (Access/Refresh Token) |
| **Pillow** | 12.2.0 | 이미지 업로드 처리 (프로필, 분실물 사진) |
| **requests** | 2.34.2 | e-Campus 외부 로그인 API 연동 |
| **PyJWT** | 2.13.0 | JWT 토큰 처리 |
| **sqlparse** | 0.5.5 | SQL 파싱 (Django 내부 의존성) |
| **asgiref** | 3.11.1 | ASGI 지원 |
| **certifi** | 2026.5.20 | SSL 인증서 |
| **charset-normalizer** | 3.4.7 | 문자 인코딩 감지 |
| **idna** | 3.16 | 국제 도메인 이름 처리 |
| **urllib3** | 2.7.0 | HTTP 클라이언트 |
| **tzdata** | 2026.2 | 시간대 데이터 |

---

## 📁 파일 구조

```
back-end/
├── manage.py                    # Django 관리 스크립트
├── requirements.txt             # Python 의존성 목록
├── db.sqlite3                   # SQLite 데이터베이스 파일
├── populate_campus.py           # 캠퍼스 초기 데이터 입력 스크립트
├── dump_schema.py               # DB 스키마 덤프 유틸리티
├── schema.txt                   # DB 스키마 텍스트
├── alphakit_backend.log         # 서버 로그 파일
├── .gitignore
│
├── config/                      # Django 프로젝트 설정
│   ├── __init__.py
│   ├── settings.py              # 프로젝트 전체 설정 (DB, JWT, 로깅 등)
│   ├── urls.py                  # 루트 URL 라우팅 (api/ → core.urls)
│   ├── wsgi.py                  # WSGI 배포 설정
│   └── asgi.py                  # ASGI 배포 설정
│
├── core/                        # 메인 앱
│   ├── __init__.py
│   ├── admin.py                 # Django Admin 등록 (전체 모델)
│   ├── apps.py                  # 앱 설정
│   ├── urls.py                  # API URL 라우팅
│   ├── views.py                 # 기본 뷰 (미사용)
│   ├── tests.py                 # 인증 API 유닛 테스트
│   │
│   ├── models/                  # 데이터 모델
│   │   ├── __init__.py          # 모델 일괄 export
│   │   ├── campus.py            # School, Place, CampusEdge, PlaceAlias
│   │   ├── users.py             # Student, Professor
│   │   ├── courses.py           # Course, StudentCourse
│   │   ├── rooms.py             # StudyRoom, Reservation
│   │   ├── scholarships.py      # Scholarship, ScholarshipHistory
│   │   └── community.py         # LostItemPost, Comment
│   │
│   ├── api/                     # API 뷰 (엔드포인트 핸들러)
│   │   ├── __init__.py
│   │   ├── login.py             # e-Campus 연동 로그인 + JWT 발급
│   │   ├── auth.py              # 회원가입 + 프로필 조회/수정
│   │   ├── courses.py           # 강의 검색 (Trie + Rabin-Karp)
│   │   ├── wishlist.py          # 수강 위시리스트 CRUD
│   │   ├── campus.py            # 캠퍼스 그래프 (길찾기용 노드/간선)
│   │   ├── scholarships.py      # 장학금 추천 (매칭 스코어링)
│   │   ├── rooms.py             # 스터디룸 추천 + 예약 관리
│   │   ├── losts.py             # 분실물 검색/등록/수정/삭제
│   │   ├── comments.py          # 분실물 댓글 CRUD
│   │   └── routes.py            # (미사용)
│   │
│   └── utils/                   # 유틸리티
│       └── course_search.py     # 강의 검색 엔진 (Trie, HashTable, Rabin-Karp, 초성 검색)
│
├── media/                       # 업로드 미디어 파일
│   ├── profiles/                # 학생 프로필 이미지
│   └── lost_items/              # 분실물 이미지
│
└── venv/                        # Python 가상 환경 (Git 제외)
```

---

## 🗄️ Data Model

### ER 다이어그램

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│   School     │     │    Student       │     │  Professor   │
├──────────────┤     ├──────────────────┤     ├──────────────┤
│ school_id PK │◄────│ school_id FK     │     │ professor_id │
│ name         │     │ student_id PK    │     │ school_id FK │
└──────┬───────┘     │ login_id (UQ)    │     │ name         │
       │             │ password_hash    │     └──────┬───────┘
       │             │ name             │            │
       │             │ major            │            │
       │             │ year             │            │
       │             │ gpa              │     ┌──────┴───────┐
       │             │ income_bracket   │     │   Course     │
       │             │ profile_img      │     ├──────────────┤
       │             └──────┬───────────┘     │ course_id PK │
       │                    │                 │ school_id FK │
       │                    │                 │ professor_id │
       │                    │                 │ course_code  │
       │                    │                 │ course_name  │
       │                    │                 │ description  │
       │                    │                 │ day_of_week  │
       │                    │                 │ start_time   │
       │                    │                 │ end_time     │
       │                    │                 └──────┬───────┘
       │                    │                        │
       │              ┌─────┴────────────────────────┘
       │              │  StudentCourse (위시리스트)
       │              ├──────────────────────────┐
       │              │ student_course_id PK     │
       │              │ student_id FK            │
       │              │ course_id FK             │
       │              └──────────────────────────┘
       │
  ┌────┴──────────┐     ┌─────────────────────┐
  │    Place      │     │   CampusEdge        │
  ├───────────────┤     ├─────────────────────┤
  │ place_id PK   │◄────│ node1 FK            │
  │ school_id FK  │     │ node2 FK            │
  │ name          │     │ is_walkable         │
  │ place_type    │     │ edge_id PK          │
  │ latitude      │     └─────────────────────┘
  │ longitude     │
  └──────┬────────┘     ┌─────────────────────┐
         │              │   PlaceAlias        │
         │◄─────────────│ place_id FK         │
         │              │ alias_name          │
         │              │ alias_id PK         │
         │              └─────────────────────┘
         │
  ┌──────┴────────┐
  │  StudyRoom    │
  ├───────────────┤     ┌─────────────────────────┐
  │ room_id PK    │◄────│   Reservation           │
  │ place_id FK   │     ├─────────────────────────┤
  │ name          │     │ reservation_id PK       │
  │ capacity      │     │ room_id FK              │
  │ facilities    │     │ student_id FK           │
  └───────────────┘     │ start_time              │
                        │ end_time                │
                        │ head_count              │
                        │ reservation_group_id    │
                        │ status                  │
                        └─────────────────────────┘

┌──────────────────────────┐     ┌──────────────────────────┐
│   Scholarship            │     │  ScholarshipHistory      │
├──────────────────────────┤     ├──────────────────────────┤
│ scholarship_id PK        │◄────│ scholarship_id FK        │
│ school_id FK             │     │ student_id FK            │
│ name                     │     │ history_id PK            │
│ dead_line                │     │ semester                 │
│ amount                   │     └──────────────────────────┘
│ required_gpa             │
│ required_income_bracket  │
│ duplicate_allowed        │
└──────────────────────────┘

┌──────────────────────────┐     ┌──────────────────────────┐
│   LostItemPost           │     │   Comment                │
├──────────────────────────┤     ├──────────────────────────┤
│ item_id PK               │◄────│ lost_item_id FK          │
│ school_id FK             │     │ student_id FK            │
│ student_id FK            │     │ comment_id PK            │
│ place                    │     │ comment                  │
│ title                    │     │ is_anonymous             │
│ is_anonymous             │     │ create_time              │
│ category                 │     └──────────────────────────┘
│ description              │
│ lost_item_img            │
│ status (찾음/미찾음)      │
│ create_time              │
└──────────────────────────┘
```

### 모델 요약

| 모델 | 설명 | 주요 필드 |
|------|------|-----------|
| **School** | 학교(대학) | `school_id`, `name` |
| **Place** | 캠퍼스 내 장소 (건물, 경로점) | `place_id`, `name`, `place_type`, `latitude`, `longitude` |
| **CampusEdge** | 장소 간 보행 가능 경로 | `node1`, `node2`, `is_walkable` |
| **PlaceAlias** | 장소 별칭 (예: "학생회관" → "제2학생활동관") | `alias_name`, `place` |
| **Student** | 학생 | `student_id`, `login_id`, `name`, `major`, `year`, `gpa`, `income_bracket`, `profile_img` |
| **Professor** | 교수 | `professor_id`, `name` |
| **Course** | 강의 | `course_code`, `course_name`, `professor`, `day_of_week`, `start_time`, `end_time` |
| **StudentCourse** | 수강 위시리스트 (학생-강의 N:M) | `student`, `course` |
| **StudyRoom** | 스터디룸 | `name`, `capacity`, `facilities`, `place` |
| **Reservation** | 스터디룸 예약 | `room`, `student`, `start_time`, `end_time`, `head_count`, `status` |
| **Scholarship** | 장학금 | `name`, `dead_line`, `amount`, `required_gpa`, `required_income_bracket`, `duplicate_allowed` |
| **ScholarshipHistory** | 장학금 수혜 이력 | `student`, `scholarship`, `semester` |
| **LostItemPost** | 분실물 게시글 | `title`, `category`, `description`, `lost_item_img`, `status`, `is_anonymous` |
| **Comment** | 분실물 댓글 | `lost_item`, `student`, `comment`, `is_anonymous` |

---

## 📡 API 명세

> 모든 API는 `/api/` 접두사를 사용합니다.  
> 🔒 = JWT 인증 필요 (`Authorization: Bearer <access_token>`)

### 🔐 인증 (Auth)

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| `POST` | `/api/students/login` | e-Campus 연동 로그인 | ❌ |
| `POST` | `/api/students/info` | 회원가입 (첫 로그인 후 정보 등록) | ❌ |
| `GET` | `/api/students/info` | 내 정보 조회 | 🔒 |
| `PUT` | `/api/students/info` | 내 정보 수정 (프로필 이미지 포함) | 🔒 |

<details>
<summary><b>POST /api/students/login</b> — 상세</summary>

**Request Body:**
```json
{
  "username": "학번",
  "password": "비밀번호",
  "school_id": 1
}
```

**Response (기존 사용자):**
```json
{
  "status": "success",
  "message": "로그인에 성공했습니다.",
  "data": {
    "studentId": 202012345,
    "school_id": 1,
    "login_id": "학번",
    "name": "홍길동",
    "major": "컴퓨터공학과",
    "year": 3,
    "gpa": 4.0,
    "income_bracket": 5,
    "profile_img": "/media/profiles/photo.jpg",
    "access_token": "eyJ...",
    "refresh_token": "eyJ..."
  }
}
```

**Response (첫 로그인):**
```json
{
  "status": "success",
  "message": "첫 로그인입니다.",
  "data": null
}
```
</details>

---

### 📚 강의 검색 (Courses)

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| `GET` | `/api/courses/` | 강의 검색 / 전체 목록 조회 | ❌ |

**Query Parameters:**

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `keyword` | string | 검색 키워드 (강의명 또는 내용) |
| `professor_name` | string | 교수명 검색 |
| `search_type` | string | `name` / `professor` / `content` |
| `page` | int | 페이지 번호 (기본: 1) |
| `limit` | int | 페이지당 항목 수 (기본: 20) |
| `school_id` | int | 학교 ID (기본: 1) |

**Response:**
```json
{
  "status": "success",
  "search_info": {
    "applied_algorithm": "Trie/Rabin-Karp (Name)",
    "is_searched": true
  },
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 100
  },
  "data": [
    {
      "course_id": 1,
      "course_code": "CS101",
      "course_name": "자료구조",
      "professor_name": "김교수",
      "day_of_week": "월",
      "start_time": "09:00:00",
      "end_time": "10:30:00",
      "description": "..."
    }
  ]
}
```

---

### 💾 수강 위시리스트 (Wishlist)

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| `POST` | `/api/wishlist/toggle/` | 위시리스트 추가/제거 토글 | 🔒 |
| `GET` | `/api/wishlist/` | 내 위시리스트 조회 (페이지네이션) | 🔒 |
| `DELETE` | `/api/wishlist/remove/<course_id>/` | 특정 강의 위시리스트에서 제거 | 🔒 |

---

### 🗺️ 캠퍼스 그래프 (Campus)

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| `GET` | `/api/campus/graph/` | 캠퍼스 노드(장소)/간선(경로) 그래프 데이터 | ❌ |

**Response:**
```json
{
  "status": "success",
  "data": {
    "nodes": {
      "제1공학관": { "lat": 37.4508, "lon": 127.1280, "type": "BUILDING" }
    },
    "edges": [["제1공학관", "P_01"], ["P_01", "중앙도서관"]],
    "aliases": { "공학관": "제1공학관" }
  }
}
```

> 💡 응답 데이터는 1시간 동안 서버 캐시됩니다.

---

### 🎓 장학금 추천 (Scholarships)

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| `GET` | `/api/scholarships/` | 장학금 목록 + 매칭 점수 | 🔒 |

**Query Parameters:**

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `gpa` | float | 학점 (기본: 3.85) |
| `income_bracket` | int | 소득 분위 (기본: 5) |
| `awarded_last_semester` | string | 지난 학기 수혜 여부 (`true`/`false`) |
| `page` | int | 페이지 번호 |
| `limit` | int | 페이지당 항목 수 |

**매칭 알고리즘:**
- 기본 점수 40점 + GPA 충족(+20) + 소득 충족(+20) + 중복 허용(+10) + 완전 매칭(+10) = 최대 100점
- D-Day 계산으로 마감 임박 장학금 표시
- 결과는 매칭 점수 내림차순 정렬

---

### 🏫 스터디룸 (Rooms)

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| `POST` | `/api/rooms/recommend/` | 조건 기반 스터디룸 추천 | 🔒 (선택) |
| `POST` | `/api/rooms/reserve/` | 스터디룸 예약 | 🔒 |
| `GET` | `/api/rooms/reservations/` | 내 예약 목록 조회 | 🔒 |
| `DELETE` | `/api/rooms/reservations/<id>/` | 예약 취소 | 🔒 |

<details>
<summary><b>POST /api/rooms/recommend/</b> — 상세</summary>

**Request Body:**
```json
{
  "school_id": 1,
  "head_count": 4,
  "start_time": "2026-05-28T10:00:00",
  "end_time": "2026-05-28T12:00:00",
  "facilities": ["TV", "화이트보드"],
  "page": 1,
  "limit": 10
}
```

**추천 알고리즘:**
- 수용 인원 적합도 점수: `max(100 - (여유인원 × 10), 0)`
- 시설 매칭 점수: `매칭된 시설 수 × 25`
- 예약 충돌 여부 및 14시간 타임라인 슬롯(08:00~22:00) 제공
</details>

---

### 📦 분실물 (Lost Items)

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| `POST/GET` | `/api/lost-items/search/` | 분실물 검색 (KMP + Levenshtein) | 🔒 (선택) |
| `POST` | `/api/lost-items/` | 분실물 게시글 등록 (multipart) | 🔒 |
| `GET` | `/api/students/me/lost-items` | 내가 작성한 분실물 목록 | 🔒 |
| `PUT` | `/api/students/me/lost-items/<id>` | 분실물 게시글 수정 | 🔒 |
| `DELETE` | `/api/students/me/lost-items/<id>` | 분실물 게시글 삭제 | 🔒 |
| `POST` | `/api/lost-items/suggestions/` | 분실물 검색어 자동완성 제안 | ❌ |

---

### 💬 댓글 (Comments)

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| `GET` | `/api/lost-items/<item_id>/comments/` | 댓글 목록 조회 | 🔒 |
| `POST` | `/api/lost-items/<item_id>/comments/` | 댓글 작성 | 🔒 |

---

### 공통 응답 형식

**성공:**
```json
{
  "status": "success",
  "message": "설명 메시지",
  "data": { ... }
}
```

**에러:**
```json
{
  "status": "error",
  "error_code": "AUTH_001",
  "message": "에러 설명",
  "data": null
}
```

**에러 코드:**

| 코드 | 설명 |
|------|------|
| `REQ_001` | 잘못된 요청 (필수 필드 누락) |
| `AUTH_001` | 아이디 또는 비밀번호 불일치 |
| `AUTH_002` | 이미 등록된 로그인 ID |
| `AUTH_004` | e-Campus 서버 연결 오류 |
| `AUTH_005` | e-Campus 알 수 없는 응답 |
| `DB_001` | 데이터베이스 저장 오류 |

---

## 🧠 적용 알고리즘

### 강의 검색 (`core/utils/course_search.py`)

| 알고리즘 | 용도 | 시간 복잡도 |
|----------|------|-------------|
| **Trie (트라이)** | 강의명/교수명 접두사 자동완성 | O(L) (L=접두사 길이) |
| **Rabin-Karp** | 부분 문자열 패턴 매칭 | O(N+M) 평균 |
| **한글 초성 검색** | `ㄱㄱ` → "고급", "기계" 등 매칭 | O(L) |
| **커스텀 HashTable** | course_id 기반 O(1) 조회 | O(1) 평균 |

### 분실물 검색 (`core/api/losts.py`)

| 알고리즘 | 용도 | 시간 복잡도 |
|----------|------|-------------|
| **KMP** | 정확한 패턴 매칭 | O(N+M) |
| **한글 자모 분리 (Jamo Decomposition)** | 자모 단위 유사도 비교 | O(N) |
| **Levenshtein Distance** | 오타 허용 유사 검색 | O(N×M) |

### 스터디룸 추천 (`core/api/rooms.py`)

- **가중 점수 기반 랭킹**: 수용인원 적합도 + 시설 매칭 점수
- **시간 슬롯 충돌 검사**: 08:00~22:00 (14시간) 타임라인 기반

### 장학금 추천 (`core/api/scholarships.py`)

- **다항 조건 매칭 스코어링**: GPA, 소득 분위, 중복수혜 여부 가중 평가
- **D-Day 기반 정렬**: 마감일 기준 긴급도 제공

---

## 🔐 인증 방식

**JWT (JSON Web Token)** 기반 인증을 사용합니다.

```
Authorization: Bearer <access_token>
```

| 토큰 | 유효 기간 | 용도 |
|------|-----------|------|
| Access Token | 1일 | API 요청 인증 |
| Refresh Token | 7일 | Access Token 갱신 |

**인증 플로우:**

```
1. POST /api/students/login (e-Campus 인증)
   ├── 기존 사용자 → JWT 토큰 즉시 발급
   └── 신규 사용자 → "첫 로그인" 응답
2. POST /api/students/info (회원가입 → JWT 발급)
3. 이후 API 요청 시 Authorization 헤더에 토큰 포함
```

---

## 🧪 테스트

`core/tests.py`에 인증 관련 유닛 테스트가 포함되어 있습니다.

```bash
python manage.py test core
```

### 테스트 케이스

| 테스트 | 설명 |
|--------|------|
| `test_login_missing_credentials` | 필수 필드 누락 시 400 응답 |
| `test_login_invalid_credentials` | e-Campus 인증 실패 시 401 응답 |
| `test_login_first_time_success` | 첫 로그인 시 성공 + data=null |
| `test_login_existing_user_success` | 기존 사용자 로그인 + JWT 토큰 발급 |
| `test_student_info_missing_login_id` | login_id 누락 시 400 응답 |
| `test_student_info_duplicate_user` | 중복 사용자 등록 시 400 응답 |
| `test_student_info_success` | 회원가입 성공 + JWT 토큰 발급 |

> e-Campus 외부 API 호출은 `unittest.mock.patch`로 모킹합니다.

---

## 📋 로깅

`config/settings.py`에 설정된 로깅 시스템:

| 핸들러 | 레벨 | 출력 |
|--------|------|------|
| **console** | INFO | 터미널 (`[LEVEL] message`) |
| **file** | DEBUG | `alphakit_backend.log` (`[LEVEL] timestamp \| module \| message`) |

모든 `core.api` 모듈의 로그가 기록됩니다.

```
[INFO] 2026-05-28 10:00:00 | login | === [API CALL] POST /students/login ===
[DEBUG] 2026-05-28 10:00:00 | login | Request Data: username=testuser, ...
```

---

## 📝 기타 참고 사항

- **e-Campus 연동**: 로그인은 가천대학교 e-Campus (`https://cyber.gachon.ac.kr/login/index.php`)에 실제 HTTP POST 요청을 보내 인증합니다.
- **비밀번호 저장**: Django의 `make_password()`를 사용하여 해시 저장합니다.
- **미디어 파일**: `DEBUG=True`일 때 Django가 직접 미디어 파일을 서빙합니다 (프로덕션에서는 Nginx 등 별도 설정 필요).
- **Django Admin**: 모든 모델이 Admin에 등록되어 있어 `http://localhost:8000/admin/`에서 데이터를 관리할 수 있습니다.
- **초성 검색**: 한글 유니코드 분리를 통해 `ㅈㄱ` 입력 시 "자료구조", "전공필수" 등을 검색할 수 있습니다.
