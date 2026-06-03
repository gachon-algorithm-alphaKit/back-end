"""
밸런스 게임(Topic) API

모든 뷰는 @csrf_exempt + JsonResponse + 수동 JSON 파싱 패턴을 사용합니다.
(기존 core/api/comments.py 패턴과 동일)
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Count, Q, F
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from core.models.topic import Topic, TopicVote, TopicComment, TopicCommentLike
from core.utils.word_filter import check_profanity
from core.utils.rate_limiter import rate_limiter

# ── Loggers ──────────────────────────────────────────────────
vote_logger = logging.getLogger('core.vote')
comment_logger = logging.getLogger('core.topic_comment')
security_logger = logging.getLogger('core.security')


# ── Auth helper ──────────────────────────────────────────────
def get_student_id_from_token(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    try:
        token = AccessToken(auth_header.split(' ')[1])
        return token['student_id']
    except (TokenError, InvalidToken):
        return None


# ── Anonymous numbering helper ───────────────────────────────
def build_anon_map(topic_id):
    """토픽 내 댓글 작성자에게 등장 순서대로 번호를 부여"""
    student_ids = TopicComment.objects.filter(
        topic_id=topic_id
    ).order_by('created_at').values_list('student_id', flat=True)
    anon_map = {}
    counter = 1
    for sid in student_ids:
        if sid not in anon_map:
            anon_map[sid] = counter
            counter += 1
    return anon_map


# ── Topic formatter ──────────────────────────────────────────
def format_topic(topic, student_id=None):
    my_vote = None
    if student_id:
        try:
            vote = TopicVote.objects.get(topic=topic, student_id=student_id)
            my_vote = vote.select_opinion
        except TopicVote.DoesNotExist:
            pass
    return {
        'topic_id': topic.topic_id,
        'title': topic.title,
        'opinion_1': topic.opinion_1,
        'opinion_2': topic.opinion_2,
        'publish_date': str(topic.publish_date),
        'is_active': topic.is_active,
        'total_vote_count': topic.total_vote_count,
        'my_vote': my_vote,
        'created_at': topic.created_at.isoformat() if topic.created_at else '',
    }


# ═══════════════════════════════════════════════════════════════
# 1) GET /api/topics/active/
# ═══════════════════════════════════════════════════════════════
@csrf_exempt
def get_active_topic(request):
    """현재 활성화된 토픽 조회"""
    if request.method != 'GET':
        return JsonResponse(
            {'status': 'error', 'message': 'GET 메서드만 허용됩니다.'},
            status=405, json_dumps_params={'ensure_ascii': False},
        )

    student_id = get_student_id_from_token(request)

    try:
        topic = Topic.objects.filter(is_active=True).first()
        if not topic:
            return JsonResponse(
                {'status': 'error', 'message': '현재 활성화된 토픽이 없습니다.'},
                status=404, json_dumps_params={'ensure_ascii': False},
            )
        return JsonResponse(
            {'status': 'success', 'data': format_topic(topic, student_id)},
            json_dumps_params={'ensure_ascii': False},
        )
    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': f'서버 내부 오류: {str(e)}'},
            status=500, json_dumps_params={'ensure_ascii': False},
        )


# ═══════════════════════════════════════════════════════════════
# 2) GET /api/topics/
# ═══════════════════════════════════════════════════════════════
@csrf_exempt
def get_topic_list(request):
    """토픽 목록 조회 (커서 기반 페이지네이션)"""
    if request.method != 'GET':
        return JsonResponse(
            {'status': 'error', 'message': 'GET 메서드만 허용됩니다.'},
            status=405, json_dumps_params={'ensure_ascii': False},
        )

    student_id = get_student_id_from_token(request)
    cursor = request.GET.get('cursor')

    try:
        topics_data = []

        if not cursor:
            # 첫 페이지: 활성 토픽 먼저, 그 다음 과거 토픽
            active_topic = Topic.objects.filter(is_active=True).first()
            if active_topic:
                topics_data.append(format_topic(active_topic, student_id))

            past_topics = Topic.objects.filter(
                is_active=False,
                publish_date__lt=timezone.localtime().date()
            ).order_by('-publish_date')[:10]
            for t in past_topics:
                topics_data.append(format_topic(t, student_id))
        else:
            # 커서 이후 페이지: 과거 토픽만
            cursor_int = int(cursor)
            past_topics = Topic.objects.filter(
                topic_id__lt=cursor_int,
                is_active=False,
                publish_date__lt=timezone.localtime().date()
            ).order_by('-publish_date')[:10]
            for t in past_topics:
                topics_data.append(format_topic(t, student_id))

        # next_cursor 계산
        next_cursor = None
        has_more = False
        if topics_data:
            last_topic_id = topics_data[-1]['topic_id']
            remaining = Topic.objects.filter(
                topic_id__lt=last_topic_id,
                is_active=False,
                publish_date__lt=timezone.localtime().date()
            ).count()
            if remaining > 0:
                next_cursor = last_topic_id
                has_more = True

        return JsonResponse(
            {
                'status': 'success',
                'data': {
                    'topics': topics_data,
                    'next_cursor': next_cursor,
                    'has_more': has_more,
                },
            },
            json_dumps_params={'ensure_ascii': False},
        )
    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': f'서버 내부 오류: {str(e)}'},
            status=500, json_dumps_params={'ensure_ascii': False},
        )


# ═══════════════════════════════════════════════════════════════
# 3) POST /api/topics/<topic_id>/vote/
# ═══════════════════════════════════════════════════════════════
@csrf_exempt
def handle_vote(request, topic_id):
    """투표 처리 (생성 / 변경 / confirm_required 반환)"""
    if request.method != 'POST':
        return JsonResponse(
            {'status': 'error', 'message': 'POST 메서드만 허용됩니다.'},
            status=405, json_dumps_params={'ensure_ascii': False},
        )

    student_id = get_student_id_from_token(request)
    if not student_id:
        return JsonResponse(
            {'status': 'error', 'message': '유효하지 않은 인증 토큰입니다.'},
            status=401, json_dumps_params={'ensure_ascii': False},
        )

    try:
        topic = Topic.objects.get(topic_id=topic_id)
    except Topic.DoesNotExist:
        return JsonResponse(
            {'status': 'error', 'message': '토픽을 찾을 수 없습니다.'},
            status=404, json_dumps_params={'ensure_ascii': False},
        )

    if not topic.is_active:
        return JsonResponse(
            {'status': 'error', 'message': '이미 종료된 토픽입니다.'},
            status=400, json_dumps_params={'ensure_ascii': False},
        )

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {'status': 'error', 'message': '잘못된 JSON 형식입니다.'},
            status=400, json_dumps_params={'ensure_ascii': False},
        )

    selected_opinion = body.get('selectedOpinion')
    confirm_delete = body.get('confirmDelete', False)

    if selected_opinion is None or not isinstance(selected_opinion, bool):
        return JsonResponse(
            {'status': 'error', 'message': 'selectedOpinion(bool) 값이 필요합니다.'},
            status=400, json_dumps_params={'ensure_ascii': False},
        )

    # Rate limit
    if not rate_limiter.check_rate_limit(student_id, 'vote'):
        return JsonResponse(
            {'status': 'error', 'message': '너무 빠르게 요청하고 있습니다. 잠시 후 다시 시도해주세요.'},
            status=429, json_dumps_params={'ensure_ascii': False},
        )

    try:
        existing_vote = TopicVote.objects.filter(
            topic=topic, student_id=student_id
        ).first()

        if existing_vote:
            if existing_vote.select_opinion == selected_opinion:
                # 같은 의견 → 변경 없음
                return JsonResponse(
                    {'status': 'success', 'message': '이미 같은 의견으로 투표했습니다.'},
                    json_dumps_params={'ensure_ascii': False},
                )
            else:
                # 다른 의견으로 변경
                user_comments = TopicComment.objects.filter(
                    topic=topic, student_id=student_id
                )
                comment_count = user_comments.count()

                if comment_count > 0 and not confirm_delete:
                    return JsonResponse(
                        {
                            'status': 'confirm_required',
                            'message': '의견을 변경하면 작성한 댓글이 삭제됩니다.',
                            'data': {'deletable_count': comment_count},
                        },
                        json_dumps_params={'ensure_ascii': False},
                    )

                with transaction.atomic():
                    if comment_count > 0:
                        # 댓글의 좋아요도 함께 삭제
                        comment_ids = list(user_comments.values_list('comment_id', flat=True))
                        TopicCommentLike.objects.filter(comment_id__in=comment_ids).delete()
                        user_comments.delete()
                        vote_logger.info(
                            "Vote changed with %d comments deleted: student=%s topic=%s %s→%s",
                            comment_count, student_id, topic_id,
                            existing_vote.select_opinion, selected_opinion,
                        )

                    existing_vote.select_opinion = selected_opinion
                    existing_vote.save()

                    # total_vote_count 재계산
                    topic.total_vote_count = TopicVote.objects.filter(topic=topic).count()
                    topic.save(update_fields=['total_vote_count'])

        else:
            # 새 투표
            with transaction.atomic():
                TopicVote.objects.create(
                    topic=topic,
                    student_id=student_id,
                    select_opinion=selected_opinion,
                )
                topic.total_vote_count = F('total_vote_count') + 1
                topic.save(update_fields=['total_vote_count'])
                topic.refresh_from_db()

            vote_logger.info(
                "New vote: student=%s topic=%s opinion=%s",
                student_id, topic_id, selected_opinion,
            )

        # 투표 통계 반환
        opinion1_count = TopicVote.objects.filter(topic=topic, select_opinion=True).count()
        opinion2_count = TopicVote.objects.filter(topic=topic, select_opinion=False).count()
        total_count = opinion1_count + opinion2_count

        return JsonResponse(
            {
                'status': 'success',
                'data': {
                    'opinion_1_count': opinion1_count,
                    'opinion_2_count': opinion2_count,
                    'total_count': total_count,
                    'my_vote': selected_opinion,
                },
            },
            json_dumps_params={'ensure_ascii': False},
        )

    except Exception as e:
        vote_logger.error("Vote error: %s", str(e), exc_info=True)
        return JsonResponse(
            {'status': 'error', 'message': f'서버 내부 오류: {str(e)}'},
            status=500, json_dumps_params={'ensure_ascii': False},
        )


# ═══════════════════════════════════════════════════════════════
# 4) GET /api/topics/<topic_id>/vote/stat/
# ═══════════════════════════════════════════════════════════════
@csrf_exempt
def get_vote_stat(request, topic_id):
    """투표 통계 조회"""
    if request.method != 'GET':
        return JsonResponse(
            {'status': 'error', 'message': 'GET 메서드만 허용됩니다.'},
            status=405, json_dumps_params={'ensure_ascii': False},
        )

    try:
        topic = Topic.objects.get(topic_id=topic_id)
    except Topic.DoesNotExist:
        return JsonResponse(
            {'status': 'error', 'message': '토픽을 찾을 수 없습니다.'},
            status=404, json_dumps_params={'ensure_ascii': False},
        )

    opinion1_count = TopicVote.objects.filter(topic=topic, select_opinion=True).count()
    opinion2_count = TopicVote.objects.filter(topic=topic, select_opinion=False).count()
    total_count = opinion1_count + opinion2_count

    return JsonResponse(
        {
            'status': 'success',
            'data': {
                'opinion_1_count': opinion1_count,
                'opinion_2_count': opinion2_count,
                'total_count': total_count,
            },
        },
        json_dumps_params={'ensure_ascii': False},
    )


# ═══════════════════════════════════════════════════════════════
# 5) POST /api/topics/<topic_id>/comments/
# ═══════════════════════════════════════════════════════════════
@csrf_exempt
def create_topic_comment(request, topic_id):
    """토픽 댓글 작성"""
    if request.method != 'POST':
        return JsonResponse(
            {'status': 'error', 'message': 'POST 메서드만 허용됩니다.'},
            status=405, json_dumps_params={'ensure_ascii': False},
        )

    student_id = get_student_id_from_token(request)
    if not student_id:
        return JsonResponse(
            {'status': 'error', 'message': '유효하지 않은 인증 토큰입니다.'},
            status=401, json_dumps_params={'ensure_ascii': False},
        )

    try:
        topic = Topic.objects.get(topic_id=topic_id)
    except Topic.DoesNotExist:
        return JsonResponse(
            {'status': 'error', 'message': '토픽을 찾을 수 없습니다.'},
            status=404, json_dumps_params={'ensure_ascii': False},
        )

    if not topic.is_active:
        return JsonResponse(
            {'status': 'error', 'message': '이미 종료된 토픽입니다.'},
            status=400, json_dumps_params={'ensure_ascii': False},
        )

    # 투표 여부 확인
    try:
        vote = TopicVote.objects.get(topic=topic, student_id=student_id)
    except TopicVote.DoesNotExist:
        return JsonResponse(
            {'status': 'error', 'message': '먼저 투표를 해야 댓글을 작성할 수 있습니다.'},
            status=403, json_dumps_params={'ensure_ascii': False},
        )

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {'status': 'error', 'message': '잘못된 JSON 형식입니다.'},
            status=400, json_dumps_params={'ensure_ascii': False},
        )

    comment_text = body.get('comment', '').strip()
    if not comment_text:
        return JsonResponse(
            {'status': 'error', 'message': '댓글 내용을 입력해주세요.'},
            status=400, json_dumps_params={'ensure_ascii': False},
        )

    # Rate limit
    if not rate_limiter.check_rate_limit(student_id, 'comment'):
        return JsonResponse(
            {'status': 'error', 'message': '너무 빠르게 요청하고 있습니다. 잠시 후 다시 시도해주세요.'},
            status=429, json_dumps_params={'ensure_ascii': False},
        )

    # Profanity check
    is_clean, matched_words = check_profanity(comment_text)
    if not is_clean:
        security_logger.warning(
            "Profanity blocked: student=%s topic=%s words=%s",
            student_id, topic_id, matched_words,
        )
        return JsonResponse(
            {'status': 'error', 'message': '부적절한 표현이 포함되어 있습니다.'},
            status=400, json_dumps_params={'ensure_ascii': False},
        )

    try:
        new_comment = TopicComment.objects.create(
            topic=topic,
            student_id=student_id,
            comment=comment_text,
            select_opinion=vote.select_opinion,
        )

        comment_logger.info(
            "Comment created: id=%s student=%s topic=%s",
            new_comment.comment_id, student_id, topic_id,
        )

        anon_map = build_anon_map(topic_id)
        anon_num = anon_map.get(student_id, '?')

        return JsonResponse(
            {
                'status': 'success',
                'data': {
                    'comment_id': new_comment.comment_id,
                    'writer': f'학생{anon_num}',
                    'is_writer': True,
                    'comment': new_comment.comment,
                    'select_opinion': new_comment.select_opinion,
                    'like_count': new_comment.like_count,
                    'is_liked': False,
                    'created_at': new_comment.created_at.isoformat() if new_comment.created_at else '',
                },
            },
            json_dumps_params={'ensure_ascii': False},
            status=201,
        )
    except Exception as e:
        comment_logger.error("Comment creation error: %s", str(e), exc_info=True)
        return JsonResponse(
            {'status': 'error', 'message': f'서버 내부 오류: {str(e)}'},
            status=500, json_dumps_params={'ensure_ascii': False},
        )


# ═══════════════════════════════════════════════════════════════
# 6) GET /api/topics/<topic_id>/comments/
# ═══════════════════════════════════════════════════════════════
@csrf_exempt
def get_topic_comments(request, topic_id):
    """토픽 댓글 목록 조회 (커서 기반 페이지네이션)"""
    if request.method != 'GET':
        return JsonResponse(
            {'status': 'error', 'message': 'GET 메서드만 허용됩니다.'},
            status=405, json_dumps_params={'ensure_ascii': False},
        )

    student_id = get_student_id_from_token(request)

    opinion_str = request.GET.get('opinion')
    cursor = request.GET.get('cursor')
    sort = request.GET.get('sort', 'latest')

    try:
        topic = Topic.objects.get(topic_id=topic_id)
    except Topic.DoesNotExist:
        return JsonResponse(
            {'status': 'error', 'message': '토픽을 찾을 수 없습니다.'},
            status=404, json_dumps_params={'ensure_ascii': False},
        )

    try:
        anon_map = build_anon_map(topic_id)

        # opinion 파싱
        if opinion_str is None:
            return JsonResponse(
                {'status': 'error', 'message': 'opinion 파라미터가 필요합니다.'},
                status=400, json_dumps_params={'ensure_ascii': False},
            )
        opinion_bool = opinion_str.lower() == 'true'

        qs = TopicComment.objects.filter(
            topic_id=topic_id, select_opinion=opinion_bool
        )
        total_count = qs.count()

        if sort == 'like':
            # 좋아요순: -like_count, -comment_id
            if cursor:
                parts = cursor.split('_')
                if len(parts) == 2:
                    lc = int(parts[0])
                    cid = int(parts[1])
                    qs = qs.filter(
                        Q(like_count__lt=lc) |
                        Q(like_count=lc, comment_id__lt=cid)
                    )
            qs = qs.order_by('-like_count', '-comment_id')
        else:
            # 최신순: -comment_id
            if cursor:
                cursor_int = int(cursor)
                qs = qs.filter(comment_id__lt=cursor_int)
            qs = qs.order_by('-comment_id')

        comments = list(qs[:21])  # 1개 더 가져와서 has_more 판단
        has_more = len(comments) > 20
        comments = comments[:20]

        comments_data = []
        for c in comments:
            anon_num = anon_map.get(c.student_id, '?')
            writer = f'학생{anon_num}'
            is_writer = (student_id is not None and c.student_id == student_id)
            if is_writer:
                writer = f'학생{anon_num} (나)'

            is_liked = False
            if student_id:
                is_liked = TopicCommentLike.objects.filter(
                    comment=c, student_id=student_id
                ).exists()

            comments_data.append({
                'comment_id': c.comment_id,
                'writer': writer,
                'is_writer': is_writer,
                'comment': c.comment,
                'select_opinion': c.select_opinion,
                'like_count': c.like_count,
                'is_liked': is_liked,
                'created_at': c.created_at.isoformat() if c.created_at else '',
            })

        # next_cursor 계산
        next_cursor = None
        if has_more and comments:
            last = comments[-1]
            if sort == 'like':
                next_cursor = f'{last.like_count}_{last.comment_id}'
            else:
                next_cursor = str(last.comment_id)

        return JsonResponse(
            {
                'status': 'success',
                'data': {
                    'comments': comments_data,
                    'next_cursor': next_cursor,
                    'has_more': has_more,
                    'total_count': total_count,
                },
            },
            json_dumps_params={'ensure_ascii': False},
        )
    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': f'서버 내부 오류: {str(e)}'},
            status=500, json_dumps_params={'ensure_ascii': False},
        )


# ═══════════════════════════════════════════════════════════════
# 7) PUT/DELETE /api/topics/comments/<comment_id>/
# ═══════════════════════════════════════════════════════════════
@csrf_exempt
def manage_topic_comment(request, comment_id):
    """토픽 댓글 수정 / 삭제"""
    student_id = get_student_id_from_token(request)
    if not student_id:
        return JsonResponse(
            {'status': 'error', 'message': '유효하지 않은 인증 토큰입니다.'},
            status=401, json_dumps_params={'ensure_ascii': False},
        )

    try:
        comment = TopicComment.objects.get(comment_id=comment_id)
    except TopicComment.DoesNotExist:
        return JsonResponse(
            {'status': 'error', 'message': '댓글을 찾을 수 없습니다.'},
            status=404, json_dumps_params={'ensure_ascii': False},
        )

    # 권한 검증
    if comment.student_id != student_id:
        return JsonResponse(
            {'status': 'error', 'message': '권한이 없습니다.'},
            status=403, json_dumps_params={'ensure_ascii': False},
        )

    # 토픽 활성 여부 확인
    if not comment.topic.is_active:
        return JsonResponse(
            {'status': 'error', 'message': '이미 종료된 토픽의 댓글은 수정/삭제할 수 없습니다.'},
            status=400, json_dumps_params={'ensure_ascii': False},
        )

    # ── PUT: 댓글 수정 ───────────────────────────────────────
    if request.method == 'PUT':
        try:
            body = json.loads(request.body)
            comment_text = body.get('comment', '').strip()

            if not comment_text:
                return JsonResponse(
                    {'status': 'error', 'message': '댓글 내용을 입력해주세요.'},
                    status=400, json_dumps_params={'ensure_ascii': False},
                )

            # Profanity check
            is_clean, matched_words = check_profanity(comment_text)
            if not is_clean:
                security_logger.warning(
                    "Profanity blocked on edit: student=%s comment_id=%s words=%s",
                    student_id, comment_id, matched_words,
                )
                return JsonResponse(
                    {'status': 'error', 'message': '부적절한 표현이 포함되어 있습니다.'},
                    status=400, json_dumps_params={'ensure_ascii': False},
                )

            comment.comment = comment_text
            comment.save()

            comment_logger.info(
                "Comment updated: id=%s student=%s", comment_id, student_id,
            )

            anon_map = build_anon_map(comment.topic_id)
            anon_num = anon_map.get(student_id, '?')

            return JsonResponse(
                {
                    'status': 'success',
                    'message': '댓글이 수정되었습니다.',
                    'data': {
                        'comment_id': comment.comment_id,
                        'writer': f'학생{anon_num} (나)',
                        'comment': comment.comment,
                        'select_opinion': comment.select_opinion,
                        'like_count': comment.like_count,
                        'created_at': comment.created_at.isoformat() if comment.created_at else '',
                    },
                },
                json_dumps_params={'ensure_ascii': False},
            )
        except json.JSONDecodeError:
            return JsonResponse(
                {'status': 'error', 'message': '잘못된 JSON 형식입니다.'},
                status=400, json_dumps_params={'ensure_ascii': False},
            )
        except Exception as e:
            return JsonResponse(
                {'status': 'error', 'message': f'서버 내부 오류: {str(e)}'},
                status=500, json_dumps_params={'ensure_ascii': False},
            )

    # ── DELETE: 댓글 삭제 ────────────────────────────────────
    elif request.method == 'DELETE':
        try:
            # 연관 좋아요 삭제
            TopicCommentLike.objects.filter(comment=comment).delete()
            comment.delete()

            comment_logger.info(
                "Comment deleted: id=%s student=%s", comment_id, student_id,
            )

            return JsonResponse(
                {'status': 'success', 'message': '댓글이 삭제되었습니다.'},
                json_dumps_params={'ensure_ascii': False},
            )
        except Exception as e:
            return JsonResponse(
                {'status': 'error', 'message': f'서버 내부 오류: {str(e)}'},
                status=500, json_dumps_params={'ensure_ascii': False},
            )

    return JsonResponse(
        {'status': 'error', 'message': 'PUT 또는 DELETE 메서드만 허용됩니다.'},
        status=405, json_dumps_params={'ensure_ascii': False},
    )


# ═══════════════════════════════════════════════════════════════
# 8) POST /api/topics/comments/<comment_id>/like/
# ═══════════════════════════════════════════════════════════════
@csrf_exempt
def toggle_topic_comment_like(request, comment_id):
    """댓글 좋아요 토글"""
    if request.method != 'POST':
        return JsonResponse(
            {'status': 'error', 'message': 'POST 메서드만 허용됩니다.'},
            status=405, json_dumps_params={'ensure_ascii': False},
        )

    student_id = get_student_id_from_token(request)
    if not student_id:
        return JsonResponse(
            {'status': 'error', 'message': '유효하지 않은 인증 토큰입니다.'},
            status=401, json_dumps_params={'ensure_ascii': False},
        )

    try:
        comment = TopicComment.objects.get(comment_id=comment_id)
    except TopicComment.DoesNotExist:
        return JsonResponse(
            {'status': 'error', 'message': '댓글을 찾을 수 없습니다.'},
            status=404, json_dumps_params={'ensure_ascii': False},
        )

    if not comment.topic.is_active:
        return JsonResponse(
            {'status': 'error', 'message': '이미 종료된 토픽의 댓글에는 좋아요를 할 수 없습니다.'},
            status=400, json_dumps_params={'ensure_ascii': False},
        )

    # Rate limit
    if not rate_limiter.check_rate_limit(student_id, 'like'):
        return JsonResponse(
            {'status': 'error', 'message': '너무 빠르게 요청하고 있습니다. 잠시 후 다시 시도해주세요.'},
            status=429, json_dumps_params={'ensure_ascii': False},
        )

    try:
        with transaction.atomic():
            existing_like = TopicCommentLike.objects.filter(
                comment=comment, student_id=student_id
            ).first()

            if existing_like:
                existing_like.delete()
                comment.like_count = max(0, comment.like_count - 1)
                comment.save(update_fields=['like_count'])
                action = 'unliked'
            else:
                TopicCommentLike.objects.create(
                    comment=comment,
                    student_id=student_id,
                )
                comment.like_count = F('like_count') + 1
                comment.save(update_fields=['like_count'])
                comment.refresh_from_db()
                action = 'liked'

        return JsonResponse(
            {
                'status': 'success',
                'data': {
                    'action': action,
                    'like_count': comment.like_count,
                },
            },
            json_dumps_params={'ensure_ascii': False},
        )
    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': f'서버 내부 오류: {str(e)}'},
            status=500, json_dumps_params={'ensure_ascii': False},
        )
