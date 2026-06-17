from django.db import models

class School(models.Model):
    school_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name or f"School {self.school_id}"

class Place(models.Model):
    """
    [Model] 캠퍼스 내 주요 장소(건물, 시설물) 및 경로 노드(Path Node)
    길찾기 그래프의 정점(Vertex) 역할을 수행하며, A* 알고리즘의 거리 계산(Heuristic)을 위한 위경도 좌표를 포함합니다.
    """
    place_id = models.AutoField(primary_key=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, db_column='school_id', null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    place_type = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.name or f"Place {self.place_id}"

class CampusEdge(models.Model):
    """
    [Model] 캠퍼스 길찾기 경로의 간선(Edge)
    두 Place 노드 간의 물리적 연결 관계(무방향 그래프 구조)를 나타내며, is_walkable 속성으로 보행 가능 여부를 제어합니다.
    """
    edge_id = models.AutoField(primary_key=True)
    node1 = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='edges_from')
    node2 = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='edges_to')
    is_walkable = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.node1.name} <-> {self.node2.name}"

class PlaceAlias(models.Model):
    """
    [Model] 장소 별칭(Alias) 매핑 메타데이터
    사용자가 입력하는 다양한 동의어 및 약칭(예: '기숙사')을 정규화된 Place 식별명(예: '제2학생생활관')으로 Resolution 하기 위한 테이블입니다.
    """
    alias_id = models.AutoField(primary_key=True)
    place = models.ForeignKey(Place, on_delete=models.CASCADE, db_column='place_id')
    alias_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.alias_name} -> {self.place.name}"
