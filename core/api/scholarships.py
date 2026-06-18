# -*- coding: utf-8 -*-
import json
from datetime import datetime
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage
from django.views.decorators.csrf import csrf_exempt
from core.models import Scholarship 

# ---------------------------------------------------------------------------
# 🛠️ 비즈니스 로직 헬퍼 함수
# ---------------------------------------------------------------------------
def parse_minimum_amount(amount_text):
    """텍스트 형태의 지원 금액(ex: '100만원', '등록금 100%')을 정수로 파싱합니다."""
    if not amount_text:
        return 0
    if "만원" in amount_text:
        try:
            # 숫자만 추출하여 10,000을 곱함
            num = int(''.join(filter(str.isdigit, amount_text)))
            return num * 10000
        except ValueError:
            return 0
    elif "등록금" in amount_text:
        return 3500000  # 등록금 전액 지원일 경우 가상의 평균 등록금으로 환산
    return 0

def calculate_d_day(deadline):
    """현재 시간 기준으로 마감일까지 남은 일(D-Day)을 계산합니다."""
    if not deadline:
        return -1
    now = timezone.now()
    delta = deadline - now
    return delta.days if delta.days >= 0 else -1

def evaluate_scholarship_match(student, scholarship):
    """학생의 스펙과 장학금 조건을 비교하여 매칭률과 적합 여부를 판별합니다."""
    duplicate_pass = True
    if student.get('awarded_last_semester', False) and not scholarship.duplicate_allowed:
        duplicate_pass = False

    if not duplicate_pass:
        return 0, False

    gpa_pass = True
    if scholarship.required_gpa is not None:
        gpa_pass = student['gpa'] >= float(scholarship.required_gpa)

    income_pass = True
    if scholarship.required_income_bracket is not None:
        income_pass = student['income_bracket'] <= scholarship.required_income_bracket

    is_fully_matched = gpa_pass and income_pass

    # 매칭 점수 산정 알고리즘
    score = 50
    if gpa_pass: score += 20
    if income_pass: score += 20
    if is_fully_matched: score += 10

    return max(0, min(score, 100)), is_fully_matched

# ---------------------------------------------------------------------------
# 🌐 [API] 학생 맞춤형 장학제도 목록 조회 엔드포인트
# ---------------------------------------------------------------------------
@csrf_exempt
def get_scholarships(request):
    if request.method != "GET":
        return JsonResponse({"status": "error", "message": "GET 메서드만 허용됩니다."}, status=405)

    try:
        # 1. 토큰 검증 시뮬레이션
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({"status": "error", "message": "인증 토큰이 누락되었거나 유효하지 않습니다."}, status=401)

        # 2. 로그인한 유저의 정보 및 쿼리 파라미터(우선) 파싱
        try:
            req_gpa = float(request.GET.get('gpa', 3.85))
            req_income = int(request.GET.get('income_bracket', 5))
            req_awarded_str = request.GET.get('awarded_last_semester', 'false').lower()
            req_awarded = req_awarded_str == 'true'
        except ValueError:
            req_gpa = 3.85
            req_income = 5
            req_awarded = False
            
        current_student = {
            "student_id": 1,
            "gpa": req_gpa,
            "income_bracket": req_income,
            "awarded_last_semester": req_awarded
        }

        # 3. 페이지네이션 쿼리 파라미터 파싱
        page_num = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))

        from django.db.models import Q
        # 4. 전체 장학금 쿼리셋 가져오기 (마감일이 남은 순서대로 정렬)
        queryset = Scholarship.objects.filter(
            Q(dead_line__gte=timezone.now()) | Q(dead_line__isnull=True)
        ).order_by('dead_line')

        # 5. 페이징 처리
        paginator = Paginator(queryset, limit)
        try:
            page_obj = paginator.page(page_num)
        except EmptyPage:
            page_obj = []

        # 6. 학생 데이터 기반 매칭 연산 및 직렬화
        response_data = []
        
        # [선형 탐색 및 순회 (Linear Search / Traversal)]
        # - 역할: 한 페이지 분량의 배열(page_obj) 요소를 처음부터 끝까지 순차적으로 하나씩 접근
        # - 특징: 페이징된 결과 개수(N)만큼 비례하여 실행되므로 O(N)의 시간 복잡도 발생
        for doc in page_obj:
            # 매칭 알고리즘 실행
            match_score, is_fully_matched = evaluate_scholarship_match(current_student, doc)
            d_day = calculate_d_day(doc.dead_line)
            min_amount = parse_minimum_amount(doc.amount)

            response_data.append({
                "scholarship_id": doc.scholarship_id,
                "school_id": doc.school_id if doc.school_id else 1,
                "name": doc.name,
                "dead_line": doc.dead_line.strftime("%Y-%m-%dT%H:%M:%SZ") if doc.dead_line else None,
                "minimum_amount": min_amount,
                "required_gpa": float(doc.required_gpa) if doc.required_gpa else 0,
                "required_income_bracket": doc.required_income_bracket if doc.required_income_bracket else 10,
                "duplicate_allowed": doc.duplicate_allowed,
                "recommendation_info": {
                    "match_score": match_score,
                    "d_day": d_day,
                    "is_fully_matched": is_fully_matched
                }
            })

        # 매칭 점수가 높은 순(내림차순), 금액이 높은 순(내림차순)으로 2차 정렬
        # [팀소트 알고리즘 (Timsort) & Tuple 자료구조 사용] 
        # - Tuple 역할: 파이썬의 튜플 사전식 비교(Lexicographical Comparison)를 활용하여 복합 키 생성
        # - Tuple 이유: 다중 조건 정렬을 간결하게 구현하고, 불변형(Immutable) 덕분에 정렬 처리가 효율적임
        response_data.sort(key=lambda x: (x['recommendation_info']['match_score'], x['minimum_amount']), reverse=True)

        # 7. 명세서 규격에 맞춘 성공 응답 반환
        return JsonResponse({
            "status": "success",
            "message": "학생 정보에 맞춘 장학금 추천 목록을 성공적으로 불러왔습니다.",
            "data": response_data
        }, json_dumps_params={'ensure_ascii': False}, status=200)

    except Exception as e:
        return JsonResponse({"status": "error", "message": f"서버 내부 오류: {str(e)}"}, status=500)
