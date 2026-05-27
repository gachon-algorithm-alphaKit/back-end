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
