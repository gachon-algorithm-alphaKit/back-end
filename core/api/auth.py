import logging
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth.hashers import make_password
from core.models import Student
from .login import get_tokens_for_user

logger = logging.getLogger(__name__)

@api_view(['POST', 'PUT', 'GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def student_info(request):
    if request.method in ['PUT', 'GET']:
        logger.info(f"=== [API CALL] {request.method} /students/info ===")
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({"status": "error", "message": "인증 토큰이 제공되지 않았습니다."}, status=401)
        
        token_str = auth_header.split(' ')[1]
        try:
            token = AccessToken(token_str)
            student_id = token['student_id']
            student = Student.objects.get(student_id=student_id)
        except (TokenError, InvalidToken):
            return Response({"status": "error", "message": "유효하지 않은 토큰입니다."}, status=401)
        except Student.DoesNotExist:
            return Response({"status": "error", "message": "학생 정보를 찾을 수 없습니다."}, status=404)
        
        if request.method == 'GET':
            return Response({
                "status": "success",
                "message": "학생 정보를 성공적으로 불러왔습니다.",
                "data": {
                    "name": student.name,
                    "studentId": student.student_id,
                    "year": student.year,
                    "major": student.major,
                    "gpa": float(student.gpa) if student.gpa else None,
                    "income_bracket": student.income_bracket,
                    "profile_img": student.profile_img.url if student.profile_img else ""
                }
            })
        
        # PUT method logic continues here
        data = request.data
        if 'name' in data:
            student.name = data['name']
        if 'year' in data:
            student.year = int(data['year']) if data['year'] else None
        if 'gpa' in data:
            student.gpa = float(data['gpa']) if data['gpa'] else None
        if 'income_bracket' in data:
            student.income_bracket = int(data['income_bracket']) if data['income_bracket'] else None
        
        if 'profile_img' in request.FILES:
            student.profile_img = request.FILES['profile_img']

        student.save()
        logger.info(f"Student profile updated for student_id: {student_id}")

        return Response({
            "status": "success",
            "message": "회원 정보가 성공적으로 수정되었습니다.",
            "data": {
                "name": student.name,
                "studentId": student.student_id,
                "year": student.year,
                "gpa": float(student.gpa) if student.gpa else None,
                "income_bracket": student.income_bracket,
                "profile_img": student.profile_img.url if student.profile_img else ""
            }
        })

    logger.info("=== [API CALL] POST /students/info ===")
    data = request.data
    login_id = data.get('login_id')
    
    logger.debug(f"Registration request for login_id: {login_id}")

    if not login_id:
        logger.warning("Missing login_id in registration request.")
        return Response({
            "status": "error",
            "error_code": "REQ_001",
            "message": "잘못된 요청 형식입니다. 필수 항목을 모두 입력해주세요.",
            "data": None
        }, status=400)
    
    if Student.objects.filter(login_id=login_id).exists():
        logger.warning(f"Registration failed: login_id {login_id} already exists.")
        return Response({
            "status": "error",
            "error_code": "AUTH_002",
            "message": "이미 사용 중인 로그인 아이디입니다.",
            "data": None
        }, status=400)

    try:
        student = Student.objects.create(
            student_id=data.get('student_id'),
            school_id=data.get('school_id'),
            login_id=login_id,
            password_hash=make_password(data.get('password')),
            name=data.get('name'),
            major=data.get('major'),
            year=data.get('grade'),
            gpa=data.get('gpa') if data.get('gpa') else None,
            income_bracket=data.get('income_bracket') if data.get('income_bracket') else None,
            profile_img=request.FILES.get('profile_img')
        )
        logger.info(f"Successfully created new student record for {login_id} in DB.")
    except Exception as e:
        logger.error(f"Error creating student record for {login_id}: {str(e)}")
        return Response({
            "status": "error",
            "error_code": "DB_001",
            "message": "학생 정보 저장 중 오류가 발생했습니다.",
            "data": None
        }, status=500)

    tokens = get_tokens_for_user(student)
    logger.info(f"Generated JWT tokens for newly registered student: {login_id}")

    return Response({
        "status": "success",
        "message": "회원가입 및 로그인에 성공했습니다.",
        "data": {
            "student_id": student.student_id,
            "school_id": student.school_id,
            "login_id": student.login_id,
            "major": student.major,
            "name": student.name,
            "access_token": tokens['access_token'],
            "refresh_token": tokens['refresh_token']
        }
    })
