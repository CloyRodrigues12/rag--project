from sentence_transformers import SentenceTransformer
from core_backend.settings import supabase # Make sure this imports your supabase client

# This will download the free model to your machine the first time it runs
model = SentenceTransformer('all-MiniLM-L6-v2')

def chunk_text(text, chunk_size=500):
    """Breaks large scraped text into smaller chunks for the AI to read."""
    # A simple character-based chunker. 
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def process_and_store_documents(scraped_data):
    """Embeds the text and pushes it to Supabase in batches."""
    batch_data = []
    
    for page in scraped_data:
        chunks = chunk_text(page['content'])
        
        for chunk in chunks:
            embedding = model.encode(chunk).tolist()
            batch_data.append({
                'url': page['url'],
                'content': chunk,
                'embedding': embedding
            })
            
            # When we get 10 chunks, send them all at once
            if len(batch_data) >= 10:
                try:
                    supabase.table('documents').insert(batch_data).execute()
                    print(f"Successfully stored batch of 10 vectors.")
                except Exception as e:
                    print(f"Error storing batch: {e}")
                batch_data = [] # Clear the batch
                
    # Push any leftover chunks
    if batch_data:
        try:
            supabase.table('documents').insert(batch_data).execute()
            print(f"Successfully stored final batch of {len(batch_data)} vectors.")
        except Exception as e:
            print(f"Error storing final batch: {e}")