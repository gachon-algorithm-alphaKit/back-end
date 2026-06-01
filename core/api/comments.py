import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.models.community import Comment, LostItemPost
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

def get_student_id_from_token(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    try:
        token = AccessToken(auth_header.split(' ')[1])
        return int(token['student_id'])
    except (TokenError, InvalidToken, ValueError, TypeError):
        return None


def format_comment(comment, current_student_id, post_owner_id):
    """댓글 데이터를 API 응답 형식으로 변환합니다."""
    # 익명 마스킹: is_anonymous가 true이면 실제 이름을 절대 노출하지 않음
    if comment.is_anonymous:
        writer = "익명"
    else:
        writer = comment.student.name if comment.student else "알 수 없음"

    return {
        "comment_id": comment.comment_id,
        "writer": writer,
        "is_writer": bool(current_student_id and comment.student_id and int(comment.student_id) == int(current_student_id)),
        "is_post_owner": bool(post_owner_id and comment.student_id and int(comment.student_id) == int(post_owner_id)),
        "comment": comment.comment,
        "is_anonymous": comment.is_anonymous,
        "create_time": comment.create_time.isoformat() if comment.create_time else "",
    }


@csrf_exempt
def handle_comments(request, item_id):
    """GET: 댓글 목록 조회 / POST: 댓글 작성"""

    current_student_id = get_student_id_from_token(request)
    if not current_student_id:
        return JsonResponse({"status": "error", "message": "유효하지 않은 인증 토큰입니다."}, status=401)

    # 해당 게시글 존재 여부 확인
    try:
        post = LostItemPost.objects.get(item_id=item_id)
    except LostItemPost.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "게시글을 찾을 수 없습니다."},
            status=404,
        )

    post_owner_id = post.student_id

    # ── GET: 댓글 목록 조회 ──────────────────────────────────
    if request.method == "GET":
        try:
            comments = Comment.objects.filter(lost_item_id=item_id).order_by("create_time")
            data = [format_comment(c, current_student_id, post_owner_id) for c in comments]

            return JsonResponse(
                {"status": "success", "data": data},
                json_dumps_params={"ensure_ascii": False},
                status=200,
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse(
                {"status": "error", "message": f"서버 내부 오류: {str(e)}"},
                status=500,
            )

    # ── POST: 댓글 작성 ──────────────────────────────────────
    elif request.method == "POST":
        try:
            body = json.loads(request.body)
            comment_text = body.get("comment", "").strip()
            is_anonymous = body.get("is_anonymous", True)

            if not comment_text:
                return JsonResponse(
                    {"status": "error", "message": "댓글 내용을 입력해주세요."},
                    status=400,
                )

            new_comment = Comment.objects.create(
                lost_item_id=item_id,
                student_id=current_student_id,
                comment=comment_text,
                is_anonymous=is_anonymous,
            )

            return JsonResponse(
                {
                    "status": "success",
                    "data": format_comment(new_comment, current_student_id, post_owner_id)
                },
                json_dumps_params={"ensure_ascii": False},
                status=201,
            )
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "잘못된 JSON 형식입니다."},
                status=400,
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse(
                {"status": "error", "message": f"서버 내부 오류: {str(e)}"},
                status=500,
            )

    return JsonResponse(
        {"status": "error", "message": "GET 또는 POST 메서드만 허용됩니다."},
        status=405,
    )


@csrf_exempt
def manage_comment(request, comment_id):
    """PUT: 댓글 수정 / DELETE: 댓글 삭제"""

    current_student_id = get_student_id_from_token(request)
    if not current_student_id:
        return JsonResponse({"status": "error", "message": "유효하지 않은 인증 토큰입니다."}, status=401)

    try:
        comment = Comment.objects.get(comment_id=comment_id)
    except Comment.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "댓글을 찾을 수 없습니다."},
            status=404,
        )

    # 권한 검증: 댓글 작성자만 수정/삭제 가능
    if comment.student_id != current_student_id:
        return JsonResponse(
            {"status": "error", "message": "권한이 없습니다."},
            status=403,
        )

    # ── PUT: 댓글 수정 ───────────────────────────────────────
    if request.method == "PUT":
        try:
            body = json.loads(request.body)
            comment_text = body.get("comment", "").strip()

            if not comment_text:
                return JsonResponse(
                    {"status": "error", "message": "댓글 내용을 입력해주세요."},
                    status=400,
                )

            comment.comment = comment_text
            comment.save()

            return JsonResponse(
                {
                    "status": "success",
                    "message": "댓글이 수정되었습니다.",
                    "data": {
                        "comment_id": comment.comment_id,
                        "comment": comment.comment,
                        "update_time": comment.create_time.isoformat() if comment.create_time else "",
                    },
                },
                json_dumps_params={"ensure_ascii": False},
                status=200,
            )
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "잘못된 JSON 형식입니다."},
                status=400,
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse(
                {"status": "error", "message": f"서버 내부 오류: {str(e)}"},
                status=500,
            )

    # ── DELETE: 댓글 삭제 ────────────────────────────────────
    elif request.method == "DELETE":
        try:
            comment.delete()
            return JsonResponse(
                {"status": "success", "message": "댓글이 삭제되었습니다."},
                json_dumps_params={"ensure_ascii": False},
                status=200,
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse(
                {"status": "error", "message": f"서버 내부 오류: {str(e)}"},
                status=500,
            )

    return JsonResponse(
        {"status": "error", "message": "PUT 또는 DELETE 메서드만 허용됩니다."},
        status=405,
    )
