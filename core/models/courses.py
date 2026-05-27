from django.db import models
from .campus import School
from .users import Professor, Student

class Course(models.Model):
    course_id = models.AutoField(primary_key=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, db_column='school_id', null=True, blank=True)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, db_column='professor_id', null=True, blank=True)
    course_code = models.CharField(max_length=255, null=True, blank=True)
    course_name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    day_of_week = models.CharField(max_length=255, null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return self.course_name or self.course_code or f"Course {self.course_id}"

class StudentCourse(models.Model):
    student_course_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, db_column='student_id', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, db_column='course_id', null=True, blank=True)
