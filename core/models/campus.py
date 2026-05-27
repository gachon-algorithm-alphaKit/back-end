from django.db import models

class School(models.Model):
    school_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name or f"School {self.school_id}"

class Place(models.Model):
    place_id = models.AutoField(primary_key=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, db_column='school_id', null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    place_type = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.name or f"Place {self.place_id}"

class CampusEdge(models.Model):
    edge_id = models.AutoField(primary_key=True)
    node1 = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='edges_from')
    node2 = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='edges_to')
    is_walkable = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.node1.name} <-> {self.node2.name}"

class PlaceAlias(models.Model):
    alias_id = models.AutoField(primary_key=True)
    place = models.ForeignKey(Place, on_delete=models.CASCADE, db_column='place_id')
    alias_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.alias_name} -> {self.place.name}"
