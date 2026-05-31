from django.contrib import admin
from .models import (
    School, Place, CampusEdge, PlaceAlias, Student, Professor, Course, StudentCourse, StudyRoom,
    Reservation, Scholarship, ScholarshipHistory, LostItemPost, Comment,
    Topic, TopicVote, TopicComment, TopicCommentLike
)

admin.site.register(School)
admin.site.register(Place)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'login_id', 'name', 'school')
    readonly_fields = ('student_id',)

admin.site.register(Student, StudentAdmin)
admin.site.register(Professor)
admin.site.register(Course)
admin.site.register(StudentCourse)
admin.site.register(StudyRoom)
admin.site.register(Reservation)
admin.site.register(Scholarship)
admin.site.register(ScholarshipHistory)
admin.site.register(LostItemPost)
admin.site.register(Comment)
admin.site.register(CampusEdge)
admin.site.register(PlaceAlias)


# ── 밸런스 게임 (Topic) ──────────────────────────────────────
class TopicAdmin(admin.ModelAdmin):
    list_display = ('topic_id', 'title', 'publish_date', 'is_active', 'total_vote_count')
    list_filter = ('is_active', 'publish_date')
    ordering = ('-publish_date',)


class TopicVoteAdmin(admin.ModelAdmin):
    list_display = ('vote_id', 'topic', 'student', 'select_opinion', 'created_at')
    list_filter = ('select_opinion',)


class TopicCommentAdmin(admin.ModelAdmin):
    list_display = ('comment_id', 'topic', 'student', 'select_opinion', 'like_count', 'created_at')
    list_filter = ('select_opinion',)
    ordering = ('-created_at',)


admin.site.register(Topic, TopicAdmin)
admin.site.register(TopicVote, TopicVoteAdmin)
admin.site.register(TopicComment, TopicCommentAdmin)
admin.site.register(TopicCommentLike)
