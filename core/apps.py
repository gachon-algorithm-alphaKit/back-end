from django.apps import AppConfig
import sys

class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv:
            from core.utils.course_search import search_engine
            try:
                search_engine.load_data()
                print("CourseSearchEngine initialized successfully.")
            except Exception as e:
                print(f"Failed to initialize CourseSearchEngine: {e}")
