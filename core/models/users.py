from django.db import models
from .campus import School

class Student(models.Model):
    student_id = models.IntegerField(primary_key=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, db_column='school_id', null=True, blank=True)
    login_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    password_hash = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    major = models.TextField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    income_bracket = models.IntegerField(null=True, blank=True)
    profile_img = models.ImageField(upload_to='profiles/', null=True, blank=True)

    def __str__(self):
        return self.name or self.login_id or f"Student {self.student_id}"

class Professor(models.Model):
    professor_id = models.AutoField(primary_key=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, db_column='school_id', null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name or f"Professor {self.professor_id}"
