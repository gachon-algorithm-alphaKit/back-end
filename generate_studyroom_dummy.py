import os
import sys
import django
import random
from datetime import datetime, time

sys.path.append('d:/project/AlphaKit/back-end')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from core.models import StudyRoom, Reservation, Student

def main():
    today = timezone.localtime().date()
    
    # 1. 예약에 사용할 임의의 학생들 풀 준비
    students = list(Student.objects.all())
    if not students:
        print("학생 데이터가 없습니다. 먼저 학생 데이터를 생성해주세요.")
        return
    
    print(f"[{today}] 스터디룸 공실 조합 테스트용 대량 더미 데이터를 생성합니다...")
    
    # 테스터의 검색 조건에 맞는 시설 목록
    all_facilities = 'TV, 화이트보드, HDMI, 빔프로젝터'
    
    # 2. 모든 방을 대상으로 세팅 (일부 방이 완전히 비어있으면 조합 로직이 안 탈 수 있음)
    rooms = list(StudyRoom.objects.all())
    if len(rooms) < 10:
        for i in range(10 - len(rooms)):
            StudyRoom.objects.create(name=f"Test Room {len(rooms) + i + 1}", capacity=6, facilities=all_facilities)
        rooms = list(StudyRoom.objects.all())
        
    for room in rooms:
        # 모든 방의 수용인원을 6 이상으로 맞추어, 5명 검색 시 무조건 필터링되게 만듦
        if room.capacity is None or room.capacity < 6:
            room.capacity = 6
        room.facilities = all_facilities
        room.save()
        
    # 3. 오늘 자 기존 예약 전체 초기화
    today_start = timezone.make_aware(datetime.combine(today, time.min))
    today_end = timezone.make_aware(datetime.combine(today, time.max))
    Reservation.objects.filter(start_time__gte=today_start, start_time__lte=today_end).delete()
    
    def create_reservation(room, start_hour, end_hour):
        start_time = timezone.make_aware(datetime.combine(today, time(start_hour, 0)))
        end_time = timezone.make_aware(datetime.combine(today, time(end_hour, 0)))
        random_student = random.choice(students)
        Reservation.objects.create(
            room=room,
            student=random_student,
            start_time=start_time,
            end_time=end_time,
            head_count=random.randint(2, 5),
            reservation_group_id=f"dummy_{room.room_id}_{start_hour}_{random.randint(100,999)}",
            status='RESERVED'
        )

    # 4. 공실 조합이 자연스럽게 발생하도록 모든 방마다 10~14시 사이에 부분적으로 예약을 꽉 채움
    # 어느 한 방도 10~14시 전체가 통으로 비어있지 않게 해서 '조합'을 강제함
    patterns = [
        [(10, 12)],           # 12~14시 빈방
        [(12, 14)],           # 10~12시 빈방
        [(11, 13)],           # 10~11시, 13~14시 빈방
        [(10, 11), (13, 14)], # 11~13시 빈방
        [(10, 13)],           # 13~14시 빈방
        [(11, 14)],           # 10~11시 빈방
        [(10, 12), (13, 14)]  # 12~13시 빈방
    ]
    
    print(f"총 {len(rooms)}개의 방에 대해 예약을 세팅합니다.")
    for room in rooms:
        pattern = random.choice(patterns)
        for (start, end) in pattern:
            create_reservation(room, start, end)
    
    print("\n-> 더미 데이터 생성 완료!")
    print("\n사용법:")
    print("python generate_studyroom_dummy.py")
    print("모든 방에 대해 10~14시 사이 부분 예약이 꽉 찼으므로, 이제 공실 조합 화면이 무조건 노출됩니다.")

if __name__ == '__main__':
    main()
