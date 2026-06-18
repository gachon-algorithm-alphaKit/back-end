import json
import math

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.utils import timezone

from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from core.models.community import LostItemPost
from core.models.campus import School

# 실행 환경: Python 3.x , Django
# 필요 라이브러리: json, JsonResponse, csrf_exempt, Q, timezone, math, TokenError, InvalidToken, AccessToken
# Input 데이터 출처: Gemini 생성 (추후 학교별 API 로 대체 가능)

def get_student_id_from_token(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    try:
        token = AccessToken(auth_header.split(' ')[1])
        return int(token['student_id'])
    except (TokenError, InvalidToken, ValueError, TypeError):
        return None

# 자료구조: 1차원 배열(List) (KMP 알고리즘의 LPS 배열 구현용)
# 프로세싱 과정:
# 1. 검색어(pattern)를 분석하여 접두사와 접미사가 일치하는 최대 길이를 기록한 LPS 배열을 생성합니다.
# 2. 본문 텍스트를 순회하며 패턴과 한 글자씩 비교합니다.
# 3. 불일치가 발생하면 되돌아가지 않고, LPS 배열을 참고하여 건너뜀으로써 탐색 속도를 최적화합니다.
# 4. 대소문자 무시를 위해 외부에서 lower() 적용
def compute_lps(pattern):
    lps = [0] * len(pattern)
    length = 0  # 이전 접두사/접미사 일치 길이
    i = 1
    
    # 1. 패턴 전체를 순회하며 LPS 배열을 채웁니다.
    while i < len(pattern):
        # 1-1. 현재 문자와 이전 접두사 문자가 일치하는 경우
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        # 1-2. 일치하지 않는 경우
        else:
            if length != 0:
                # 바로 이전의 일치했던 위치로 돌아가서 다시 비교합니다.
                length = lps[length - 1]
            else:
                # 일치하는 접두사가 없으면 0으로 기록하고 다음 문자로 넘어갑니다.
                lps[i] = 0
                i += 1
    return lps

def kmp_search(text, pattern):
    if not pattern: return False
    
    # 1. 검색어에 대한 LPS 배열을 먼저 계산합니다.
    lps = compute_lps(pattern)
    i = 0  # 본문(text) 인덱스
    j = 0  # 패턴(pattern) 인덱스
    
    # 2. 본문 텍스트를 순회하며 탐색을 시작합니다.
    while i < len(text):
        # 2-1. 문자가 일치하면 두 인덱스를 모두 증가시킵니다.
        if pattern[j] == text[i]:
            i += 1
            j += 1
            
        # 2-2. 패턴의 끝까지 모두 일치했다면 검색 성공입니다.
        if j == len(pattern):
            return True
            
        # 2-3. 일치하지 않는 문자가 발생했을 때
        elif i < len(text) and pattern[j] != text[i]:
            if j != 0:
                # LPS 배열을 참고하여 불필요한 비교를 건너뜁니다 (이 점이 KMP의 핵심 최적화입니다).
                j = lps[j - 1]
            else:
                # 패턴의 첫 글자부터 틀렸다면 본문 인덱스만 1 증가시킵니다.
                i += 1
    return False

# 자료구조: 1차원 배열(List) (Levenshtein 알고리즘의 DP 테이블 공간 최적화용)
# 프로세싱 과정:
# 1. 전체 2차원 DP 행렬을 만드는 대신, 이전 행(previous_row)과 현재 행(current_row) 단 2개의 1차원 배열만 사용해 메모리를 절약합니다.
# 2. 두 문자열의 글자들을 순회하며 삽입, 삭제, 대체 중 가장 적은 비용이 드는 연산 횟수를 현재 행에 누적 기록합니다.
# 3. 최종적으로 행의 마지막 인덱스 값을 반환하여 두 문자열이 얼마나 다른지(거리)를 측정합니다.
def levenshtein(s1, s2):
    # 항상 긴 문자열을 s1으로 두어 메모리 사용량(s2의 길이)을 최소화합니다.
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
        
    # 1. 첫 번째 행을 초기화합니다. (0부터 s2의 길이까지)
    previous_row = range(len(s2) + 1)
    
    # 2. 긴 문자열(s1)의 문자들을 차례대로 순회합니다.
    for i, c1 in enumerate(s1):
        # 현재 행의 첫 번째 값은 항상 삭제 연산의 누적값(i+1)입니다.
        current_row = [i + 1]
        
        # 3. 짧은 문자열(s2)의 문자들과 하나씩 비교합니다.
        for j, c2 in enumerate(s2):
            # 삽입, 삭제, 변경 중 가장 적은 비용이 드는 연산을 선택합니다.
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            
            # 4. 세 가지 경우 중 최솟값을 현재 행에 기록합니다.
            current_row.append(min(insertions, deletions, substitutions))
            
        # 5. 다음 반복을 위해 현재 행을 이전 행으로 업데이트합니다.
        previous_row = current_row
        
    # 최종적으로 배열의 마지막 원소가 두 문자열 사이의 거리(최소 연산 횟수)가 됩니다.
    return previous_row[-1]

#한글 자모 분리 기반 Levenshtein Distance (오타 및 유사도 탐색)
def decompose_hangul(text):
    result = []
    for char in text:
        code = ord(char)
        if 0xAC00 <= code <= 0xD7A3:
            code -= 0xAC00
            cho = code // 588
            jung = (code % 588) // 28
            jong = code % 28
            result.extend([chr(0x1100 + cho), chr(0x1161 + jung), chr(0x11A7 + jong) if jong > 0 else ' '])
        else:
            result.append(char)
    return "".join(result)

def get_fuzzy_match_score(text, keyword):
    """
    한글 자모를 분리하여 더 강력한 오타 검색을 지원합니다.
    자모 기준의 거리를 반환합니다.
    """
    if not keyword: return 0
    text_dec = decompose_hangul(text.lower())
    keyword_dec = decompose_hangul(keyword.lower())
    
    min_dist = float('inf')
    k_len = len(keyword_dec)
    
    if len(text_dec) >= k_len:
        # 단어 단위로 검사
        words = text.lower().split()
        for word in words:
            word_dec = decompose_hangul(word)
            dist = levenshtein(word_dec, keyword_dec)
            min_dist = min(min_dist, dist)
            
        # 여러 단어로 이루어진 키워드일 경우를 대비한 윈도우 검사 (자모 기준)
        for i in range(len(text_dec) - k_len + 1):
            window = text_dec[i:i+k_len]
            dist = levenshtein(window, keyword_dec)
            min_dist = min(min_dist, dist)
    else:
        min_dist = levenshtein(text_dec, keyword_dec)
        
    return min_dist


@csrf_exempt
def search_lost_items(request):
    try:
        if request.method == "POST":
            body = json.loads(request.body)
            school_id = body.get("school_id", 1)
            keyword = body.get("keyword", "").strip()
            page = int(body.get("page", 1))
            limit = int(body.get("limit", 10))
        else:
            school_id = int(request.GET.get("school_id", 1))
            keyword = request.GET.get("keyword", "").strip()
            page = int(request.GET.get("page", 1))
            limit = int(request.GET.get("limit", 10))
            
        offset = (page - 1) * limit
        student_id = get_student_id_from_token(request)
            
        if not keyword:
            qs = LostItemPost.objects.filter(school_id=school_id).order_by('-create_time')
            total_items = qs.count()
            total_pages = math.ceil(total_items / limit) if limit > 0 else 1
            items = qs[offset:offset+limit]
            
            return JsonResponse({
                "status": "success",
                "message": "전체 분실물 목록을 불러왔습니다.",
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_items": total_items
                },
                "data": [format_item_dict(item, current_student_id=student_id) for item in items]
            }, json_dumps_params={'ensure_ascii': False}, status=200)

        # 1차 필터링
        keyword_lower = keyword.lower()
        bigrams = [keyword_lower[i:i+2] for i in range(len(keyword_lower)-1)] if len(keyword_lower) > 1 else [keyword_lower]
        
        q_obj = Q()
        for bi in bigrams:
            q_obj |= Q(title__icontains=bi) | Q(description__icontains=bi)
        
        q_obj |= Q(title__icontains=keyword_lower) | Q(description__icontains=keyword_lower)

        initial_qs = LostItemPost.objects.filter(school_id=school_id).filter(q_obj).distinct()
        
        matched_items = []
        analyzed_count = initial_qs.count()
        
        for item in initial_qs:
            title = item.title or ""
            desc = item.description or ""
            combined_text = f"{title} {desc}".lower()
            
            # 단계 A: KMP 알고리즘으로 100% 일치하는 단어가 있는지 검사
            is_exact_match = kmp_search(combined_text, keyword_lower)
            
            if is_exact_match:
                match_score = {"is_exact_match": True, "levenshtein_distance": 0}
                matched_items.append(format_item_dict(item, current_student_id=student_id, match_score=match_score))
                continue
                
            # 단계 B: 한글 자모 분리 기반 Levenshtein
            l_dist = get_fuzzy_match_score(combined_text, keyword_lower)
            
            # 자모 단위이므로 기준 거리를 넉넉히 줌 (예: 자모 4개까지 오타 허용)
            if l_dist <= 4:
                match_score = {"is_exact_match": False, "levenshtein_distance": l_dist}
                matched_items.append(format_item_dict(item, current_student_id=student_id, match_score=match_score))

        matched_items.sort(key=lambda x: (
            not x['match_score']['is_exact_match'], 
            x['match_score']['levenshtein_distance']
        ))
        
        total_items = len(matched_items)
        total_pages = math.ceil(total_items / limit) if limit > 0 else 1
        paginated_items = matched_items[offset:offset+limit]

        return JsonResponse({
            "status": "success",
            "message": "입력하신 검색어와 가장 유사한 분실물을 찾았습니다.",
            "search_info": {
                "applied_algorithm": ["KMP", "Jamo-Levenshtein"],
                "analyzed_items_count": analyzed_count
            },
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_items
            },
            "data": paginated_items
        }, json_dumps_params={'ensure_ascii': False}, status=200)

    except Exception as e:
        return JsonResponse({"status": "error", "message": f"서버 내부 오류: {str(e)}"}, status=500)
