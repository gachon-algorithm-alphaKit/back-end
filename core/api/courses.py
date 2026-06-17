# 실행 환경: Python 3.x, Django
# 필요 라이브러리: django, (검색 엔진은 core/utils/course_search.py에서 import)
# Input 데이터 출처: 가천대학교 강의 정보 (직접 수집 후 DB 저장)
#   - 엔드포인트: GET /api/courses/
#   - 파라미터: school_id, keyword, professor_name, search_type(name/professor/content), page, limit

import math
from django.http import JsonResponse

# 자료구조: Trie(강의명/교수명/초성 접두사 탐색), HashTable(course_id O(1) 조회)
# 알고리즘: Trie 탐색(접두사 자동완성), Rabin-Karp(부분 문자열 탐색)
from core.utils.course_search import search_engine


def get_courses(request):
    """
    강의 검색 API
    - search_type=name      : Trie 탐색 + Rabin-Karp (강의명)
    - search_type=professor : Trie 탐색 + Rabin-Karp (교수명)
    - search_type=content   : Rabin-Karp 단독 (강의 설명 키워드 탐색)
    """
    try:
        if not search_engine.is_loaded:
            search_engine.load_data()

        school_id      = request.GET.get('school_id', '1')
        keyword        = request.GET.get('keyword', '').strip()
        professor_name = request.GET.get('professor_name', '').strip()
        search_type    = request.GET.get('search_type', '').strip()

        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            page = 1

        try:
            limit = int(request.GET.get('limit', 20))
        except ValueError:
            limit = 20

        results           = []
        is_searched       = False
        applied_algorithm = []

        if search_type == 'name' and keyword:
            # 알고리즘: Trie 탐색(접두사 일치) + Rabin-Karp(부분 일치) - 강의명 검색
            results = search_engine.search(keyword, field='name')
            applied_algorithm.append("Trie/Rabin-Karp (Name)")
            is_searched = True

        elif search_type == 'professor' and professor_name:
            # 알고리즘: Trie 탐색(접두사 일치) + Rabin-Karp(부분 일치) - 교수명 검색
            results = search_engine.search(professor_name, field='professor')
            applied_algorithm.append("Trie/Rabin-Karp (Professor)")
            is_searched = True

        elif search_type == 'content' and keyword:
            # 알고리즘: Rabin-Karp 단독 - 강의 설명(description) 내 키워드 탐색
            results = search_engine.search_by_content(keyword)
            applied_algorithm.append("Rabin-Karp (Content)")
            is_searched = True

        elif keyword and professor_name:
            # 강의명 + 교수명 교집합 검색 (각각 Trie+Rabin-Karp 후 course_id 교차)
            course_hits = search_engine.search(keyword, field='name')
            prof_hits   = search_engine.search(professor_name, field='professor')
            prof_ids    = {r['course_id'] for r in prof_hits}
            results     = [c for c in course_hits if c['course_id'] in prof_ids]
            applied_algorithm.append("Intersection (Name & Professor)")
            is_searched = True

        elif keyword:
            # 알고리즘: Trie 탐색 + Rabin-Karp - 강의명 기본 검색
            results = search_engine.search(keyword, field='name')
            applied_algorithm.append("Trie/Rabin-Karp (Name)")
            is_searched = True

        elif professor_name:
            # 알고리즘: Trie 탐색 + Rabin-Karp - 교수명 기본 검색
            results = search_engine.search(professor_name, field='professor')
            applied_algorithm.append("Trie/Rabin-Karp (Professor)")
            is_searched = True

        else:
            # 검색 조건 없음: HashTable 기반 인메모리 전체 목록 반환
            results = search_engine.courses
            applied_algorithm.append("None")

        # 페이지네이션
        total_items    = len(results)
        total_pages    = math.ceil(total_items / limit) if limit > 0 else 1
        start_idx      = (page - 1) * limit
        end_idx        = start_idx + limit
        paginated_data = results[start_idx:end_idx]

        response_data = {
            "status" : "success",
            "message": "통합 조건 검색 및 강의 조회를 성공적으로 완료했습니다.",
            "search_info": {
                "applied_algorithm": " + ".join(applied_algorithm),
                "is_searched"      : is_searched
            },
            "pagination": {
                "current_page": page,
                "total_pages" : total_pages,
                "total_items" : total_items
            },
            "data": paginated_data
        }
        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({
            "status" : "error",
            "message": str(e)
        }, status=500)
