import os
import django
from django.utils import timezone
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models.campus import School
from core.models.users import Student
from core.models.rooms import StudyRoom, Reservation

def create_dummy_data():
    print("Creating dummy data for backtracking test on school_id=1...")
    
    school = School.objects.get(school_id=1)
    
    # Dummy students
    student1, _ = Student.objects.get_or_create(
        student_id=9999991, 
        defaults={'school': school, 'name': 'Dummy Student 1', 'login_id': 'dummy1'}
    )
    student2, _ = Student.objects.get_or_create(
        student_id=9999992, 
        defaults={'school': school, 'name': 'Dummy Student 2', 'login_id': 'dummy2'}
    )
    
    # Target date: 2026-06-04
    current_tz = timezone.get_current_timezone()
    target_date = datetime(2026, 6, 4).date()
    base_time = timezone.make_aware(datetime.combine(target_date, datetime.min.time()), current_tz)
    
    time_10 = base_time + timedelta(hours=10)
    time_11 = base_time + timedelta(hours=11)
    time_12 = base_time + timedelta(hours=12)
    time_13 = base_time + timedelta(hours=13)
    
    print(f"Target test time: {time_10} to {time_13}")
    
    all_rooms = list(StudyRoom.objects.filter(place__school_id=1))
    print(f"Found {len(all_rooms)} rooms in school_id=1.")
    
    # Clear existing reservations for the target date to avoid conflicts
    Reservation.objects.filter(
        room__in=all_rooms,
        start_time__gte=base_time,
        end_time__lte=base_time + timedelta(days=1)
    ).delete()
    
    # We will divide the rooms into 3 groups
    # Group 1: Available 10-11, Booked 11-13
    # Group 2: Available 11-12, Booked 10-11, 12-13
    # Group 3: Available 12-13, Booked 10-12
    
    for i, room in enumerate(all_rooms):
        group = i % 3
        
        if group == 0:
            # Group 1: Booked 11-13
            Reservation.objects.create(
                room=room, student=student1, start_time=time_11, end_time=time_13, head_count=1, status="CONFIRMED"
            )
        elif group == 1:
            # Group 2: Booked 10-11 and 12-13
            Reservation.objects.create(
                room=room, student=student1, start_time=time_10, end_time=time_11, head_count=1, status="CONFIRMED"
            )
            Reservation.objects.create(
                room=room, student=student2, start_time=time_12, end_time=time_13, head_count=1, status="CONFIRMED"
            )
        else:
            # Group 3: Booked 10-12
            Reservation.objects.create(
                room=room, student=student2, start_time=time_10, end_time=time_12, head_count=1, status="CONFIRMED"
            )

    print("Successfully set up reservations for ALL rooms in school_id=1.")
    print("Now NO single room is available from 10:00 to 13:00, forcing the backtracking algorithm.")

if __name__ == '__main__':
    create_dummy_data()
