import os
import sys
import django
import random
from django.utils import timezone

sys.path.append('d:/project/AlphaKit/back-end')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Topic, TopicVote, TopicComment, TopicCommentLike, Student

def main():
    today = timezone.localtime().date()
    
    topic = Topic.objects.filter(publish_date=today).first()
    
    if not topic:
        topic = Topic.objects.create(
            title="테스트 밸런스 게임",
            opinion_1="옵션 A",
            opinion_2="옵션 B",
            publish_date=today,
            is_active=True
        )
        print("오늘의 토픽이 없어서 새로 생성했습니다.")

    print(f"[{today}] '{topic.title}' 더미 데이터 생성을 시작합니다...")

    TopicVote.objects.filter(topic=topic).delete()
    TopicComment.objects.filter(topic=topic).delete()
    TopicCommentLike.objects.filter(comment__topic=topic).delete()
    
    students = list(Student.objects.all())
    if len(students) < 300:
        print(f"현재 학생 수가 {len(students)}명입니다. 부족한 인원을 채웁니다.")
        for i in range(300 - len(students)):
            s = Student.objects.create(
                student_id=f"test_student_new_{i}",
                email=f"test_{i}@example.com"
            )
            s.name = f"학생_{i}"
            s.save()
        students = list(Student.objects.all())
    
    sample_students = random.sample(students, 300)
    
    created_comments = []
    
    prefixes = ["저는", "솔직히", "생각해봤는데", "무조건", "아무리 봐도"]
    suffixes = ["선택할게요.", "쪽이 맞죠.", "가 좋습니다.", "할래요.", "가 짱이죠!"]
    
    print("1단계: 300명의 학생 투표 및 댓글 작성 중...")
    
    for student in sample_students:
        is_opinion_1 = random.choice([True, False])
        
        TopicVote.objects.create(
            topic=topic,
            student=student,
            select_opinion=is_opinion_1
        )
        
        if random.random() <= 0.3:
            op_text = topic.opinion_1 if is_opinion_1 else topic.opinion_2
            comment_text = f"{random.choice(prefixes)} '{op_text}' {random.choice(suffixes)}"
            
            c = TopicComment.objects.create(
                topic=topic,
                student=student,
                comment=comment_text,
                select_opinion=is_opinion_1,
                like_count=0
            )
            created_comments.append(c)

    topic.total_vote_count = TopicVote.objects.filter(topic=topic).count()
    topic.save()

    print(f"-> 총 300명 투표 완료, {len(created_comments)}개의 댓글 생성됨.")
    print("2단계: 작성된 댓글에 대한 좋아요(추천) 누르기 로직 실행 중...")

    comments_op1 = [c for c in created_comments if c.select_opinion]
    comments_op2 = [c for c in created_comments if not c.select_opinion]

    for student in sample_students:
        vote = TopicVote.objects.get(topic=topic, student=student)
        target_comments = comments_op1 if vote.select_opinion else comments_op2
        
        num_likes = min(5, len(target_comments))
        if num_likes == 0:
            continue
            
        selected_comments = set()
        
        for _ in range(num_likes):
            candidates = [c for c in target_comments if c not in selected_comments]
            if not candidates:
                break
                
            if random.random() <= 0.7:
                candidates.sort(key=lambda x: x.like_count, reverse=True)
                top_pool_size = max(1, int(len(candidates) * 0.3))
                chosen = random.choice(candidates[:top_pool_size])
            else:
                chosen = random.choice(candidates)
                
            selected_comments.add(chosen)
            chosen.like_count += 1
            
            TopicCommentLike.objects.create(
                comment=chosen,
                student=student
            )
            
    TopicComment.objects.bulk_update(created_comments, ['like_count'])

    print("-> 추천(좋아요) 처리 완료!")
    print("\n사용법:")
    print("python generate_balancegame_dummy.py")
    print("이후 클라이언트에서 밸런스 게임 페이지에 접속하여 오늘 날짜의 토픽과 댓글, 좋아요 데이터를 확인하세요.")

if __name__ == '__main__':
    main()
