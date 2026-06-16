import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import LostItemPost

items = LostItemPost.objects.all()
valid_categories = ['전자기기', '지갑/카드', '의류/액세서리', '가방/파우치', '학용품', '열쇠/USB', '기타']
updated_count = 0

for item in items:
    if item.category not in valid_categories:
        # Move category to place if place is empty
        if not item.place and item.category:
            item.place = item.category
        
        title = item.title or ''
        desc = item.description or ''
        text = title + ' ' + desc
        
        if any(x in text for x in ['에어팟', '아이패드', '폰', '노트북']):
            item.category = '전자기기'
        elif any(x in text for x in ['지갑', '카드', '학생증', '신분증']):
            item.category = '지갑/카드'
        elif any(x in text for x in ['옷', '잠바', '모자', '안경', '목걸이']):
            item.category = '의류/액세서리'
        elif any(x in text for x in ['가방', '백팩', '파우치']):
            item.category = '가방/파우치'
        elif any(x in text for x in ['펜', '필통', '공책', '책']):
            item.category = '학용품'
        elif any(x in text for x in ['열쇠', 'USB', '키']):
            item.category = '열쇠/USB'
        else:
            item.category = '기타'
            
        item.save()
        updated_count += 1

print(f"DB 업데이트 완료: 총 {updated_count}개의 항목이 수정되었습니다.")