@csrf_exempt
def suggest_lost_items(request):
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "POST 메서드만 허용됩니다."}, status=405)
        body = json.loads(request.body)
        keyword = body.get("keyword", "").strip()
        # student_id = get_student_id_from_token(request)  # optional auth if needed
        if not keyword:
            recent_qs = LostItemPost.objects.order_by('-create_time')[:5]
            data = [{"name": item.title} for item in recent_qs]
            return JsonResponse({"status": "success", "data": data}, json_dumps_params={'ensure_ascii': False}, status=200)
        # Compute fuzzy match scores for all items
        all_items = LostItemPost.objects.all()
        scored = []
        for item in all_items:
            title = item.title or ""
            dist = get_fuzzy_match_score(title, keyword)
            scored.append((dist, title))
        scored.sort(key=lambda x: x[0])
        top5 = [{"name": name} for _, name in scored[:5]]
        return JsonResponse({"status": "success", "data": top5}, json_dumps_params={'ensure_ascii': False}, status=200)
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"서버 내부 오류: {str(e)}"}, status=500)
def format_item_dict(item, current_student_id=None, match_score=None):
    img_url = ""
    if item.lost_item_img:
        if item.lost_item_img.name.startswith("http"):
            img_url = item.lost_item_img.name
        else:
            img_url = item.lost_item_img.url

    author_name = "알 수 없음"
    author_dept = "소속 없음"
    author_profile_img = ""

    if item.student:
        author_name = item.student.name or "알 수 없음"
        author_dept = item.student.major or "소속 없음"
        if item.student.profile_img:
            if item.student.profile_img.name.startswith("http"):
                author_profile_img = item.student.profile_img.name
            else:
                author_profile_img = item.student.profile_img.url

    data = {
        "item_id": item.item_id,
        "school_id": item.school_id_id if hasattr(item, 'school_id_id') else item.school_id,
        "student_id": item.student_id_id if hasattr(item, 'student_id_id') else item.student_id,
        "title": item.title,
        "is_anonymous": item.is_anonymous,
        "category": item.category,
        "place": item.place or "",
        "description": item.description,
        "status": item.status,
        "lost_item_img": img_url,
        "create_time": item.create_time.isoformat() if item.create_time else "",
        "is_mine": bool(current_student_id and item.student_id and int(item.student_id) == int(current_student_id)),
        "author_name": author_name,
        "author_dept": author_dept,
        "author_profile_img": author_profile_img,
    }
    if match_score:
        data["match_score"] = match_score
    return data

