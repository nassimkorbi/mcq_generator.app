import os
import json
import re
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import requests
from django.conf import settings

class AIService:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.PersistentClient(path=str(settings.CHROMA_DB_PATH))
        self.ollama_url = "http://localhost:11434"
        
    def create_collection(self, document_id: str):
        """Create a new collection for a document"""
        collection_name-= f"doc_{document_id}".replace('-', '_')
        try:
            collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            return collection
        except Exception as e:
            # Collection might already exist
            return self.chroma_client.get_collection(name=collection_name)
    
    def add_text_chunks(self, document_id: str, text_chunks: List[str], page_numbers: List[int]):
        """Add text chunks to the vector database"""
        collection = self.create_collection(document_id)
        
        embeddings = self.embedding_model.encode(text_chunks).tolist()
        
        ids = [f"chunk_{i}" for i in range(len(text_chunks))]
        metadatas = [{"page": page_num, "chunk_id": i} for i, page_num in enumerate(page_numbers)]
        
        collection.add(
            embeddings=embeddings,
            documents=text_chunks,
            metadatas=metadatas,
            ids=ids
        )
    
    def retrieve_relevant_context(self, document_id: str, query: str, n_results: int = 5) -> List[str]:
        """Retrieve relevant context for a query"""
        collection_name = f"doc_{document_id}".replace('-', '_')
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=n_results
            )
            
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return []
    
    def call_gemma(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call Gemma 2B via Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "gemma2:2b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature for more consistent output
                        "top_p": 0.8,
                        "num_predict": max_tokens
                    }
                },
                timeout=120  # Increased timeout
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                print(f"Ollama API error: {response.status_code}")
                return "Error: Could not generate response"
                
        except Exception as e:
            print(f"Error calling Gemma: {e}")
            return "Error: AI service unavailable"
    
    def generate_single_mcq(self, context: str, topic: str = "") -> Dict:
        """Generate a single MCQ question using a simpler approach"""
        
        # Simple, focused prompt for single question generation
        prompt = f"""Based on the following text, create ONE multiple choice question.

TEXT:
{context[:1500]}  # Limit context to avoid token limits

TOPIC FOCUS: {topic if topic else "main concepts"}

Create a question in this EXACT format:

QUESTION: [Write your question here]
A) [First option]
B) [Second option] 
C) [Third option]
D) [Fourth option]
ANSWER: [A, B, C, or D]
EXPLANATION: [Brief explanation why this answer is correct]

Make sure:
- Question tests understanding, not just memory
- Only ONE option is clearly correct
- Other options are plausible but wrong
- Base everything on the provided text only

Generate the question now:"""

        response = self.call_gemma(prompt, max_tokens=500)
        return self.parse_single_mcq(response)
    
    def parse_single_mcq(self, response: str) -> Dict:
        """Parse a single MCQ response"""
        try:
            question_data = {
                'question_text': '',
                'options': {},
                'correct_answer': '',
                'explanation': ''
            }
            
            lines = response.strip().split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('QUESTION:'):
                    question_data['question_text'] = line.replace('QUESTION:', '').strip()
                elif line.startswith('A)'):
                    question_data['options']['A'] = line[2:].strip()
                elif line.startswith('B)'):
                    question_data['options']['B'] = line[2:].strip()
                elif line.startswith('C)'):
                    question_data['options']['C'] = line[2:].strip()
                elif line.startswith('D)'):
                    question_data['options']['D'] = line[2:].strip()
                elif line.startswith('ANSWER:'):
                    answer = line.replace('ANSWER:', '').strip()
                    # Extract just the letter
                    for letter in ['A', 'B', 'C', 'D']:
                        if letter in answer:
                            question_data['correct_answer'] = letter
                            break
                elif line.startswith('EXPLANATION:'):
                    question_data['explanation'] = line.replace('EXPLANATION:', '').strip()
            
            # Validate the question
            if (question_data['question_text'] and 
                len(question_data['options']) == 4 and 
                question_data['correct_answer'] in ['A', 'B', 'C', 'D']):
                return question_data
            else:
                print(f"Invalid question data: {question_data}")
                return None
                
        except Exception as e:
            print(f"Error parsing MCQ: {e}")
            return None
    
    def generate_mcq_questions(self, document_id: str, topic: str = "", page_range: str = "", num_questions: int = 5) -> List[Dict]:
        """Generate multiple choice questions using iterative approach"""
        
        print(f"Starting MCQ generation for document {document_id}")
        print(f"Topic: '{topic}', Page range: '{page_range}', Num questions: {num_questions}")
        
        # Get relevant context
        search_queries = []
        if topic:
            search_queries.append(topic)
            search_queries.append(f"key concepts about {topic}")
        else:
            search_queries.extend([
                "main concepts and key points",
                "important information and definitions",
                "fundamental principles and ideas"
            ])
        
        # Collect context from multiple searches
        all_context_chunks = []
        for query in search_queries:
            chunks = self.retrieve_relevant_context(document_id, query, n_results=6)
            all_context_chunks.extend(chunks)
        
        # Remove duplicates and limit
        unique_chunks = list(dict.fromkeys(all_context_chunks))[:10]
        
        if not unique_chunks:
            print("No context chunks retrieved")
            return []
        
        print(f"Retrieved {len(unique_chunks)} context chunks")
        
        # Generate questions one by one using different context chunks
        questions = []
        max_attempts = num_questions * 3  # Allow multiple attempts
        attempts = 0
        
        for i in range(num_questions):
            if attempts >= max_attempts:
                break
                
            # Use different context chunks for variety
            context_chunk = unique_chunks[i % len(unique_chunks)]
            
            print(f"Generating question {i+1}/{num_questions} (attempt {attempts+1})")
            
            try:
                question = self.generate_single_mcq(context_chunk, topic)
                if question:
                    # Check for duplicates
                    is_duplicate = any(
                        self.questions_similar(question['question_text'], existing['question_text']) 
                        for existing in questions
                    )
                    
                    if not is_duplicate:
                        questions.append(question)
                        print(f"Successfully generated question {len(questions)}")
                    else:
                        print(f"Duplicate question detected, skipping")
                else:
                    print(f"Failed to generate valid question")
                    
            except Exception as e:
                print(f"Error generating question {i+1}: {e}")
            
            attempts += 1
        
        print(f"Generated {len(questions)} questions total")
        return questions
    
    def questions_similar(self, q1: str, q2: str) -> bool:
        """Check if two questions are too similar"""
        # Simple similarity check
        q1_words = set(q1.lower().split())
        q2_words = set(q2.lower().split())
        
        if len(q1_words) == 0 or len(q2_words) == 0:
            return False
            
        intersection = len(q1_words.intersection(q2_words))
        union = len(q1_words.union(q2_words))
        
        similarity = intersection / union if union > 0 else 0
        return similarity > 0.7  # 70% similarity threshold
    
    def answer_question(self, document_id: str, question: str) -> str:
        """Answer a question using RAG - this already works well"""
        
        # Retrieve relevant context
        context_chunks = self.retrieve_relevant_context(document_id, question, n_results=5)
        context = "\n\n".join(context_chunks)
        
        if not context.strip():
            return "I don't have enough information from the document to answer this question."
        
        # Prompt engineering for accurate answers
        prompt = f"""You are a helpful AI assistant answering questions based on a document.

CONTEXT FROM DOCUMENT:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Answer the question based ONLY on the provided context
2. If the context doesn't contain enough information, say so clearly
3. Be concise but comprehensive
4. Cite specific parts of the context when relevant
5. Do not make assumptions or add information not in the context

ANSWER:
"""

        return self.call_gemma(prompt, max_tokens=500)
    
    def evaluate_answer(self, question_text: str, correct_answer: str, user_answer: str, options: Dict) -> Dict:
        """Evaluate user's answer and provide feedback"""
        is_correct = user_answer.upper() == correct_answer.upper()
        
        feedback = {
            'is_correct': is_correct,
            'message': '',
            'correct_option': options.get(correct_answer, ''),
            'user_option': options.get(user_answer, '')
        }
        
        if is_correct:
            feedback['message'] = "Correct! Well done."
        else:
            feedback['message'] = f"Incorrect. The correct answer is {correct_answer}: {feedback['correct_option']}"
        
        return feedback
    
    def test_connection(self) -> bool:
        """Test if the AI service is working"""
        try:
            response = self.call_gemma("Hello, respond with 'OK' if you can hear me.", max_tokens=10)
            return "OK" in response or "ok" in response.lower()
        except:
            return False
