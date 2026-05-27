from django.contrib import admin
from .models import (
    School, Place, Student, Professor, Course, StudentCourse, StudyRoom,
    Reservation, Scholarship, ScholarshipHistory, LostItemPost, Comment
)

admin.site.register(School)
admin.site.register(Place)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'login_id', 'name', 'school')
    readonly_fields = ('student_id',)

admin.site.register(Student, StudentAdmin)
admin.site.register(Professor)
admin.site.register(Course)
admin.site.register(StudentCourse)
admin.site.register(StudyRoom)
admin.site.register(Reservation)
admin.site.register(Scholarship)
admin.site.register(ScholarshipHistory)
admin.site.register(LostItemPost)
admin.site.register(Comment)
