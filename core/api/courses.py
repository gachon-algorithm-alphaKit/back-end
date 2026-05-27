import math
from django.http import JsonResponse
from core.utils.course_search import search_engine

def get_courses(request):
    try:
        # Check if engine is loaded, fallback to load_data if not
        if not search_engine.is_loaded:
            search_engine.load_data()

        # Parse query parameters
        school_id = request.GET.get('school_id', '1')
        keyword = request.GET.get('keyword', '').strip()
        professor_name = request.GET.get('professor_name', '').strip()
        search_type = request.GET.get('search_type', '').strip()
        
        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            page = 1
            
        try:
            limit = int(request.GET.get('limit', 20))
        except ValueError:
            limit = 20

        results = []
        is_searched = False
        applied_algorithm = []

        if search_type == 'name' and keyword:
            results = search_engine.search(keyword, field='name')
            applied_algorithm.append("Trie/Rabin-Karp (Name)")
            is_searched = True
        elif search_type == 'professor' and professor_name:
            results = search_engine.search(professor_name, field='professor')
            applied_algorithm.append("Trie/Rabin-Karp (Professor)")
            is_searched = True
        elif search_type == 'content' and keyword:
            results = search_engine.search_by_content(keyword)
            applied_algorithm.append("Rabin-Karp (Content)")
            is_searched = True
        elif keyword and professor_name:
            # Fallback if no specific search_type but both provided
            course_hits = search_engine.search(keyword, field='name')
            prof_hits = search_engine.search(professor_name, field='professor')
            prof_ids = {r['course_id'] for r in prof_hits}
            results = [c for c in course_hits if c['course_id'] in prof_ids]
            applied_algorithm.append("Intersection (Name & Professor)")
            is_searched = True
        elif keyword:
            results = search_engine.search(keyword, field='name')
            applied_algorithm.append("Trie/Rabin-Karp (Name)")
            is_searched = True
        elif professor_name:
            results = search_engine.search(professor_name, field='professor')
            applied_algorithm.append("Trie/Rabin-Karp (Professor)")
            is_searched = True
        else:
            # No search criteria, return all
            results = search_engine.courses
            applied_algorithm.append("None")

        total_items = len(results)
        total_pages = math.ceil(total_items / limit) if limit > 0 else 1
        
        # Pagination slice
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_data = results[start_idx:end_idx]

        response_data = {
            "status": "success",
            "message": "통합 조건 검색 및 강의 조회를 성공적으로 완료했습니다.",
            "search_info": {
                "applied_algorithm": " + ".join(applied_algorithm),
                "is_searched": is_searched
            },
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_items
            },
            "data": paginated_data
        }
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)
