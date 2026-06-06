import json
import uuid
from datetime import datetime
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Q
from core.models.rooms import StudyRoom, Reservation
import random

@csrf_exempt
def recommend_study_rooms(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST 메서드만 허용됩니다."}, status=405)

    try:
        body = json.loads(request.body)
        school_id = body.get("school_id", 1)
        head_count = body.get("head_count", 1)
        start_time_str = body.get("start_time")
        end_time_str = body.get("end_time")
        requested_facilities = set(body.get("facilities", []))
        page = int(body.get("page", 1))
        limit = int(body.get("limit", 10))

        # 현재 유저 확인 (JWT)
        current_student_id = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            from rest_framework_simplejwt.tokens import AccessToken
            try:
                token = AccessToken(auth_header.split(' ')[1])
                current_student_id = int(token['student_id'])
            except Exception:
                pass

        # Timezone 처리: KST -> UTC (또는 Aware Datetime)
        # 프론트엔드에서 넘어오는 start_time, end_time 포맷 파싱 (예: "2026-05-28T10:00:00")
        try:
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)
        except (ValueError, TypeError):
            return JsonResponse({"status": "error", "message": "잘못된 시간 형식입니다."}, status=400)

        if timezone.is_naive(start_time):
            # KST라고 가정하고 Aware로 변환한 뒤 처리 (프론트에서 넘어온 시간이 Naive인 경우)
            current_tz = timezone.get_current_timezone()
            start_time = timezone.make_aware(start_time, current_tz)
            end_time = timezone.make_aware(end_time, current_tz)

        # 1. 겹치는 예약이 있는 방 ID 찾기 및 14시간 슬롯 생성
        target_date = start_time.date()
        date_start = timezone.make_aware(datetime.combine(target_date, datetime.min.time()), current_tz)
        date_end = date_start + timezone.timedelta(days=1)
        
        daily_reservations = Reservation.objects.filter(
            start_time__lt=date_end,
            end_time__gt=date_start
        )
        
        overlapping_room_ids = set()
        my_overlapping_room_ids = set()
        room_bookings = {}
        
        for res in daily_reservations:
            # Overlapping logic
            if res.start_time < end_time and res.end_time > start_time:
                overlapping_room_ids.add(res.room_id)
                if current_student_id and res.student_id == current_student_id:
                    my_overlapping_room_ids.add(res.room_id)
            
            # Timeline slot logic (08:00 ~ 22:00)
            if res.room_id not in room_bookings:
                room_bookings[res.room_id] = [False] * 14
                
            res_start_hour = res.start_time.astimezone(current_tz).hour
            res_end_hour = res.end_time.astimezone(current_tz).hour
            
            # Handle end_time spanning past midnight or exactly at top of hour
            if res.end_time.astimezone(current_tz).minute == 0 and res.end_time.astimezone(current_tz).hour != res_start_hour:
                pass # end hour is fine
                
            res_start_hour = max(8, res_start_hour)
            res_end_hour = min(22, res_end_hour)
            
            for h in range(res_start_hour, res_end_hour):
                if 8 <= h < 22:
                    room_bookings[res.room_id][h - 8] = True

        # 2. 방 필터링 (학교 일치, 수용인원 충족) - 겹치는 예약 제외하지 않음 (UI 비활성화 목적)
        all_rooms = StudyRoom.objects.select_related('place').filter(
            place__school_id=school_id,
            capacity__gte=head_count
        )

        recommendations = []

        # Check if the user has ANY overlapping reservation
        user_has_overlap = len(my_overlapping_room_ids) > 0

        # 3. 필터링된 방에 대한 Scoring 계산
        for room in all_rooms:
            room_is_booked = room.room_id in overlapping_room_ids
            is_available = (not room_is_booked) and (not user_has_overlap)
            is_my_reservation = room.room_id in my_overlapping_room_ids
            booked_slots = room_bookings.get(room.room_id, [False] * 14)
            # 시설 문자열을 리스트로 파싱 (예: "TV,화이트보드" -> ["TV", "화이트보드"])
            facilities_list = [f.strip() for f in room.facilities.split(',')] if room.facilities else []
            room_facilities = set(facilities_list)
            
            matched = list(requested_facilities.intersection(room_facilities))
            facility_score = len(matched) * 30 
            
            # 수용 인원 낭비 최소화 점수
            wasted_space = room.capacity - head_count
            capacity_score = max(100 - (wasted_space * 10), 0)
            
            total_score = capacity_score + facility_score

            recommendations.append({
                "room_id": room.room_id,
                "name": room.name,
                "capacity": room.capacity,
                "score": total_score,
                "matched_facilities": matched,
                # 프론트엔드 연동을 위한 추가 정보
                "place_id": room.place_id,
                "place_name": room.place.name if room.place else "위치 미정",
                "facilities": facilities_list,
                "is_available": is_available,
                "is_my_reservation": is_my_reservation,
                "booked_slots": booked_slots
            })

        # 1차 정렬: 추천 여부 (is_available), 2차 정렬: 점수 (score)
        recommendations.sort(key=lambda x: (x["is_available"], x["score"]), reverse=True)

        # 순위 부여
        for idx, rec in enumerate(recommendations):
            rec["rank"] = idx + 1

        # 페이지네이션
        total_items = len(recommendations)
        total_pages = max(1, (total_items + limit - 1) // limit)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_recommendations = recommendations[start_idx:end_idx]

        if not any(r["is_available"] for r in recommendations):
            duration_hours = int((end_time - start_time).total_seconds() // 3600)
            if duration_hours >= 2:
                # 1. 각 시간대(slot)별 사용 가능한 방 목록 사전 계산
                slot_valid_rooms = []
                for h in range(duration_hours):
                    slot_start = start_time + timezone.timedelta(hours=h)
                    slot_end = start_time + timezone.timedelta(hours=h+1)
                    valid_for_h = []
                    
                    for room in all_rooms:
                        is_avail = True
                        for res in daily_reservations:
                            if res.start_time < slot_end and res.end_time > slot_start:
                                if res.room_id == room.room_id or (current_student_id and res.student_id == current_student_id):
                                    is_avail = False
                                    break
                                    
                        if is_avail:
                            facilities_list = [f.strip() for f in room.facilities.split(',')] if room.facilities else []
                            matched = list(requested_facilities.intersection(set(facilities_list)))
                            facility_score = len(matched) * 30 
                            wasted_space = room.capacity - head_count
                            capacity_score = max(100 - (wasted_space * 10), 0)
                            score = capacity_score + facility_score
                            
                            valid_for_h.append({
                                "room_id": room.room_id,
                                "name": room.name,
                                "capacity": room.capacity,
                                "score": score,
                                "matched_facilities": matched,
                                "place_id": room.place_id,
                                "place_name": room.place.name if room.place else "위치 미정",
                                "facilities": facilities_list,
                                "start_time": slot_start.isoformat(),
                                "end_time": slot_end.isoformat(),
                                "start_hour": slot_start.astimezone(current_tz).hour,
                                "end_hour": slot_end.astimezone(current_tz).hour
                            })
                            
                    # 탐색 공간 축소를 위해 해당 슬롯에서 점수가 높은 방 상위 5개만 후보로 사용
                    valid_for_h.sort(key=lambda x: x["score"], reverse=True)
                    slot_valid_rooms.append(valid_for_h[:5])
                    
                # 2. 백트래킹(DFS)으로 최적의 조합 찾기
                best_combos = []
                
                def backtrack(hour_idx, current_combo, current_raw_score, room_changes):
                    if hour_idx == duration_hours:
                        # 방 이동 패널티: 1회 변경당 -50점
                        penalty = room_changes * 50
                        final_score = current_raw_score - penalty
                        best_combos.append({
                            "slots": list(current_combo),
                            "total_score": final_score / duration_hours,
                            "raw_score": final_score
                        })
                        return
                        
                    for room_data in slot_valid_rooms[hour_idx]:
                        is_change = 0
                        if current_combo and current_combo[-1]["room_id"] != room_data["room_id"]:
                            is_change = 1
                            
                        current_combo.append(room_data)
                        backtrack(hour_idx + 1, current_combo, current_raw_score + room_data["score"], room_changes + is_change)
                        current_combo.pop()
                        
                # 모든 시간대에 최소 1개 이상의 사용 가능한 방이 있어야 조합 가능
                if all(len(rooms) > 0 for rooms in slot_valid_rooms):
                    backtrack(0, [], 0, 0)
                    
                    # 최종 점수(패널티 적용) 기준으로 내림차순 정렬 후 상위 3개 추출
                    best_combos.sort(key=lambda x: x["raw_score"], reverse=True)
                    top_3_combos = best_combos[:3]
                    
                    for i, combo in enumerate(top_3_combos):
                        combo["combo_id"] = f"combo_{i+1}"
                        del combo["raw_score"]
                        
                        # 슬롯 병합 로직 (연속된 동일 방 병합)
                        merged_slots = []
                        if combo["slots"]:
                            current_slot = combo["slots"][0].copy()
                            for slot in combo["slots"][1:]:
                                if slot["room_id"] == current_slot["room_id"]:
                                    current_slot["end_time"] = slot["end_time"]
                                    current_slot["end_hour"] = slot["end_hour"]
                                else:
                                    merged_slots.append(current_slot)
                                    current_slot = slot.copy()
                            merged_slots.append(current_slot)
                        combo["slots"] = merged_slots
                        
                    return JsonResponse({
                        "status": "success",
                        "data": {
                            "match_type": "COMBINED",
                            "recommendations": top_3_combos,
                            "pagination": {
                                "current_page": 1,
                                "total_pages": 1,
                                "total_items": len(top_3_combos)
                            }
                        }
                    }, json_dumps_params={'ensure_ascii': False}, status=200)

        return JsonResponse({
            "status": "success",
            "data": {
                "match_type": "SINGLE",
                "recommendations": paginated_recommendations,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_items": total_items
                }
            }
        }, json_dumps_params={'ensure_ascii': False}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "올바르지 않은 JSON 형식입니다."}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"서버 내부 오류: {str(e)}"}, status=500)

