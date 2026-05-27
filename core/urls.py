from django.urls import path
from .api.login import student_login
from .api.auth import student_info
from .api.courses import get_courses
from .api.wishlist import wishlist_toggle, wishlist_list, wishlist_remove
from .api.campus import get_campus_graph

urlpatterns = [
    path('students/login', student_login, name='student_login'),
    path('students/info', student_info, name='student_info'),
    path('courses/', get_courses, name='get_courses'),
    path('wishlist/', wishlist_list, name='wishlist_list'),
    path('wishlist/toggle/', wishlist_toggle, name='wishlist_toggle'),
    path('wishlist/remove/<int:course_id>/', wishlist_remove, name='wishlist_remove'),
    path('campus/graph/', get_campus_graph, name='campus_graph'),
]
