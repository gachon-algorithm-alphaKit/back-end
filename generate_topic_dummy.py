import os
import sys
import django
import random
import argparse
from datetime import timedelta
from django.utils import timezone

sys.path.append('d:/project/AlphaKit/back-end')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Topic, TopicComment, TopicVote, Student

def generate_comments_for_topic(topic, students):
    print(f"[{topic.publish_date}] '{topic.title}' 더미 데이터 생성 중...")

    # 이미 투표가 있으면 스킵할지, 아니면 초기화할지 결정 (여기서는 초기화 후 덮어쓰기)
    TopicVote.objects.filter(topic=topic).delete()
    TopicComment.objects.filter(topic=topic).delete()

    # 자연스러운 한국어 문장 템플릿 (어떤 주제의 옵션이든 어울리도록)
    prefixes = [
        "전 솔직히", "생각해봤는데,", "아무리 그래도", "저는 무조건", "누가 뭐래도",
        "음... 고민되지만", "현실적으로 생각하면", "제 성향상", "이건 닥치고",
        "친구들이랑 얘기해봤는데 다들"
    ]
    suffixes = [
        "선택할래요.", "쪽이 낫다고 봅니다.", "고를 것 같아요.", "가 최고죠 ㅋㅋ",
        "없이는 못 살 것 같아요 ㅠㅠ", "쪽으로 마음이 기우네요.", "가 정답 아닌가요?",
        "할 바에는 차라리 죽음을 택하겠습니다...", "가 더 행복할 듯.", "할게요!"
    ]
    extras = ["", "ㅋㅋ", "ㅎㅎ", "ㅠㅠ", "인정하시나요?", "저만 그런가요?", "밸런스 진짜 황금밸런스네;;", "오늘 주제 너무 재밌어요!"]

    created_comments = 0
    sample_students = random.sample(students, min(len(students), random.randint(150, 250)))

    for student in sample_students:
        # 30%~70% 랜덤 비율로 옵션 1, 옵션 2 선택
        op_prob = random.uniform(0.3, 0.7)
        op = random.random() < op_prob

        # 1. 투표 생성
        TopicVote.objects.create(
            topic=topic,
            student=student,
            select_opinion=op
        )

        # 2. 댓글 내용 조립
        op_text = topic.opinion_1 if op else topic.opinion_2
        
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        extra = random.choice(extras)
        
        # 20% 확률로 짧은 댓글
        if random.random() < 0.2:
            comment_text = f"'{op_text}' {suffix} {extra}".strip()
        else:
            comment_text = f"{prefix} '{op_text}' {suffix} {extra}".strip()

        # 좋아요 수 무작위 부여
        like_count = random.randint(0, 30)
        if random.random() < 0.05:
            like_count = random.randint(50, 200) # 베스트 댓글

        TopicComment.objects.create(
            topic=topic,
            student=student,
            comment=comment_text,
            select_opinion=op,
            like_count=like_count
        )
        created_comments += 1

    topic.total_vote_count = TopicVote.objects.filter(topic=topic).count()
    topic.save()
    print(f"  -> {created_comments}개의 투표 및 댓글 생성 완료.\n")

def main():
    parser = argparse.ArgumentParser(description="오늘 이후 또는 특정 기간의 토픽 더미 데이터 생성기")
    parser.add_argument('--all', action='store_true', help="모든 토픽에 대해 생성")
    parser.add_argument('--days', type=int, default=7, help="오늘부터 며칠 후까지 생성할지 (기본: 7일)")
    args = parser.parse_args()

    today = timezone.now().date()

    if args.all:
        topics = Topic.objects.all()
    else:
        end_date = today + timedelta(days=args.days)
        topics = Topic.objects.filter(publish_date__gte=today, publish_date__lte=end_date)
    
    if not topics.exists():
        print("조건에 맞는 토픽이 없습니다.")
        return

    students = list(Student.objects.all())
    if not students:
        print("학생 데이터가 없습니다.")
        return

    print(f"총 {topics.count()}개의 토픽에 대해 더미 데이터를 생성합니다...\n")
    for topic in topics:
        generate_comments_for_topic(topic, students)

    print("모든 더미 데이터 생성이 완료되었습니다!")

if __name__ == '__main__':
    main()
