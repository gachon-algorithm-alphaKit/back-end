from django.db import models
from .users import Student


class Topic(models.Model):
    topic_id = models.AutoField(primary_key=True)
    title = models.TextField()
    opinion_1 = models.TextField()
    opinion_2 = models.TextField()
    publish_date = models.DateField()
    is_active = models.BooleanField(default=False)
    total_vote_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['publish_date'], name='idx_topic_publish_date'),
        ]

    def __str__(self):
        return f"[{self.publish_date}] {self.title}"


class TopicVote(models.Model):
    vote_id = models.AutoField(primary_key=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, db_column='topic_id')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, db_column='student_id')
    select_opinion = models.BooleanField()  # True=opinion_1, False=opinion_2
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['topic', 'student'], name='unique_topic_vote'),
        ]
        indexes = [
            models.Index(fields=['topic'], name='idx_vote_topic'),
        ]

    def __str__(self):
        return f"Vote {self.vote_id}: topic={self.topic_id}, student={self.student_id}"


class TopicComment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, db_column='topic_id')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, db_column='student_id')
    comment = models.TextField()
    select_opinion = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    like_count = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['topic', '-like_count', '-comment_id'], name='idx_comment_topic_like'),
        ]

    def __str__(self):
        return f"Comment {self.comment_id} on topic {self.topic_id}"


class TopicCommentLike(models.Model):
    like_id = models.AutoField(primary_key=True)
    comment = models.ForeignKey(TopicComment, on_delete=models.CASCADE, db_column='comment_id')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, db_column='student_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['comment', 'student'], name='unique_comment_like'),
        ]

    def __str__(self):
        return f"Like {self.like_id}: comment={self.comment_id}, student={self.student_id}"
