import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.files.storage import default_storage
from .models import PDFDocument, QuizSession, Question, ChatMessage
from .pdf_processor import PDFProcessor
from .ai_service import AIService

def home(request):
    """Home page with upload form"""
    documents = PDFDocument.objects.all().order_by('-uploaded_at')
    return render(request, 'learning_app/home.html', {'documents': documents})

def upload_pdf(request):
    """Handle PDF upload"""
    if request.method == 'POST':
        if 'pdf_file' not in request.FILES:
            messages.error(request, 'No file selected')
            return redirect('home')
        
        pdf_file = request.FILES['pdf_file']
        title = request.POST.get('title', pdf_file.name)
        
        # Validate file
        if not pdf_file.name.endswith('.pdf'):
            messages.error(request, 'Please upload a PDF file')
            return redirect('home')
        
        try:
            # Create document record
            document = PDFDocument.objects.create(
                title=title,
                file=pdf_file
            )
            
            # Process PDF
            processor = PDFProcessor()
            ai_service = AIService()
            
            # Extract text and get page count
            full_text, total_pages = processor.extract_text_from_pdf(pdf_file)
            document.total_pages = total_pages
            document.save()
            
            # Create text chunks and add to vector database
            chunks, page_numbers = processor.chunk_text(full_text)
            ai_service.add_text_chunks(str(document.id), chunks, page_numbers)
            
            document.processed = True
            document.save()
            
            messages.success(request, f'PDF "{title}" uploaded and processed successfully!')
            return redirect('document_detail', document_id=document.id)
            
        except Exception as e:
            messages.error(request, f'Error processing PDF: {str(e)}')
            return redirect('home')
    
    return redirect('home')

def document_detail(request, document_id):
    """Document detail page"""
    document = get_object_or_404(PDFDocument, id=document_id)
    quiz_sessions = QuizSession.objects.filter(document=document).order_by('-created_at')
    
    return render(request, 'learning_app/document_detail.html', {
        'document': document,
        'quiz_sessions': quiz_sessions
    })

def create_quiz(request, document_id):
    """Create a new quiz session with comprehensive debugging"""
    document = get_object_or_404(PDFDocument, id=document_id)
    
    if not document.processed:
        messages.error(request, 'Document is still being processed. Please wait and try again.')
        return redirect('document_detail', document_id=document.id)
    
    if request.method == 'POST':
        topic = request.POST.get('topic', '').strip()
        page_range = request.POST.get('page_range', '').strip()
        num_questions = int(request.POST.get('num_questions', 5))
        
        print("="*50)
        print("QUIZ GENERATION DEBUG")
        print("="*50)
        print(f"Document ID: {document.id}")
        print(f"Document Title: {document.title}")
        print(f"Topic: '{topic}'")
        print(f"Page Range: '{page_range}'")
        print(f"Number of Questions: {num_questions}")
        
        try:
            # Test AI connection first
            ai_service = AIService()
            
            print("Testing AI connection...")
            if not ai_service.test_connection():
                messages.error(request, 'AI service is not available. Please make sure Ollama is running with Gemma 2B model.')
                return redirect('document_detail', document_id=document.id)
            print("✓ AI connection successful")
            
            # Test context retrieval
            print("Testing context retrieval...")
            test_query = topic if topic else "main concepts"
            context_chunks = ai_service.retrieve_relevant_context(str(document.id), test_query, n_results=3)
            
            if not context_chunks:
                messages.error(request, 'No content found in the document. The document might not have been processed correctly.')
                return redirect('document_detail', document_id=document.id)
            
            print(f"✓ Retrieved {len(context_chunks)} context chunks")
            print(f"Sample context (first 200 chars): {context_chunks[0][:200]}...")
            
            # Create quiz session
            quiz_session = QuizSession.objects.create(
                document=document,
                topic=topic,
                page_range=page_range
            )
            print(f"✓ Quiz session created: {quiz_session.id}")
            
            # Generate questions with detailed logging
            print("Starting question generation...")
            questions_data = ai_service.generate_mcq_questions(
                str(document.id), 
                topic, 
                page_range, 
                num_questions
            )
            
            print(f"Question generation completed. Generated {len(questions_data)} questions")
            
            if not questions_data:
                print("❌ No questions generated")
                
                # Try a simpler approach - generate just one question to test
                print("Attempting to generate a single test question...")
                test_context = context_chunks[0][:800]  # Use first chunk, limited size
                test_question = ai_service.generate_single_mcq(test_context, topic)
                
                if test_question:
                    print("✓ Test question generation successful")
                    questions_data = [test_question]
                else:
                    print("❌ Even test question generation failed")
                    messages.error(request, 
                        'Unable to generate questions. This could be due to:\n'
                        '• Complex or unclear content in the specified range\n'
                        '• AI model limitations with the current topic\n'
                        '• Try with a simpler topic or different page range\n'
                        '• Check that Ollama and Gemma 2B are working properly'
                    )
                    quiz_session.delete()
                    return redirect('document_detail', document_id=document.id)
            
            # Create question objects
            created_questions = 0
            for i, q_data in enumerate(questions_data):
                try:
                    print(f"Creating question {i+1}: {q_data.get('question_text', 'No text')[:50]}...")
                    
                    Question.objects.create(
                        quiz_session=quiz_session,
                        question_text=q_data['question_text'],
                        options=q_data['options'],
                        correct_answer=q_data['correct_answer'],
                        explanation=q_data.get('explanation', '')
                    )
                    created_questions += 1
                    print(f"✓ Question {i+1} created successfully")
                    
                except Exception as e:
                    print(f"❌ Error creating question {i+1}: {e}")
                    continue
            
            if created_questions == 0:
                print("❌ No questions were successfully created")
                messages.error(request, 'Failed to create any questions. Please try again with different parameters.')
                quiz_session.delete()
                return redirect('document_detail', document_id=document.id)
            
            print(f"✓ Successfully created {created_questions} questions")
            print("="*50)
            
            messages.success(request, f'🎉 Quiz created successfully with {created_questions} questions!')
            return redirect('take_quiz', quiz_id=quiz_session.id)
            
        except Exception as e:
            import traceback
            print(f"❌ CRITICAL ERROR: {str(e)}")
            print("Full traceback:")
            print(traceback.format_exc())
            print("="*50)
            
            messages.error(request, f'Unexpected error: {str(e)}. Please check the console for details and try again.')
            return redirect('document_detail', document_id=document.id)
    
    return render(request, 'learning_app/create_quiz.html', {'document': document})

