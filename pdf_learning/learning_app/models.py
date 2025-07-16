from django.db import models
import uuid

class PDFDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='pdfs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    total_pages = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return self.title

class QuizSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(PDFDocument, on_delete=models.CASCADE)
    topic = models.CharField(max_length=200, blank=True)
    page_range = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    score = models.FloatField(null=True, blank=True)

class Question(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
    ]
    
    quiz_session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='mcq')
    options = models.JSONField()  # Store as {"A": "option1", "B": "option2", ...}
    correct_answer = models.CharField(max_length=1)  # A, B, C, or D
    explanation = models.TextField(blank=True)
    user_answer = models.CharField(max_length=1, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)

class ChatMessage(models.Model):
    document = models.ForeignKey(PDFDocument, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
