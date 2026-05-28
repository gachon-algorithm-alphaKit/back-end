from django.urls import path
from .api.login import student_login
from .api.auth import student_info
from .api.courses import get_courses
from .api.wishlist import wishlist_toggle, wishlist_list, wishlist_remove
from .api.campus import get_campus_graph
from .api.scholarships import get_scholarships
from .api.rooms import recommend_study_rooms, create_reservation, get_my_reservations, cancel_reservation

urlpatterns = [
    path('students/login', student_login, name='student_login'),
    path('students/info', student_info, name='student_info'),
    path('courses/', get_courses, name='get_courses'),
    path('wishlist/', wishlist_list, name='wishlist_list'),
    path('wishlist/toggle/', wishlist_toggle, name='wishlist_toggle'),
    path('wishlist/remove/<int:course_id>/', wishlist_remove, name='wishlist_remove'),
    path('campus/graph/', get_campus_graph, name='campus_graph'),
    path('scholarships/', get_scholarships, name='get_scholarships'),
    path('rooms/recommend/', recommend_study_rooms, name='recommend_study_rooms'),
    path('rooms/reserve/', create_reservation, name='create_reservation'),
    path('rooms/reservations/', get_my_reservations, name='get_my_reservations'),
    path('rooms/reservations/<int:reservation_id>/', cancel_reservation, name='cancel_reservation'),
]