def take_quiz(request, quiz_id):
    """Take a quiz"""
    quiz_session = get_object_or_404(QuizSession, id=quiz_id)
    questions = quiz_session.questions.all()
    
    if request.method == 'POST':
        # Process quiz submission
        ai_service = AIService()
        correct_count = 0
        
        for question in questions:
            user_answer = request.POST.get(f'question_{question.id}', '').strip().upper()
            question.user_answer = user_answer
            
            if user_answer == question.correct_answer:
                question.is_correct = True
                correct_count += 1
            else:
                question.is_correct = False
            
            question.save()
        
        # Calculate score
        total_questions = questions.count()
        score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        
        quiz_session.score = score
        quiz_session.completed = True
        quiz_session.save()
        
        return redirect('quiz_results', quiz_id=quiz_session.id)
    
    return render(request, 'learning_app/take_quiz.html', {
        'quiz_session': quiz_session,
        'questions': questions
    })

def quiz_results(request, quiz_id):
    """Show quiz results"""
    quiz_session = get_object_or_404(QuizSession, id=quiz_id)
    questions = quiz_session.questions.all()
    
    return render(request, 'learning_app/quiz_results.html', {
        'quiz_session': quiz_session,
        'questions': questions
    })

def chatbot(request, document_id):
    """Chatbot interface"""
    document = get_object_or_404(PDFDocument, id=document_id)
    messages_history = ChatMessage.objects.filter(document=document).order_by('timestamp')
    
    return render(request, 'learning_app/chatbot.html', {
        'document': document,
        'messages': messages_history
    })

@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request, document_id):
    """API endpoint for chat"""
    document = get_object_or_404(PDFDocument, id=document_id)
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get AI response
        ai_service = AIService()
        ai_response = ai_service.answer_question(str(document.id), user_message)
        
        # Save chat message
        chat_message = ChatMessage.objects.create(
            document=document,
            message=user_message,
            response=ai_response
        )
        
        return JsonResponse({
            'response': ai_response,
            'timestamp': chat_message.timestamp.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def debug_quiz_generation(request, document_id):
    """Debug view to test quiz generation step by step"""
    document = get_object_or_404(PDFDocument, id=document_id)
    
    debug_info = {
        'document': document,
        'tests': []
    }
    
    try:
        ai_service = AIService()
        
        # Test 1: AI Connection
        test_result = {
            'name': 'AI Connection Test',
            'status': 'success' if ai_service.test_connection() else 'failed',
            'details': 'Testing connection to Gemma 2B via Ollama'
        }
        debug_info['tests'].append(test_result)
        
        # Test 2: Context Retrieval
        context_chunks = ai_service.retrieve_relevant_context(str(document.id), "main concepts", n_results=3)
        test_result = {
            'name': 'Context Retrieval Test',
            'status': 'success' if context_chunks else 'failed',
            'details': f'Retrieved {len(context_chunks)} context chunks'
        }
        if context_chunks:
            test_result['sample'] = context_chunks[0][:200] + "..."
        debug_info['tests'].append(test_result)
        
        # Test 3: Single Question Generation
        if context_chunks:
            test_question = ai_service.generate_single_mcq(context_chunks[0][:800], "")
            test_result = {
                'name': 'Single Question Generation Test',
                'status': 'success' if test_question else 'failed',
                'details': 'Testing generation of a single MCQ question'
            }
            if test_question:
                test_result['question'] = test_question
            debug_info['tests'].append(test_result)
        
    except Exception as e:
        debug_info['error'] = str(e)
    
    return render(request, 'learning_app/debug_quiz.html', debug_info)