@csrf_exempt
def create_reservation(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST 메서드만 허용됩니다."}, status=405)

    try:
        # 실제 JWT 토큰 인증 적용
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
        from core.models.users import Student
        
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({"status": "error", "message": "인증 토큰이 제공되지 않았습니다."}, status=401)
            
        token_str = auth_header.split(' ')[1]
        try:
            token = AccessToken(token_str)
            student_id = int(token['student_id'])
            current_student = Student.objects.get(student_id=student_id)
            current_student_id = current_student.student_id
        except (TokenError, InvalidToken):
            return JsonResponse({"status": "error", "message": "유효하지 않은 토큰입니다."}, status=401)
        except Student.DoesNotExist:
            return JsonResponse({"status": "error", "message": "학생 정보를 찾을 수 없습니다."}, status=404)

        body = json.loads(request.body)
        room_id = body.get("room_id")
        start_time_str = body.get("start_time")
        end_time_str = body.get("end_time")
        head_count = body.get("head_count", 1)

        if not all([room_id, start_time_str, end_time_str]):
            return JsonResponse({"status": "error", "message": "room_id, start_time, end_time은 필수 항목입니다."}, status=400)

        current_tz = timezone.get_current_timezone()

        try:
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)
        except (ValueError, TypeError):
            return JsonResponse({"status": "error", "message": "잘못된 시간 형식입니다."}, status=400)

        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time, current_tz)
            end_time = timezone.make_aware(end_time, current_tz)

        # 7일 제한
        now = timezone.now()
        max_date = now + timezone.timedelta(days=7)
        if start_time > max_date:
            return JsonResponse({"status": "error", "message": "최대 일주일 뒤까지만 예약할 수 있습니다."}, status=400)

        with transaction.atomic():
            # Room overlap check
            if Reservation.objects.filter(
                room_id=room_id,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exists():
                return JsonResponse({"status": "error", "message": "선택한 시간대에 이미 예약이 존재합니다."}, status=400)
            
            # User overlap check
            if Reservation.objects.filter(
                student_id=current_student_id,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exists():
                return JsonResponse({"status": "error", "message": "해당 시간대에 이미 다른 스터디룸 예약이 존재합니다."}, status=400)
            
            new_reservation = Reservation.objects.create(
                student_id=current_student_id,
                room_id=room_id,
                start_time=start_time,
                end_time=end_time,
                head_count=head_count,
                status="CONFIRMED"
            )

        return JsonResponse({
            "status": "success",
            "message": "예약이 성공적으로 확정되었습니다.",
            "data": {
                "reservation_id": new_reservation.reservation_id,
            }
        }, json_dumps_params={'ensure_ascii': False}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "올바르지 않은 JSON 형식입니다."}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"서버 내부 오류: {str(e)}"}, status=500)

