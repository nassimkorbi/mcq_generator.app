from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_pdf, name='upload_pdf'),
    path('document/<uuid:document_id>/', views.document_detail, name='document_detail'),
    path('document/<uuid:document_id>/quiz/create/', views.create_quiz, name='create_quiz'),
    path('document/<uuid:document_id>/debug/', views.debug_quiz_generation, name='debug_quiz_generation'),
    path('quiz/<uuid:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('quiz/<uuid:quiz_id>/results/', views.quiz_results, name='quiz_results'),
    path('document/<uuid:document_id>/chat/', views.chatbot, name='chatbot'),
    path('api/chat/<uuid:document_id>/', views.chat_api, name='chat_api'),
]
