from django.core.management.base import BaseCommand
from learning_app.ai_service import AIService
from learning_app.models import PDFDocument

class Command(BaseCommand):
    help = 'Test quiz generation functionality'

    def handle(self, *args, **options):
        self.stdout.write("🧪 Testing Quiz Generation System")
        self.stdout.write("=" * 50)
        
        # Test AI Service
        ai_service = AIService()
        
        if ai_service.test_connection():
            self.stdout.write(self.style.SUCCESS("✅ AI service connection successful"))
        else:
            self.stdout.write(self.style.ERROR("❌ AI service connection failed"))
            return
        
        # Test with first available document
        documents = PDFDocument.objects.filter(processed=True)
        if not documents.exists():
            self.stdout.write(self.style.ERROR("❌ No processed documents found"))
            return
        
        document = documents.first()
        self.stdout.write(f"✅ Testing with document: {document.title}")
        
        # Test question generation
        questions = ai_service.generate_mcq_questions(
            str(document.id), 
            topic="", 
            page_range="", 
            num_questions=2
        )
        
        if questions:
            self.stdout.write(self.style.SUCCESS(f"✅ Generated {len(questions)} questions"))
            for i, q in enumerate(questions, 1):
                self.stdout.write(f"Q{i}: {q['question_text'][:60]}...")
        else:
            self.stdout.write(self.style.ERROR("❌ Question generation failed"))
