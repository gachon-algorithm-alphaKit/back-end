from django.db import models
from .campus import Place
from .users import Student

class StudyRoom(models.Model):
    room_id = models.AutoField(primary_key=True)
    place = models.ForeignKey(Place, on_delete=models.CASCADE, db_column='place_id', null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    capacity = models.IntegerField(null=True, blank=True)
    facilities = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name or f"Room {self.room_id}"

class Reservation(models.Model):
    reservation_id = models.AutoField(primary_key=True)
    room = models.ForeignKey(StudyRoom, on_delete=models.CASCADE, db_column='room_id', null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, db_column='student_id', null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    head_count = models.IntegerField(null=True, blank=True)
    reservation_group_id = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
