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
        # Look for the new mode parameter (default to 'full' if not provided)
        mode = request.data.get('mode', 'full') 
        
        if not url:
            return Response({"error": "URL is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # If 'single' page is selected, stop after 1 page. Otherwise, do 20.
            max_pages = 1 if mode == 'single' else 20
            
            print(f"Starting scrape for: {url} in '{mode}' mode (Max Pages: {max_pages})")
            scraped_data = scrape_url(url, max_pages=max_pages)
            
            if not scraped_data:
                return Response({"error": "No content scraped. Check URL."}, status=status.HTTP_400_BAD_REQUEST)

            print("Embedding and uploading to Supabase...")
            process_and_store_documents(scraped_data)
            
            return Response({"message": f"Successfully ingested and embedded {len(scraped_data)} pages from {url}."}, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"CRITICAL INGEST ERROR: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    


# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class ChatQueryView(APIView):
    def post(self, request):
        user_question = request.data.get('question')
        chat_history = request.data.get('history', [])
        
        if not user_question:
            return Response({"error": "Question is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 1. THE MAGIC: Context-Aware Query Expansion (ONLY if history exists)
            if chat_history:
                recent_history = chat_history[-4:]
                history_text = "\n".join([f"{msg['role'].upper()}: {msg['text']}" for msg in recent_history])

                expansion_prompt = f"""
                You are a query optimizer. Read the chat history, then rewrite the Latest Question into a standalone, detailed search query. 
                If the Latest Question uses pronouns like 'it', 'he', 'she', or 'they', figure out what it refers to from the Chat History and replace the pronoun with the actual noun.
                
                Chat History:
                {history_text}
                
                Latest Question: '{user_question}'
                
                Return ONLY the rewritten standalone query, no other text.
                """
                
                expansion_response = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": expansion_prompt}],
                    model="llama-3.1-8b-instant",
                )
                optimized_query = expansion_response.choices[0].message.content.strip()
                print(f"Optimized Memory Search: {optimized_query}")
            else:
                # If it's the first question, just use the original question!
                optimized_query = user_question
                print(f"First Question (No Memory Needed): {optimized_query}")
            
            # 2. RETRIEVAL: Search the database
            question_embedding = model.encode(optimized_query).tolist()
            
            response = supabase.rpc(
                'match_documents', 
                {'query_embedding': question_embedding, 'match_threshold': 0.1, 'match_count': 5}
            ).execute()
            
            relevant_chunks = response.data
            
            if not relevant_chunks:
                return Response({"answer": "I don't have enough information from the scraped website to answer that."}, status=status.HTTP_200_OK)

            context_text = "\n\n".join([chunk['content'] for chunk in relevant_chunks])
            
            # 3. GENERATION: Build the final memory array for Groq
            system_prompt = f"""
            You are a helpful AI assistant. Answer the user's question based ONLY on the following context scraped from a website. 
            If the answer is not in the context, say "I cannot find the answer on the provided website."
            
            Context:
            {context_text}
            """
            
            messages_for_llm = [{"role": "system", "content": system_prompt}]
            
            for msg in chat_history[-4:]:
                role = "assistant" if msg['role'] == "ai" else "user"
                messages_for_llm.append({"role": role, "content": msg['text']})
                
            messages_for_llm.append({"role": "user", "content": user_question})
            
            chat_completion = groq_client.chat.completions.create(
                messages=messages_for_llm,
                model="llama-3.1-8b-instant",
            )
            
            final_answer = chat_completion.choices[0].message.content
            
            return Response({"answer": final_answer}, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"CRITICAL CHAT ERROR: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)