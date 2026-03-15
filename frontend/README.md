# Frontend: RAG Chatbot UI

This directory contains the React.js user interface for the RAG-Powered Website Chatbot. It provides a simple, intuitive chat interface for users to input URLs and ask questions.

## Available Scripts

In the project directory, you can run:

### `npm install`
Installs all required dependencies. Run this before starting the application for the first time.

### `npm start`
Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

## API Connection
By default, this frontend expects the Django backend to be running locally on `http://127.0.0.1:8000/`. Ensure your Django server is active and CORS is configured properly to accept requests from localhost:3000.