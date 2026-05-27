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

class LostItemPost(models.Model):
    item_id = models.AutoField(primary_key=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, db_column='school_id', null=True, blank=True)
    place = models.TextField(null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, db_column='student_id', null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    is_anonymous = models.BooleanField(default=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    lost_item_img = models.ImageField(upload_to='lost_items/', null=True, blank=True)
    create_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title or f"LostItemPost {self.item_id}"

class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    lost_item = models.ForeignKey(LostItemPost, on_delete=models.CASCADE, db_column='lost_item_id', null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, db_column='student_id', null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
