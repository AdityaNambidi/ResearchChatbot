from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import os
from dotenv import load_dotenv
import PyPDF2
import io
import openai
from openai import OpenAI
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import json
from datetime import datetime, timezone
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS
import uuid

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback-secret-key-change-in-production')
CORS(app, supports_credentials=True)

# OpenAI API configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")
client = OpenAI(api_key=OPENAI_API_KEY)

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI')
if not MONGODB_URI:
    raise ValueError("MONGODB_URI not found in environment variables")
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client['chatbot']
users_collection = db['users']
chats_collection = db['chats']
pdfs_collection = db['pdfs']

# In-memory storage for PDF chunks and embeddings (per user)
user_pdf_data = {}

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def chunk_text(text, chunk_size=1000, overlap=200):
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks

def get_embeddings(texts):
    """Get embeddings from OpenAI"""
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        print(f"Error getting embeddings: {e}")
        return None

def retrieve_relevant_chunks(user_id, query, top_k=3):
    """Retrieve most relevant chunks based on query"""
    if user_id not in user_pdf_data:
        return []
    
    pdf_data = user_pdf_data[user_id]
    if not pdf_data['loaded'] or len(pdf_data['embeddings']) == 0:
        return []
    
    # Get query embedding
    query_embeddings = get_embeddings([query])
    if not query_embeddings:
        return []
    
    query_embedding = np.array(query_embeddings[0]).reshape(1, -1)
    
    # Calculate similarities
    similarities = cosine_similarity(query_embedding, pdf_data['embeddings'])[0]
    
    # Get top k chunks
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    relevant_chunks = [pdf_data['chunks'][i] for i in top_indices]
    
    return relevant_chunks

