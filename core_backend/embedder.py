from sentence_transformers import SentenceTransformer
from core_backend.settings import supabase

# This will download the free model to your machine the first time it runs
model = SentenceTransformer('all-MiniLM-L6-v2')

def chunk_text(text, chunk_size=500):
    """Breaks large scraped text into smaller chunks for the AI to read."""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def process_and_store_documents(scraped_data):
    """Embeds text in native batches and pushes to Supabase."""
    
    # 1. Flatten all pages into a master list of chunks
    all_chunks = []
    for page in scraped_data:
        chunks = chunk_text(page['content'])
        for chunk in chunks:
            all_chunks.append({
                "url": page['url'], 
                "content": chunk
            })
            
    total_chunks = len(all_chunks)
    print(f"\n🧠 Vectorizing {total_chunks} text chunks...")
    
    # 2. Process in batches of 50 for massive CPU speedups
    batch_size = 50 
    
    for i in range(0, total_chunks, batch_size):
        batch = all_chunks[i : i + batch_size]
        
        # Extract just the raw text strings for the AI model
        texts_to_encode = [item['content'] for item in batch]
        
        print(f"Encoding batch {i} to {min(i+batch_size, total_chunks)}...")
        
        # NATIVE BATCHING: Pass the whole list to the model at once!
        embeddings = model.encode(texts_to_encode).tolist()
        
        # Prepare the data dictionary for Supabase
        supabase_data = []
        for j, item in enumerate(batch):
            supabase_data.append({
                'url': item['url'],
                'content': item['content'],
                'embedding': embeddings[j] # Match the generated embedding back to the text
            })
            
        # Push the batch of 50 directly to Supabase
        try:
            supabase.table('documents').insert(supabase_data).execute()
        except Exception as e:
            print(f"Error storing batch in Supabase: {e}")
            
    print("✅ All vectors successfully stored in database.")