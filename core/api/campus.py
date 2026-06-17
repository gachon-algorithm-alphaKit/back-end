from django.http import JsonResponse
from django.core.cache import cache
from core.models import Place, CampusEdge, PlaceAlias

def get_campus_graph(request):
    """
    [API] 캠퍼스 길찾기 그래프 데이터 제공
    
    Description:
      클라이언트(Front-end)의 A* 기반 경로 탐색 및 맵 렌더링을 위한 캠퍼스 노드 및 간선(Edge) 정보를 제공합니다.
      DB 조회 부하 최소화를 위해 1시간 단위로 In-Memory Caching을 적용합니다.
    
    Endpoint: GET /api/campus/graph/
    
    Returns:
      JSON 형태의 Graph 구조
      - nodes: 고유 식별자를 키로 갖는 위경도(lat, lon) 및 노드 타입(type) 매핑 데이터
      - edges: 보행 가능한(is_walkable=True) 연결 관계를 나타내는 노드 이름 쌍(Adjacency List)
      - aliases: 사용자 친화적인 약칭/별칭을 정규 노드명으로 치환하기 위한 Alias 매핑
    """
    if request.method != 'GET':
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
    
    # 1시간(3600초) 동안 캐싱하여 서버 부하 최소화
    cache_key = "campus_graph_data"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return JsonResponse({"status": "success", "data": cached_data})
    
    nodes = {}
    places = Place.objects.all()
    for p in places:
        if p.latitude and p.longitude:
            nodes[p.name] = {
                "lat": float(p.latitude),
                "lon": float(p.longitude),
                "type": p.place_type or "BUILDING"
            }
            
    edges = []
    campus_edges = CampusEdge.objects.filter(is_walkable=True).select_related('node1', 'node2')
    for e in campus_edges:
        if e.node1.name in nodes and e.node2.name in nodes:
            edges.append([e.node1.name, e.node2.name])
            
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
    
    cache.set(cache_key, graph_data, 3600)
    
    return JsonResponse({
        "status": "success",
        "data": graph_data
    })

def get_naver_static_map(request):
    """
    [API] 네이버 Static Map Proxy
    
    Description:
      CORS 정책 우회 및 클라이언트 측 API Key 탈취 방지를 위해 Back-end에서 Naver Static Map API를 대리 호출(Proxy)합니다.
      클라이언트가 전달한 지도 파라미터(중심 좌표, 해상도 등)를 기반으로 정적 지도 이미지 바이너리를 렌더링하여 반환합니다.
      
    Endpoint: GET /api/campus/map/
    
    Query Parameters:
      - w, h: 이미지 크기 (default: 1024x1024)
      - center: 중심 위경도 좌표 (format: "lon,lat")
      - level: 줌 레벨 (default: 16)
      - format: 반환 이미지 포맷 (default: png)
    """
    import requests
    from django.http import HttpResponse

    if request.method != 'GET':
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

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
    
    client_id = '892iyj75cq'
    client_secret = 'ZiJpxXhpGaKwbJVRX5intB1I83C4Z3n314qZosD0'

    headers = {
        'X-NCP-APIGW-API-KEY-ID': client_id,
        'X-NCP-APIGW-API-KEY': client_secret,
        'Referer': 'http://localhost'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            return HttpResponse(response.content, content_type=f'image/{fmt}')
        else:
            return JsonResponse({"status": "error", "message": f"Naver API error: {response.status_code}"}, status=502)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
