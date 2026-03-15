from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core_backend.scraper import scrape_url
from core_backend.embedder import process_and_store_documents
import os
from groq import Groq
from core_backend.settings import supabase
from core_backend.embedder import model # Re-using free HuggingFace model

class IngestURLView(APIView):
    def post(self, request):
        url = request.data.get('url')
        
        if not url:
            return Response({"error": "URL is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 1. Scrape the website (limit depth to 1 for hackathon speed)
            print(f"Starting scrape for: {url}")
            scraped_data = scrape_url(url, max_depth=1)
            
            if not scraped_data:
                return Response({"error": "No content scraped. Check URL."}, status=status.HTTP_400_BAD_REQUEST)

            # 2. Chunk, embed, and upload to Supabase
            print("Embedding and uploading to Supabase...")
            process_and_store_documents(scraped_data)
            
            return Response({"message": f"Successfully ingested and embedded {len(scraped_data)} pages from {url}."}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        


# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class ChatQueryView(APIView):
    def post(self, request):
        user_question = request.data.get('question')
        
        if not user_question:
            return Response({"error": "Question is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 1. RETRIEVAL: Convert the question into a vector embedding
            question_embedding = model.encode(user_question).tolist()
            
            # Search Supabase using the SQL function we created earlier
            # Lowering the threshold to 0.1 to ensure we don't filter out good context
            response = supabase.rpc(
                'match_documents', 
                {'query_embedding': question_embedding, 'match_threshold': 0.1, 'match_count': 3}
            ).execute()
            
            relevant_chunks = response.data
            
            if not relevant_chunks:
                return Response({"answer": "I don't have enough information from the scraped website to answer that."}, status=status.HTTP_200_OK)

            # Combine the retrieved text chunks into a single string
            context_text = "\n\n".join([chunk['content'] for chunk in relevant_chunks])
            
            # 2. GENERATION: Send the context and the question to Groq (Llama 3)
            system_prompt = f"""
            You are a helpful AI assistant. Answer the user's question based ONLY on the following context scraped from a website. 
            If the answer is not in the context, say "I cannot find the answer on the provided website."
            
            Context:
            {context_text}
            """
            
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ],
                model="llama-3.1-8b-instant",
            )
            
            final_answer = chat_completion.choices[0].message.content
            
            return Response({"answer": final_answer}, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"CRITICAL CHAT ERROR: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)