@csrf_exempt
def create_combo_reservation(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST 메서드만 허용됩니다."}, status=405)

    try:
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
        from core.models.users import Student
        
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({"status": "error", "message": "인증 토큰이 제공되지 않았습니다."}, status=401)
            
        token_str = auth_header.split(' ')[1]
        try:
            token = AccessToken(token_str)
            student_id = int(token['student_id'])
            current_student = Student.objects.get(student_id=student_id)
            current_student_id = current_student.student_id
        except (TokenError, InvalidToken):
            return JsonResponse({"status": "error", "message": "유효하지 않은 토큰입니다."}, status=401)
        except Student.DoesNotExist:
            return JsonResponse({"status": "error", "message": "학생 정보를 찾을 수 없습니다."}, status=404)

        body = json.loads(request.body)
        slots = body.get("slots", [])
        head_count = body.get("head_count", 1)

        if not slots:
            return JsonResponse({"status": "error", "message": "slots 데이터가 필요합니다."}, status=400)

        current_tz = timezone.get_current_timezone()
        now = timezone.now()
        max_date = now + timezone.timedelta(days=7)

        with transaction.atomic():
            new_reservations = []
            group_id = uuid.uuid4().hex
            for slot in slots:
                room_id = slot.get("room_id")
                start_time_str = slot.get("start_time")
                end_time_str = slot.get("end_time")

                if not all([room_id, start_time_str, end_time_str]):
                    raise ValueError("room_id, start_time, end_time은 필수 항목입니다.")

                start_time = timezone.make_aware(datetime.fromisoformat(start_time_str), current_tz) if timezone.is_naive(datetime.fromisoformat(start_time_str)) else datetime.fromisoformat(start_time_str)
                end_time = timezone.make_aware(datetime.fromisoformat(end_time_str), current_tz) if timezone.is_naive(datetime.fromisoformat(end_time_str)) else datetime.fromisoformat(end_time_str)

                if start_time > max_date:
                    raise ValueError("최대 일주일 뒤까지만 예약할 수 있습니다.")

                if Reservation.objects.filter(room_id=room_id, start_time__lt=end_time, end_time__gt=start_time).exists():
                    raise ValueError(f"방 {room_id}의 선택한 시간대에 이미 예약이 존재합니다.")
                
                if Reservation.objects.filter(student_id=current_student_id, start_time__lt=end_time, end_time__gt=start_time).exists():
                    raise ValueError(f"해당 시간대에 이미 다른 스터디룸 예약이 존재합니다.")
                
                res = Reservation.objects.create(
                    student_id=current_student_id,
                    room_id=room_id,
                    start_time=start_time,
                    end_time=end_time,
                    reservation_group_id=group_id,
                    head_count=head_count,
                    status="CONFIRMED"
                )
                new_reservations.append(res)

        return JsonResponse({
            "status": "success",
            "message": "공실 조합 예약이 성공적으로 확정되었습니다.",
            "data": {
                "reservation_ids": [r.reservation_id for r in new_reservations],
            }
        }, json_dumps_params={'ensure_ascii': False}, status=200)

    except ValueError as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "올바르지 않은 JSON 형식입니다."}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"서버 내부 오류: {str(e)}"}, status=500)