@csrf_exempt
def handle_lost_items(request):
    # 2. 분실물 신규 등록 (POST)
    if request.method == "POST":
        try:
            student_id = get_student_id_from_token(request)
            if not student_id:
                return JsonResponse({"status": "error", "message": "유효하지 않은 인증 토큰입니다."}, status=401)

            # multipart/form-data 파싱
            school_id = request.POST.get("school_id", 1)
            place_id = request.POST.get("place_id")
            title = request.POST.get("title", "").strip()
            is_anonymous_str = request.POST.get("is_anonymous", "false").lower()
            is_anonymous = is_anonymous_str == "true"
            category = request.POST.get("category", "")
            place = request.POST.get("place", "")
            description = request.POST.get("description", "").strip()
            
            image_file = request.FILES.get("lost_item_img")

            # 유효성 검사 (필수 항목 체크)
            if not title or not category:
                return JsonResponse({"status": "error", "message": "제목과 카테고리는 필수 입력 항목입니다."}, status=400)

            school = School.objects.filter(school_id=school_id).first()
            
            new_item = LostItemPost.objects.create(
                school=school,
                place=place,
                student_id=student_id,
                title=title,
                is_anonymous=is_anonymous,
                category=category,
                description=description,
                lost_item_img=image_file,
                create_time=timezone.now()
            )

            return JsonResponse({
                "status": "success",
                "message": "분실물 게시글이 성공적으로 등록되었습니다.",
                "data": format_item_dict(new_item, current_student_id=student_id)
            }, json_dumps_params={'ensure_ascii': False}, status=201)

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"서버 내부 오류: {str(e)}"}, status=500)

    # 허용되지 않은 메서드 차단
    else:
        return JsonResponse({"status": "error", "message": "POST 메서드만 허용됩니다."}, status=405)

