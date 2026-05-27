from django.db import models
from .campus import School
from .users import Student

class Scholarship(models.Model):
    scholarship_id = models.AutoField(primary_key=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, db_column='school_id', null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    dead_line = models.DateTimeField(null=True, blank=True)
    amount = models.CharField(max_length=255, null=True, blank=True)
    required_gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    required_income_bracket = models.IntegerField(null=True, blank=True)
    duplicate_allowed = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return self.name or f"Scholarship {self.scholarship_id}"

class ScholarshipHistory(models.Model):
    history_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, db_column='student_id', null=True, blank=True)
    scholarship = models.ForeignKey(Scholarship, on_delete=models.CASCADE, db_column='scholarship_id', null=True, blank=True)
    semester = models.CharField(max_length=255, null=True, blank=True)
