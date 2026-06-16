from django.http import JsonResponse
from django.core.cache import cache
from core.models import Place, CampusEdge, PlaceAlias

def get_campus_graph(request):
    """
    GET /api/campus/graph/
    반환 형태:
    {
        "status": "success",
        "data": {
            "nodes": { "P_01": {"lat": ..., "lon": ..., "type": "PATH"}, ... },
            "edges": [ ["P_01", "P_02"], ... ],
            "aliases": { "기숙사": "제2학생생활관", ... }
        }
    }
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
    GET /api/campus/map/
    Query parameters:
      - w, h, center, level, format
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