@csrf_exempt
def get_my_lost_items(request):
    if request.method == "GET":
        try:
            student_id = get_student_id_from_token(request)
            if not student_id:
                return JsonResponse({"status": "error", "message": "유효하지 않은 인증 토큰입니다."}, status=401)
                
            page = int(request.GET.get("page", 1))
            limit = int(request.GET.get("limit", 10))
            
            offset = (page - 1) * limit
            
            qs = LostItemPost.objects.filter(student_id=student_id).order_by('-create_time')
            total_items = qs.count()
            total_pages = math.ceil(total_items / limit) if limit > 0 else 1
            
            items = qs[offset:offset+limit]
            
            return JsonResponse({
                "status": "success",
                "message": "내가 작성한 분실물 게시글을 성공적으로 불러왔습니다.",
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_items": total_items
                },
                "data": [format_item_dict(item, current_student_id=student_id) for item in items]
            }, json_dumps_params={'ensure_ascii': False}, status=200)
            
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"서버 내부 오류: {str(e)}"}, status=500)
    return JsonResponse({"status": "error", "message": "GET 메서드만 허용됩니다."}, status=405)

import os
from django.conf import settings

@csrf_exempt
def update_lost_item(request, item_id):
    if request.method == "PUT":
        try:
            student_id = get_student_id_from_token(request)
            if not student_id:
                return JsonResponse({"status": "error", "message": "유효하지 않은 인증 토큰입니다."}, status=401)
            
            # Django에서 PUT으로 전달된 multipart/form-data를 읽기 위한 트릭
            if request.META.get('CONTENT_TYPE', '').startswith('multipart'):
                request.method = "POST"
                request._load_post_and_files()
                request.method = "PUT"
                
            try:
                item = LostItemPost.objects.get(item_id=item_id)
            except LostItemPost.DoesNotExist:
                return JsonResponse({"status": "error", "message": "게시글을 찾을 수 없습니다."}, status=404)
                
            # 소유권 검증
            if item.student_id != student_id:
                return JsonResponse({"status": "error", "message": "수정 권한이 없습니다."}, status=403)
                
            # data 파싱 (프론트에서 data라는 키에 JSON 스트링으로 보냄)
            data_str = request.POST.get('data')
            if not data_str:
                return JsonResponse({"status": "error", "message": "잘못된 요청: data 필드가 누락되었습니다."}, status=400)
                
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                return JsonResponse({"status": "error", "message": "잘못된 요청: data 필드의 JSON 형식이 올바르지 않습니다."}, status=400)
                
            title = data.get('title', '').strip()
            description = data.get('description', '').strip()
            category = data.get('category', item.category)
            place = data.get('place', item.place)
            is_anonymous = data.get('is_anonymous', item.is_anonymous)
            status = data.get('status', item.status)
            
            if not title or not description:
                return JsonResponse({"status": "error", "message": "제목과 특징(설명)은 필수 입력 항목입니다."}, status=400)
                
            # 텍스트 데이터 업데이트
            item.title = title
            item.description = description
            item.category = category
            item.place = place
            item.is_anonymous = is_anonymous
            item.status = status
            
            # 이미지 업데이트 처리
            new_img = request.FILES.get('lost_item_img')
            if new_img:
                # 기존 이미지가 있다면 삭제
                if item.lost_item_img and os.path.isfile(item.lost_item_img.path):
                    os.remove(item.lost_item_img.path)
                item.lost_item_img = new_img
                
            item.save()
            
            return JsonResponse({
                "status": "success",
                "message": "분실물 게시글이 성공적으로 수정되었습니다.",
                "data": format_item_dict(item, current_student_id=student_id)
            }, json_dumps_params={'ensure_ascii': False}, status=200)
            
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"서버 내부 오류: {str(e)}"}, status=500)
            
    elif request.method == "DELETE":
        try:
            student_id = get_student_id_from_token(request)
            if not student_id:
                return JsonResponse({"status": "error", "message": "유효하지 않은 인증 토큰입니다."}, status=401)
                
            try:
                item = LostItemPost.objects.get(item_id=item_id)
            except LostItemPost.DoesNotExist:
                return JsonResponse({"status": "error", "message": "게시글을 찾을 수 없습니다."}, status=404)
                
            if item.student_id != student_id:
                return JsonResponse({"status": "error", "message": "삭제 권한이 없습니다."}, status=403)
                
            # 기존 이미지가 있다면 삭제
            if item.lost_item_img and os.path.isfile(item.lost_item_img.path):
                os.remove(item.lost_item_img.path)
                
            item.delete()
            return JsonResponse({"status": "success", "message": "게시글이 삭제되었습니다."}, status=200)
            
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"서버 내부 오류: {str(e)}"}, status=500)
            
    return JsonResponse({"status": "error", "message": "허용되지 않는 메서드입니다."}, status=405)

@csrf_exempt
def claim_lost_item(request, item_id):
    if request.method == "POST":
        try:
            student_id = get_student_id_from_token(request)
            if not student_id:
                return JsonResponse({"status": "error", "message": "유효하지 않은 인증 토큰입니다."}, status=401)
                
            try:
                item = LostItemPost.objects.get(item_id=item_id)
            except LostItemPost.DoesNotExist:
                return JsonResponse({"status": "error", "message": "게시글을 찾을 수 없습니다."}, status=404)
                
            item.status = True
            item.save()
            return JsonResponse({"status": "success", "message": "수령 신청이 완료되었습니다."}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"서버 내부 오류: {str(e)}"}, status=500)
    return JsonResponse({"status": "error", "message": "POST 메서드만 허용됩니다."}, status=405)
