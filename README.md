# RAG Chatbot - PDF Q&A & Web Search

A full-featured RAG (Retrieval-Augmented Generation) chatbot with authentication, PDF Q&A, and web search capabilities.

## Features

- **User Authentication**: Sign up and login system with MongoDB storage
- **PDF RAG**: Upload PDF documents and ask questions about their content
- **Web Search**: Ask questions and get answers based on web search results
- **Chat History**: All conversations are stored in MongoDB
- **Full-Screen UI**: Modern tabbed interface with authentication

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Edit `.env` and add your actual credentials:
     - `FLASK_SECRET_KEY`: A secret key for Flask sessions (use a strong random string)
     - `OPENAI_API_KEY`: Your OpenAI API key
     - `MONGODB_URI`: Your MongoDB connection string

3. Run the Flask application:
```bash
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

### Authentication
1. When you first open the page, you'll see a login/signup modal
2. Create an account or login with existing credentials
3. You'll stay logged in until you logout

### PDF RAG Tab
1. Upload a PDF file using the upload section
2. Wait for the PDF to be processed (you'll see a success message)
3. Ask questions about the PDF content in the chat interface
4. The bot will answer based on the PDF content using RAG

### Web Search Tab
1. Switch to the "Web Search" tab
2. Ask any question
3. The bot will search the web and provide an answer based on search results

## Database Schema

### Users Collection
- `_id`: Unique user ID
- `username`: Username
- `email`: Email address
- `password_hash`: Hashed password
- `created_at`: Account creation timestamp

### Chats Collection
- `_id`: Unique chat ID
- `user_id`: Reference to user
- `type`: Either "pdf_rag" or "web_search"
- `message`: User's message
- `response`: Bot's response
- `search_query`: Search query (for web_search type)
- `timestamp`: Chat timestamp

### PDFs Collection
- `_id`: Unique PDF ID
- `user_id`: Reference to user
- `filename`: Original filename
- `chunks_count`: Number of text chunks
- `uploaded_at`: Upload timestamp

## How It Works

### PDF RAG
1. **PDF Upload**: The PDF is uploaded and text is extracted
2. **Chunking**: The text is split into overlapping chunks
3. **Embedding**: Each chunk is converted to a vector embedding using OpenAI's embedding model
4. **Query Processing**: When you ask a question:
   - Your question is converted to an embedding
   - Similar chunks are retrieved using cosine similarity
   - The relevant chunks are used as context for OpenAI's GPT model
   - The model generates an answer based on the context

### Web Search
1. **Query Processing**: Your question is sent to the backend
2. **Web Search**: DuckDuckGo searches the web for relevant results
3. **Context Building**: Top search results are formatted as context
4. **Answer Generation**: OpenAI GPT generates an answer based on the search results

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: MongoDB
- **AI/ML**: OpenAI API (embeddings and chat)
- **Web Search**: DuckDuckGo Search (free, no API key required)
- **PDF Processing**: PyPDF2
- **Vector Similarity**: scikit-learn

## Deployment on Vercel

1. **Install Vercel CLI** (if not already installed):
```bash
npm i -g vercel
```

2. **Login to Vercel**:
```bash
vercel login
```

3. **Set Environment Variables** in Vercel Dashboard or via CLI:
```bash
vercel env add FLASK_SECRET_KEY
vercel env add OPENAI_API_KEY
vercel env add MONGODB_URI
```

4. **Deploy**:
```bash
vercel
```

Or deploy to production:
```bash
vercel --prod
```

**Note**: Make sure to set all three environment variables (`FLASK_SECRET_KEY`, `OPENAI_API_KEY`, `MONGODB_URI`) in your Vercel project settings before deploying.

## Notes

- The application stores PDF embeddings in memory (per user, resets when server restarts)
- Designed for single-user use per session
- Uses OpenAI's `text-embedding-3-small` for embeddings and `gpt-3.5-turbo` for chat
- Web search uses DuckDuckGo which is free and doesn't require an API key
- For Vercel deployment, ensure all environment variables are set in the Vercel dashboard