def search_web(query, max_results=5):
    """Search the web using DuckDuckGo"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            if not results:
                print(f"No results found for query: {query}")
            return results
    except Exception as e:
        print(f"Error searching web: {e}")
        import traceback
        traceback.print_exc()
        return []

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def require_admin(f):
    """Decorator to require admin authentication"""
    def decorated_function(*args, **kwargs):
        if 'admin' not in session or not session.get('admin'):
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_dashboard():
    return render_template('admin.html')

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    # Check if user already exists
    if users_collection.find_one({'$or': [{'username': username}, {'email': email}]}):
        return jsonify({'error': 'Username or email already exists'}), 400
    
    # Create new user
    user_id = str(uuid.uuid4())
    password_hash = generate_password_hash(password)
    
    user_doc = {
        '_id': user_id,
        'username': username,
        'email': email,
        'password_hash': password_hash,
        'created_at': datetime.now(timezone.utc)
    }
    
    users_collection.insert_one(user_doc)
    
    # Set session
    session['user_id'] = user_id
    session['username'] = username
    
    return jsonify({
        'message': 'Signup successful',
        'user': {'id': user_id, 'username': username}
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    # Find user
    user = users_collection.find_one({'username': username})
    
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Set session
    session['user_id'] = user['_id']
    session['username'] = user['username']
    
    return jsonify({
        'message': 'Login successful',
        'user': {'id': user['_id'], 'username': user['username']}
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    user_id = session.get('user_id')
    if user_id and user_id in user_pdf_data:
        del user_pdf_data[user_id]
    session.clear()
    return jsonify({'message': 'Logout successful'})

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {'id': session['user_id'], 'username': session['username']}
        })
    return jsonify({'authenticated': False})

@app.route('/api/pdf/upload', methods=['POST'])
@require_auth
def upload_pdf():
    user_id = session['user_id']
    
    if 'pdf' not in request.files:
        return jsonify({'error': 'No PDF file provided'}), 400
    
    pdf_file = request.files['pdf']
    if pdf_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_file)
        if not text.strip():
            return jsonify({'error': 'Could not extract text from PDF'}), 400
        
        # Chunk the text
        chunks = chunk_text(text)
        
        # Get embeddings for chunks
        embeddings = get_embeddings(chunks)
        if not embeddings:
            return jsonify({'error': 'Failed to generate embeddings'}), 500
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings)
        
        # Store in memory (per user)
        user_pdf_data[user_id] = {
            'chunks': chunks,
            'embeddings': embeddings_array,
            'loaded': True
        }
        
        # Store PDF metadata in MongoDB
        try:
            pdf_id = str(uuid.uuid4())
            pdf_doc = {
                '_id': pdf_id,
                'user_id': user_id,
                'filename': pdf_file.filename,
                'chunks_count': len(chunks),
                'uploaded_at': datetime.now(timezone.utc)
            }
            result = pdfs_collection.insert_one(pdf_doc)
            print(f"PDF saved to MongoDB: {result.inserted_id}")
        except Exception as e:
            print(f"Error saving PDF to MongoDB: {e}")
            import traceback
            traceback.print_exc()
        
        return jsonify({
            'message': 'PDF uploaded and processed successfully',
            'chunks': len(chunks)
        })
    
    except Exception as e:
        return jsonify({'error': f'Error processing PDF: {str(e)}'}), 500

@app.route('/api/pdf/chat', methods=['POST'])
@require_auth
def pdf_chat():
    user_id = session['user_id']
    
    if user_id not in user_pdf_data or not user_pdf_data[user_id]['loaded']:
        return jsonify({'error': 'Please upload a PDF first'}), 400
    
    data = request.json
    query = data.get('message', '')
    
    if not query:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        # Retrieve relevant chunks
        relevant_chunks = retrieve_relevant_chunks(user_id, query, top_k=3)
        
        if not relevant_chunks:
            return jsonify({'error': 'Could not retrieve relevant information'}), 500
        
        # Create context from relevant chunks
        context = "\n\n".join(relevant_chunks)
        
        # Create prompt for OpenAI
        system_prompt = """You are a helpful assistant that answers questions based on the provided context from a PDF document. 
        Answer the question using only the information from the context. If the answer is not in the context, say "I don't have enough information to answer this question based on the uploaded PDF."
        
        Format your response using markdown:
        - Use **bold** for important terms or key points
        - Use headings (## Heading) to organize different sections
        - Use --- to separate major sections (horizontal rule)
        - Use bullet points (-) for lists
        - Keep paragraphs concise and well-structured
        
        Be concise and accurate."""
        
        user_prompt = f"""Context from PDF:
{context}

Question: {query}

Answer:"""
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        
        # Save chat to MongoDB
        chat_doc = {
            '_id': str(uuid.uuid4()),
            'user_id': user_id,
            'type': 'pdf_rag',
            'message': query,
            'response': answer,
            'timestamp': datetime.now(timezone.utc)
        }
        chats_collection.insert_one(chat_doc)
        
        return jsonify({
            'response': answer
        })
    
    except Exception as e:
        return jsonify({'error': f'Error generating response: {str(e)}'}), 500

@app.route('/api/websearch/chat', methods=['POST'])
@require_auth
def websearch_chat():
    user_id = session['user_id']
    
    data = request.json
    query = data.get('message', '')
    
    if not query:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        # Search the web
        search_results = search_web(query, max_results=5)
        
        if not search_results:
            # If no search results, still try to answer using OpenAI with a note
            system_prompt = """You are a helpful assistant. The web search did not return results, but try to provide a helpful answer based on your knowledge. If you cannot provide accurate information, let the user know.
            
            Format your response using markdown:
            - Use **bold** for important terms or key points
            - Use headings (## Heading) to organize different sections
            - Use --- to separate major sections (horizontal rule)
            - Use bullet points (-) for lists
            - Keep paragraphs concise and well-structured"""
            
            user_prompt = f"""Question: {query}

Please provide a helpful answer. Note that web search results were not available."""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            
            # Save chat to MongoDB
            chat_doc = {
                '_id': str(uuid.uuid4()),
                'user_id': user_id,
                'type': 'web_search',
                'message': query,
                'response': answer,
                'search_query': query,
                'timestamp': datetime.now(timezone.utc)
            }
            chats_collection.insert_one(chat_doc)
            
            return jsonify({
                'response': answer
            })
        
        # Format search results as context
        context_parts = []
        for i, result in enumerate(search_results, 1):
            title = result.get('title', '')
            body = result.get('body', '')
            url = result.get('href', '')
            context_parts.append(f"Result {i}:\nTitle: {title}\nContent: {body}\nURL: {url}")
        
        context = "\n\n".join(context_parts)
        
        # Create prompt for OpenAI
        system_prompt = """You are a helpful assistant that answers questions based on web search results. 
        Use the search results provided to answer the user's question. Cite sources when relevant.
        
        Format your response using markdown:
        - Use **bold** for important terms or key points
        - Use headings (## Heading) to organize different sections
        - Use --- to separate major sections (horizontal rule)
        - Use bullet points (-) for lists
        - Keep paragraphs concise and well-structured
        
        Be concise and accurate."""
        
        user_prompt = f"""Web Search Results:
{context}

Question: {query}

Answer:"""
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        
        # Save chat to MongoDB
        chat_doc = {
            '_id': str(uuid.uuid4()),
            'user_id': user_id,
            'type': 'web_search',
            'message': query,
            'response': answer,
            'search_query': query,
            'timestamp': datetime.now(timezone.utc)
        }
        chats_collection.insert_one(chat_doc)
        
        return jsonify({
            'response': answer
        })
    
    except Exception as e:
        return jsonify({'error': f'Error generating response: {str(e)}'}), 500

@app.route('/api/chats/history', methods=['GET'])
@require_auth
def get_chat_history():
    user_id = session['user_id']
    chat_type = request.args.get('type', 'all')  # 'pdf_rag', 'web_search', or 'all'
    
    query = {'user_id': user_id}
    if chat_type != 'all':
        query['type'] = chat_type
    
    chats = list(chats_collection.find(query).sort('timestamp', -1).limit(50))
    
    # Convert ObjectId to string
    for chat in chats:
        chat['_id'] = str(chat['_id'])
        chat['timestamp'] = chat['timestamp'].isoformat()
    
    return jsonify({'chats': chats})

# Admin endpoints
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if username == 'admin' and password == 'admin':
        session['admin'] = True
        session['admin_username'] = 'admin'
        return jsonify({'message': 'Admin login successful'})
    
    return jsonify({'error': 'Invalid admin credentials'}), 401

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin', None)
    session.pop('admin_username', None)
    return jsonify({'message': 'Admin logout successful'})

@app.route('/api/admin/status', methods=['GET'])
def admin_status():
    if 'admin' in session and session.get('admin'):
        return jsonify({'authenticated': True, 'username': session.get('admin_username')})
    return jsonify({'authenticated': False})

@app.route('/api/admin/users', methods=['GET'])
@require_admin
def get_all_users():
    users = list(users_collection.find({}, {'password_hash': 0}).sort('created_at', -1))
    
    for user in users:
        user['_id'] = str(user['_id'])
        user['created_at'] = user['created_at'].isoformat()
    
    return jsonify({'users': users})

@app.route('/api/admin/users/<user_id>/pdfs', methods=['GET'])
@require_admin
def get_user_pdfs(user_id):
    try:
        pdfs = list(pdfs_collection.find({'user_id': user_id}).sort('uploaded_at', -1))
        print(f"Found {len(pdfs)} PDFs for user {user_id}")
        
        for pdf in pdfs:
            pdf['_id'] = str(pdf['_id'])
            if 'uploaded_at' in pdf:
                pdf['uploaded_at'] = pdf['uploaded_at'].isoformat()
        
        return jsonify({'pdfs': pdfs})
    except Exception as e:
        print(f"Error fetching PDFs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'pdfs': []}), 500

@app.route('/api/admin/users/<user_id>/chats', methods=['GET'])
@require_admin
def get_user_chats(user_id):
    chats = list(chats_collection.find({'user_id': user_id}).sort('timestamp', -1))
    
    for chat in chats:
        chat['_id'] = str(chat['_id'])
        chat['timestamp'] = chat['timestamp'].isoformat()
    
    return jsonify({'chats': chats})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
