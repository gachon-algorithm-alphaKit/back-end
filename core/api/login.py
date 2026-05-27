import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
import requests
from core.models import Student

logger = logging.getLogger(__name__)

def get_tokens_for_user(student):
    refresh = RefreshToken()
    refresh['student_id'] = student.student_id
    refresh['login_id'] = student.login_id
    
    return {
        'refresh_token': str(refresh),
        'access_token': str(refresh.access_token),
    }

@api_view(['POST'])
@permission_classes([AllowAny])
def student_login(request):
    logger.info("=== [API CALL] POST /students/login ===")
    username = request.data.get('username')
    password = request.data.get('password')
    school_id = request.data.get('school_id')

    logger.debug(f"Request Data: username={username}, school_id={school_id}, password={'***' if password else 'None'}")

    if not username or not password:
        logger.warning("Missing username or password in request.")
        return Response({
            "status": "error",
            "error_code": "REQ_001",
            "message": "잘못된 요청 형식입니다. 필수 항목을 모두 입력해주세요.",
            "data": None
        }, status=400)

    login_url = "https://cyber.gachon.ac.kr/login/index.php"
    payload = {
        "username": username,
        "password": password
    }
    
    try:
        logger.info(f"Sending login request to e-Campus: {login_url}")
        response = requests.post(login_url, data=payload, timeout=5)
        html_content = response.text
        logger.debug(f"e-Campus Response Status Code: {response.status_code}")
    except Exception as e:
        logger.error(f"e-Campus connection error: {str(e)}")
        return Response({
            "status": "error",
            "error_code": "AUTH_004",
            "message": "e-Campus 서버와 통신할 수 없습니다.",
            "data": None
        }, status=500)

    if "아이디 또는 패스워드가 잘못 입력되었습니다." in html_content:
        logger.warning(f"e-Campus login failed for username: {username} (Invalid credentials)")
        return Response({
            "status": "error",
            "error_code": "AUTH_001",
            "message": "아이디 또는 비밀번호가 일치하지 않습니다.",
            "data": None
        }, status=401)
    
    elif "강좌 전체보기" in html_content:
        logger.info(f"e-Campus login successful for username: {username}")
        try:
            student = Student.objects.get(login_id=username)
            logger.debug(f"Existing student found in DB: ID {student.student_id}")
            tokens = get_tokens_for_user(student)
            logger.info("Generated JWT tokens for returning student.")
            return Response({
                "status": "success",
                "message": "로그인에 성공했습니다.",
                "data": {
                    "studentId": student.student_id,
                    "school_id": student.school_id,
                    "login_id": student.login_id,
                    "major": student.major,
                    "name": student.name,
                    "year": student.year,
                    "gpa": float(student.gpa) if student.gpa else None,
                    "income_bracket": student.income_bracket,
                    "profile_img": student.profile_img.url if student.profile_img else "",
                    "access_token": tokens['access_token'],
                    "refresh_token": tokens['refresh_token']
                }
            })
        except Student.DoesNotExist:
            logger.info(f"Student {username} not found in DB. Prompting for first-time login/registration.")
            return Response({
                "status": "success",
                "message": "첫 로그인 입니다.",
                "data": None
            })
    else:
        logger.error(f"Unknown e-Campus response for username: {username}")
        return Response({
            "status": "error",
            "error_code": "AUTH_005",
            "message": "인증 결과를 확인할 수 없습니다. (알 수 없는 응답)",
            "data": None
        }, status=500)