@csrf_exempt
def get_my_reservations(request):
    if request.method != "GET":
        return JsonResponse({"status": "error", "message": "GET 메서드만 허용됩니다."}, status=405)

    try:
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
        
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({"status": "error", "message": "인증 토큰이 제공되지 않았습니다."}, status=401)
            
        token_str = auth_header.split(' ')[1]
        try:
            token = AccessToken(token_str)
            student_id = int(token['student_id'])
        except (TokenError, InvalidToken):
            return JsonResponse({"status": "error", "message": "유효하지 않은 토큰입니다."}, status=401)

        reservations = Reservation.objects.filter(student_id=student_id).select_related('room__place').order_by('start_time')
        
        current_tz = timezone.get_current_timezone()
        
        data = []
        for res in reservations:
            location = res.room.place.name if res.room and res.room.place else "위치 미정"
            room_name = res.room.name if res.room else f"Room {res.room_id}"
            
            start = res.start_time.astimezone(current_tz)
            end = res.end_time.astimezone(current_tz)
            
            date_str = start.strftime("%Y.%m.%d")
            
            data.append({
                "id": str(res.reservation_id),
                "roomName": room_name,
                "location": location,
                "date": date_str,
                "startHour": start.hour,
                "endHour": end.hour if end.hour != 0 else 24,
                "reservationGroupId": res.reservation_group_id,
            })
            
        return JsonResponse({
            "status": "success",
            "data": {
                "reservations": data
            }
        }, json_dumps_params={'ensure_ascii': False}, status=200)

    except Exception as e:
        return JsonResponse({"status": "error", "message": f"서버 내부 오류: {str(e)}"}, status=500)

@csrf_exempt
def cancel_reservation(request, reservation_id):
    if request.method != "DELETE":
        return JsonResponse({"status": "error", "message": "DELETE 메서드만 허용됩니다."}, status=405)
    
    try:
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
        
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({"status": "error", "message": "인증 토큰이 제공되지 않았습니다."}, status=401)
            
        token_str = auth_header.split(' ')[1]
        try:
            token = AccessToken(token_str)
            student_id = int(token['student_id'])
        except (TokenError, InvalidToken):
            return JsonResponse({"status": "error", "message": "유효하지 않은 토큰입니다."}, status=401)
            
        try:
            reservation = Reservation.objects.get(reservation_id=reservation_id, student_id=student_id)
            reservation.delete()
            return JsonResponse({"status": "success", "message": "예약이 취소되었습니다."}, status=200)
        except Reservation.DoesNotExist:
            return JsonResponse({"status": "error", "message": "해당 예약을 찾을 수 없거나 권한이 없습니다."}, status=404)
            
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"서버 내부 오류: {str(e)}"}, status=500)
