import json
import os
import django
from django.test import RequestFactory
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.api.rooms import recommend_study_rooms

def test_api():
    current_tz = timezone.get_current_timezone()
    tomorrow = timezone.now().date() + timedelta(days=1)
    base_time = timezone.make_aware(timezone.datetime.combine(tomorrow, timezone.datetime.min.time()), current_tz)
    
    time_10 = base_time + timedelta(hours=10)
    time_13 = base_time + timedelta(hours=13)
    
    payload = {
        "school_id": 99,
        "head_count": 2,
        "start_time": time_10.isoformat(),
        "end_time": time_13.isoformat(),
        "facilities": ["TV"],
        "page": 1,
        "limit": 10
    }
    
    factory = RequestFactory()
    request = factory.post('/api/rooms/recommend', data=json.dumps(payload), content_type='application/json')
    response = recommend_study_rooms(request)
    print(response.status_code)
    try:
        print(json.dumps(json.loads(response.content), indent=2, ensure_ascii=False))
    except Exception:
        print(response.content.decode('utf-8'))

if __name__ == '__main__':
    test_api()
