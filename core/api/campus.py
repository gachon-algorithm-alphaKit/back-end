# 실행 환경: Python 3.x, Django
# 필요 라이브러리: django (캐싱 및 DB 모델 접근), requests (네이버 맵 API 호출)
# Input 데이터 출처: 가천대학교 캠퍼스 건물 및 지리 정보 DB (Place, CampusEdge, PlaceAlias)
#   - 엔드포인트: GET /api/campus/graph/ (그래프 데이터), GET /api/campus/map/ (지도 이미지)
#   - 파라미터 (/graph/): 없음
#   - 파라미터 (/map/): w, h, center, level, format

from django.http import JsonResponse
from django.core.cache import cache
from core.models import Place, CampusEdge, PlaceAlias

# 자료구조: Graph (Adjacency List 방식의 노드-간선 매핑), HashTable (O(1) 캐싱 및 노드 빠른 접근)
# 알고리즘: 클라이언트 단의 A* (A-Star) 알고리즘을 위한 기반 그래프 구조(Nodes, Edges) 제공

def get_campus_graph(request):
    """
    캠퍼스 길찾기 그래프 데이터 API
    - nodes: 위경도(lat, lon) 및 노드 타입(type) 매핑 데이터 제공
    - edges: 보행 가능한(is_walkable=True) 연결 관계 제공
    - aliases: 사용자 친화적인 약칭/별칭 제공
    """
    if request.method != 'GET':
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
    
    # 캐시 확인: DB 조회 부하 최소화를 위해 1시간 단위 인메모리 캐시(HashTable) 확인
    cache_key = "campus_graph_data"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return JsonResponse({"status": "success", "data": cached_data})
    
    # 1. 노드(Nodes) 구성: Place 객체를 기반으로 노드 정보(좌표 및 타입) 해시테이블 생성
    nodes = {}
    places = Place.objects.all()
    for p in places:
        if p.latitude and p.longitude:
            nodes[p.name] = {
                "lat": float(p.latitude),
                "lon": float(p.longitude),
                "type": p.place_type or "BUILDING"
            }
            
    # 2. 간선(Edges) 구성: 보행 가능한(walkable) CampusEdge 객체를 기반으로 인접 리스트(Adjacency List) 생성
    edges = []
    campus_edges = CampusEdge.objects.filter(is_walkable=True).select_related('node1', 'node2')
    for e in campus_edges:
        if e.node1.name in nodes and e.node2.name in nodes:
            edges.append([e.node1.name, e.node2.name])
            
    # 3. 별칭(Aliases) 구성: PlaceAlias 정보를 기반으로 정규 노드명으로 치환하기 위한 매핑 생성
    aliases = {}
    place_aliases = PlaceAlias.objects.select_related('place')
    for a in place_aliases:
        if a.place.name in nodes:
            aliases[a.alias_name] = a.place.name
            
    graph_data = {
        "nodes": nodes,
        "edges": edges,
        "aliases": aliases
    }
    
    # 캐시 저장: 데이터 구성 후 1시간(3600초) 캐싱 적용
    cache.set(cache_key, graph_data, 3600)
    
    return JsonResponse({
        "status": "success",
        "data": graph_data
    })

def get_naver_static_map(request):
    """
    네이버 Static Map Proxy API
    - CORS 우회 및 API Key 은닉을 위해 백엔드에서 대리 호출 (Proxy)
    """
    import requests
    from django.http import HttpResponse

    if request.method != 'GET':
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

    # 파라미터 파싱
    w = request.GET.get('w', '1024')
    h = request.GET.get('h', '1024')
    center = request.GET.get('center')
    level = request.GET.get('level', '16')
    fmt = request.GET.get('format', 'png')

    if not center:
        return JsonResponse({"status": "error", "message": "center is required"}, status=400)

    url = "https://maps.apigw.ntruss.com/map-static/v2/raster"
    params = {
        'w': w,
        'h': h,
        'center': center,
        'level': level,
        'format': fmt
    }
    
    # 네이버 API 키 설정
    client_id = '892iyj75cq'
    client_secret = 'ZiJpxXhpGaKwbJVRX5intB1I83C4Z3n314qZosD0'

    headers = {
        'X-NCP-APIGW-API-KEY-ID': client_id,
        'X-NCP-APIGW-API-KEY': client_secret,
        'Referer': 'http://localhost'
    }

    try:
        # 네이버 API 호출 및 프록시 반환
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            return HttpResponse(response.content, content_type=f'image/{fmt}')
        else:
            return JsonResponse({"status": "error", "message": f"Naver API error: {response.status_code}"}, status=502)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
