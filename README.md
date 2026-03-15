# RAG-Powered Website Chatbot 🤖🌐

A full-stack application that allows users to input any URL, extract its content, and have a conversational Q&A with that specific text using Retrieval-Augmented Generation (RAG). 

Built as a lean MVP for hackathon demonstration.

## 🚀 Tech Stack
* **Frontend:** React.js
* **Backend:** Python / Django
* **Database & Vector Store:** Supabase (PostgreSQL with `pgvector`)
* **AI/LLM Core:** Embeddings and generation mapping to scraped context.

## 🧠 How it Works (MVP Flow)
1. **Ingest:** User submits a URL via the React frontend.
2. **Process:** The Django backend scrapes the site, chunks the text, and generates vector embeddings.
3. **Store:** Embeddings are stored in Supabase using `pgvector`.
4. **Retrieve & Chat:** User queries are embedded and mapped against the Supabase vector store via similarity search. The top matching context is passed to the LLM to generate an accurate, hallucination-free answer.

## 🛠️ Local Setup Instructions

### Prerequisites
* Python 3.9+
* Node.js & npm
* A Supabase project (with pgvector extension enabled)

### Backend (Django)
1. Navigate to the root directory.
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment: 
   * Windows: `venv\Scripts\activate`
   * Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up your `.env` variables for Supabase and your LLM API keys.
6. Run the server: `python manage.py runserver`

### Frontend (React)
1. Open a new terminal and navigate to the frontend folder: `cd frontend`
2. Install packages: `npm install`
3. Start the development server: `npm start`
4. The app will open at `http://localhost:3000`