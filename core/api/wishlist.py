import logging
import math
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from core.models import Student, StudentCourse, Course

logger = logging.getLogger(__name__)


def _authenticate(request):
    """공통 토큰 인증 헬퍼. 성공 시 Student 객체, 실패 시 Response 반환."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({"status": "error", "message": "인증 토큰이 제공되지 않았습니다."}, status=401)

    token_str = auth_header.split(' ')[1]
    try:
        token = AccessToken(token_str)
        student_id = token['student_id']
        student = Student.objects.get(student_id=student_id)
        return student
    except (TokenError, InvalidToken):
        return Response({"status": "error", "message": "유효하지 않은 토큰입니다."}, status=401)
    except Student.DoesNotExist:
        return Response({"status": "error", "message": "학생 정보를 찾을 수 없습니다."}, status=404)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def wishlist_toggle(request):
    """찜 토글: 이미 있으면 삭제, 없으면 추가"""
    logger.info("=== [API CALL] POST /api/wishlist/toggle/ ===")

    result = _authenticate(request)
    if isinstance(result, Response):
        return result
    student = result

    course_id = request.data.get('course_id')
    if not course_id:
        return Response({"status": "error", "message": "course_id가 필요합니다."}, status=400)

    try:
        course = Course.objects.get(course_id=course_id)
    except Course.DoesNotExist:
        return Response({"status": "error", "message": "해당 강의를 찾을 수 없습니다."}, status=404)

    try:
        with transaction.atomic():
            existing = StudentCourse.objects.filter(student=student, course=course).first()
            if existing:
                existing.delete()
                logger.info(f"Student {student.student_id} removed course {course_id} from wishlist.")
                return Response({
                    "status": "success",
                    "message": "장바구니에서 삭제했습니다.",
                    "data": {"course_id": course_id, "action": "removed"}
                })
            else:
                sc = StudentCourse.objects.create(student=student, course=course)
                logger.info(f"Student {student.student_id} added course {course_id} to wishlist.")
                return Response({
                    "status": "success",
                    "message": "강의를 장바구니에 담았습니다.",
                    "data": {
                        "wishlist_id": sc.student_course_id,
                        "course_id": course_id,
                        "action": "added",
                        "created_at": sc.pk,
                    }
                })
    except Exception as e:
        logger.error(f"Wishlist toggle error: {str(e)}")
        return Response({"status": "error", "message": "장바구니 처리 중 오류가 발생했습니다."}, status=500)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def wishlist_list(request):
    """찜 목록 조회 (페이지네이션)"""
    logger.info("=== [API CALL] GET /api/wishlist/ ===")

    result = _authenticate(request)
    if isinstance(result, Response):
        return result
    student = result

    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1
    try:
        limit = int(request.GET.get('limit', 20))
    except ValueError:
        limit = 20

    qs = StudentCourse.objects.filter(student=student).select_related('course', 'course__professor')
    total_items = qs.count()
    total_pages = math.ceil(total_items / limit) if limit > 0 else 1

    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    items = qs[start_idx:end_idx]

    data = []
    for sc in items:
        c = sc.course
        if not c:
            continue
        try:
            data.append({
                "wishlist_id": sc.student_course_id,
                "course_id": c.course_id,
                "course_code": c.course_code or '',
                "course_name": c.course_name or '',
                "professor_name": c.professor.name if c.professor else '',
                "major_term": '',
                "day_of_week": c.day_of_week or '',
                "start_time": c.start_time.strftime('%H:%M:%S') if c.start_time else '',
                "end_time": c.end_time.strftime('%H:%M:%S') if c.end_time else '',
                "description": c.description or '',
            })
        except Exception as e:
            logger.warning(f"Skipping wishlist item {sc.student_course_id}: {e}")
            continue

    return Response({
        "status": "success",
        "message": "내가 찜한 강의 목록을 성공적으로 불러왔습니다.",
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total_items": total_items,
        },
        "data": data
    })


@api_view(['DELETE'])
@authentication_classes([])
@permission_classes([AllowAny])
def wishlist_remove(request, course_id):
    """찜 목록에서 특정 강의 삭제"""
    logger.info(f"=== [API CALL] DELETE /api/wishlist/remove/{course_id}/ ===")

    result = _authenticate(request)
    if isinstance(result, Response):
        return result
    student = result

    try:
        sc = StudentCourse.objects.get(student=student, course_id=course_id)
        sc.delete()
        logger.info(f"Student {student.student_id} removed course {course_id} from wishlist.")
        return Response({
            "status": "success",
            "message": "장바구니에서 강의를 성공적으로 삭제했습니다."
        })
    except StudentCourse.DoesNotExist:
        return Response({
            "status": "error",
            "message": "장바구니에 해당 강의가 존재하지 않습니다."
        }, status=404)
    except Exception as e:
        logger.error(f"Wishlist remove error: {str(e)}")
        return Response({"status": "error", "message": "삭제 중 오류가 발생했습니다."}, status=500)
