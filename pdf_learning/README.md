# PDF Learning Assistant

An interactive Django application that generates multiple choice questions from PDF documents using AI and provides a chatbot for document-based Q&A.

## Features

- **PDF Upload & Processing**: Upload PDF documents and extract text content
- **AI-Powered MCQ Generation**: Generate multiple choice questions based on specific topics or page ranges
- **Interactive Quizzes**: Take quizzes with real-time progress tracking and detailed results
- **AI Chatbot**: Ask questions about document content using RAG (Retrieval Augmented Generation)
- **Open Source**: Uses only free and open-source tools

## Technology Stack

- **Backend**: Django 4.2
- **AI Model**: Gemma 2B (via Ollama)
- **Vector Database**: ChromaDB
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **PDF Processing**: PyPDF2
- **Frontend**: Bootstrap 5, Vanilla JavaScript

## Prerequisites

1. Python 3.8+
2. Ollama installed and running
3. Gemma 2B model downloaded

## Installation

1. **Clone the repository**
   \`\`\`bash
   git clone <repository-url>
   cd mcq_generator.app
   \`\`\`

2. **Install Ollama**
   - Visit https://ollama.ai and install Ollama
   - Start Ollama service: `ollama serve`
   - Download Gemma 2B: `ollama pull gemma2:2b`

3. **Set up Python environment**
   \`\`\`bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   \`\`\`

4. **Set up Django**
   \`\`\`bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser  # Optional
   \`\`\`

5. **Create required directories**
   \`\`\`bash
   mkdir -p media/pdfs
   mkdir -p chroma_db
   \`\`\`

## Usage

1. **Start the application**
   \`\`\`bash
   # Make sure Ollama is running
   ollama serve
   
   # Start Django development server
   python manage.py runserver
   \`\`\`

2. **Access the application**
   - Open http://127.0.0.1:8000 in your browser

3. **Upload a PDF**
   - Click "Upload New PDF" on the home page
   - Select a PDF file and provide a title
   - Wait for processing to complete

4. **Create a Quiz**
   - Go to document details
   - Click "Create New Quiz"
   - Specify topic, page range, and number of questions
   - Take the generated quiz

5. **Chat with AI**
   - Click "Chat with AI" from document details
   - Ask questions about the document content

## Key Components

### AI Service (`ai_service.py`)
- Handles Gemma 2B integration via Ollama
- Implements RAG for context retrieval
- Generates MCQ questions with prompt engineering
- Provides chatbot functionality

### PDF Processor (`pdf_processor.py`)
- Extracts text from PDF files
- Chunks text for vector storage
- Handles page range parsing

### Models
- **PDFDocument**: Stores uploaded PDF metadata
- **QuizSession**: Tracks quiz attempts
- **Question**: Individual quiz questions
- **ChatMessage**: Chat history

## Prompt Engineering

The application uses carefully crafted prompts to:
- Generate high-quality multiple choice questions
- Avoid hallucinations in chatbot responses
- Ensure answers are based only on document content
- Provide clear explanations

## Configuration

Key settings in `settings.py`:
- `CHROMA_DB_PATH`: Vector database location
- `MAX_FILE_SIZE`: Maximum PDF file size (10MB)

## Troubleshooting

1. **Ollama Connection Issues**
   - Ensure Ollama is running: `ollama serve`
   - Check if Gemma 2B is available: `ollama list`

2. **PDF Processing Errors**
   - Ensure PDF is not password protected
   - Check file size limits

3. **Vector Database Issues**
   - Delete `chroma_db` folder and restart

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Ollama for local AI model serving
- ChromaDB for vector storage
- Sentence Transformers for embeddings
- Django community for the excellent framework
