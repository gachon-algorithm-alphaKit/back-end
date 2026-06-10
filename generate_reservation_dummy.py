import os
import django
from datetime import timedelta
from django.utils import timezone
import random

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models.rooms import StudyRoom, Reservation
from core.models.users import Student

def generate():
    Reservation.objects.all().delete()
    print("Deleted old reservations.")

    students = list(Student.objects.all()[:50])
    if not students:
        print("No students found.")
        return

    rooms = list(StudyRoom.objects.all())
    if not rooms:
        print("No rooms found.")
        return

    current_tz = timezone.get_current_timezone()
    now = timezone.now().astimezone(current_tz)
    # Start of today
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    print(f"Generating dummy reservations based on today: {today.date()}")

    reservations_to_create = []

    for day_offset in range(3):  # Today, tomorrow, day after
        current_day = today + timedelta(days=day_offset)
        
        for room in rooms:
            # We want to create heavy bookings so backtracking is triggered.
            # To ensure there are gaps for combination, we book randomly.
            
            hours = list(range(8, 22))
            num_blocks = random.randint(2, 4)
            blocks_start = random.sample(hours[:-2], num_blocks)
            blocks_start.sort()

            for start_h in blocks_start:
                duration = random.randint(1, 3)
                end_h = min(22, start_h + duration)
                
                start_time = current_day.replace(hour=start_h)
                end_time = current_day.replace(hour=end_h)

                # avoid overlapping in the generated list
                conflict = False
                for r in reservations_to_create:
                    if r.room_id == room.room_id and r.start_time < end_time and r.end_time > start_time:
                        conflict = True
                        break
                
                if not conflict:
                    reservations_to_create.append(
                        Reservation(
                            student=random.choice(students),
                            room=room,
                            start_time=start_time,
                            end_time=end_time,
                            head_count=random.randint(1, room.capacity if room.capacity else 4),
                            status="CONFIRMED"
                        )
                    )

    Reservation.objects.bulk_create(reservations_to_create)
    print(f"Created {len(reservations_to_create)} dummy reservations successfully.")

if __name__ == "__main__":
    generate()
