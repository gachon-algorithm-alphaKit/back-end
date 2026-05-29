from django.db import models
from .campus import School
from .users import Student

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
    status = models.BooleanField(default=False) # False: 보관중, True: 주인 찾음
    create_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title or f"LostItemPost {self.item_id}"

class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    lost_item = models.ForeignKey(LostItemPost, on_delete=models.CASCADE, db_column='lost_item_id', null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, db_column='student_id', null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    is_anonymous = models.BooleanField(default=True)
    create_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment {self.comment_id} on {self.lost_item_id}"

