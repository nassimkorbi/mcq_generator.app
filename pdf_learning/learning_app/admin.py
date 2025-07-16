from django.contrib import admin
from .models import PDFDocument, QuizSession, Question, ChatMessage

@admin.register(PDFDocument)
class PDFDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'total_pages', 'processed', 'uploaded_at']
    list_filter = ['processed', 'uploaded_at']
    search_fields = ['title']
    readonly_fields = ['id', 'uploaded_at']

@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = ['document', 'topic', 'completed', 'score', 'created_at']
    list_filter = ['completed', 'created_at']
    search_fields = ['document__title', 'topic']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz_session', 'question_text', 'correct_answer', 'is_correct']
    list_filter = ['question_type', 'is_correct']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['document', 'message', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['document__title', 'message']
