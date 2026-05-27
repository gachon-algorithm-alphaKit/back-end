from django.urls import path
from .api.login import student_login
from .api.auth import student_info

urlpatterns = [
    path('students/login', student_login, name='student_login'),
    path('students/info', student_info, name='student_info'),
]
