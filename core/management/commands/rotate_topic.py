"""
수동 토픽 교체 management command.

Usage:
    python manage.py rotate_topic
"""

from django.core.management.base import BaseCommand
from core.utils.topic_scheduler import rotate_topic


class Command(BaseCommand):
    help = '밸런스 게임 토픽을 수동으로 교체합니다 (오늘 토픽 활성화)'

    def handle(self, *args, **options):
        self.stdout.write('토픽 교체를 시작합니다...')
        rotate_topic()
        self.stdout.write(self.style.SUCCESS('토픽 교체가 완료되었습니다.'))
