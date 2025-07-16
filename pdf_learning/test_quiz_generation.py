#!/usr/bin/env python
"""
Test script for quiz generation functionality
Run this to test if quiz generation is working properly
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pdf_learning.settings')
django.setup()

from learning_app.ai_service import AIService
from learning_app.models import PDFDocument

def test_quiz_generation():
    print("🧪 Testing Quiz Generation System")
    print("=" * 50)
    
    # Test 1: AI Service Connection
    print("1. Testing AI Service Connection...")
    ai_service = AIService()
    
    if ai_service.test_connection():
        print("✅ AI service connection successful")
    else:
        print("❌ AI service connection failed")
        print("   Make sure Ollama is running: ollama serve")
        print("   Make sure Gemma 2B is available: ollama pull gemma2:2b")
        return False
    
    # Test 2: Document Processing
    print("\n2. Testing Document Processing...")
    documents = PDFDocument.objects.filter(processed=True)
    
    if not documents.exists():
        print("❌ No processed documents found")
        print("   Please upload and process a PDF document first")
        return False
    
    document = documents.first()
    print(f"✅ Found processed document: {document.title}")
    
    # Test 3: Context Retrieval
    print("\n3. Testing Context Retrieval...")
    context_chunks = ai_service.retrieve_relevant_context(
        str(document.id), 
        "main concepts", 
        n_results=3
    )
    
    if context_chunks:
        print(f"✅ Retrieved {len(context_chunks)} context chunks")
        print(f"   Sample: {context_chunks[0][:100]}...")
    else:
        print("❌ No context chunks retrieved")
        return False
    
    # Test 4: Single Question Generation
    print("\n4. Testing Single Question Generation...")
    test_question = ai_service.generate_single_mcq(context_chunks[0][:800], "")
    
    if test_question:
        print("✅ Single question generation successful")
        print(f"   Question: {test_question['question_text'][:60]}...")
        print(f"   Options: {len(test_question['options'])}")
        print(f"   Correct Answer: {test_question['correct_answer']}")
    else:
        print("❌ Single question generation failed")
        return False
    
    # Test 5: Multiple Questions Generation
    print("\n5. Testing Multiple Questions Generation...")
    questions = ai_service.generate_mcq_questions(
        str(document.id), 
        topic="", 
        page_range="", 
        num_questions=3
    )
    
    if questions:
        print(f"✅ Generated {len(questions)} questions successfully")
        for i, q in enumerate(questions, 1):
            print(f"   Q{i}: {q['question_text'][:50]}...")
    else:
        print("❌ Multiple questions generation failed")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Quiz generation should work properly.")
    return True

if __name__ == "__main__":
    success = test_quiz_generation()
    sys.exit(0 if success else 1)
