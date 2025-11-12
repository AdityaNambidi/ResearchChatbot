let pdfUploaded = false;
let currentTab = 'pdf';

// Check authentication status on page load
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
});

function checkAuthStatus() {
    fetch('/api/auth/status', {
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.authenticated) {
            showMainApp(data.user.username);
        } else {
            showAuthModal();
        }
    })
    .catch(error => {
        console.error('Error checking auth status:', error);
        showAuthModal();
    });
}

function showAuthModal() {
    document.getElementById('authModal').style.display = 'flex';
    document.getElementById('mainApp').style.display = 'none';
}

function showMainApp(username) {
    document.getElementById('authModal').style.display = 'none';
    document.getElementById('mainApp').style.display = 'flex';
    document.getElementById('usernameDisplay').textContent = username;
    // Load chat history for the active tab (PDF by default)
    loadChatHistory('pdf_rag');
    // Also load web search history in background
    loadChatHistory('web_search');
}

function switchAuthTab(tab) {
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    const tabs = document.querySelectorAll('.auth-tab');
    
    tabs.forEach(t => t.classList.remove('active'));
    
    if (tab === 'login') {
        loginForm.style.display = 'block';
        signupForm.style.display = 'none';
        tabs[0].classList.add('active');
    } else {
        loginForm.style.display = 'none';
        signupForm.style.display = 'block';
        tabs[1].classList.add('active');
    }
    
    // Clear errors
    document.getElementById('loginError').textContent = '';
    document.getElementById('signupError').textContent = '';
}

function signup() {
    const username = document.getElementById('signupUsername').value.trim();
    const email = document.getElementById('signupEmail').value.trim();
    const password = document.getElementById('signupPassword').value;
    const errorDiv = document.getElementById('signupError');
    
    if (!username || !email || !password) {
        errorDiv.textContent = 'All fields are required';
        return;
    }
    
    fetch('/api/auth/signup', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ username, email, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            errorDiv.textContent = data.error;
        } else {
            showMainApp(data.user.username);
        }
    })
    .catch(error => {
        errorDiv.textContent = 'Error: ' + error.message;
    });
}

function login() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');
    
    if (!username || !password) {
        errorDiv.textContent = 'Username and password are required';
        return;
    }
    
    fetch('/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            errorDiv.textContent = data.error;
        } else {
            showMainApp(data.user.username);
        }
    })
    .catch(error => {
        errorDiv.textContent = 'Error: ' + error.message;
    });
}

function logout() {
    fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        pdfUploaded = false;
        document.getElementById('pdfChatMessages').innerHTML = '';
        document.getElementById('webChatMessages').innerHTML = '';
        showAuthModal();
    })
    .catch(error => {
        console.error('Error logging out:', error);
    });
}

function switchTab(tab) {
    currentTab = tab;
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(t => t.classList.remove('active'));
    tabContents.forEach(tc => tc.classList.remove('active'));
    
    if (tab === 'pdf') {
        tabs[0].classList.add('active');
        document.getElementById('pdfTab').classList.add('active');
        loadChatHistory('pdf_rag');
    } else {
        tabs[1].classList.add('active');
        document.getElementById('websearchTab').classList.add('active');
        loadChatHistory('web_search');
    }
}

function uploadPDF() {
    const fileInput = document.getElementById('pdfInput');
    const uploadStatus = document.getElementById('uploadStatus');
    
    if (!fileInput.files || fileInput.files.length === 0) {
        showUploadStatus('Please select a PDF file', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('pdf', fileInput.files[0]);
    
    uploadStatus.textContent = 'Uploading and processing PDF...';
    uploadStatus.className = '';
    uploadStatus.style.display = 'block';
    
    fetch('/api/pdf/upload', {
        method: 'POST',
        credentials: 'include',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showUploadStatus(data.error, 'error');
        } else {
            showUploadStatus(`PDF uploaded successfully! Processed ${data.chunks} chunks.`, 'success');
            pdfUploaded = true;
            addBotMessage('pdf', 'PDF uploaded successfully! You can now ask questions about it.');
        }
    })
    .catch(error => {
        showUploadStatus('Error uploading PDF: ' + error.message, 'error');
    });
}

function showUploadStatus(message, type) {
    const uploadStatus = document.getElementById('uploadStatus');
    uploadStatus.textContent = message;
    uploadStatus.className = type;
    uploadStatus.style.display = 'block';
}

function sendPDFMessage() {
    const userInput = document.getElementById('pdfUserInput');
    const message = userInput.value.trim();
    
    if (!message) return;
    
    if (!pdfUploaded) {
        addBotMessage('pdf', 'Please upload a PDF first before asking questions.');
        return;
    }
    
    addUserMessage('pdf', message);
    userInput.value = '';
    
    const loadingId = addBotMessage('pdf', 'Thinking...', true);
    
    fetch('/api/pdf/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        removeMessage(loadingId);
        
        if (data.error) {
            addBotMessage('pdf', 'Error: ' + data.error);
        } else {
            addBotMessage('pdf', data.response);
        }
    })
    .catch(error => {
        removeMessage(loadingId);
        addBotMessage('pdf', 'Error: ' + error.message);
    });
}

function sendWebMessage() {
    const userInput = document.getElementById('webUserInput');
    const message = userInput.value.trim();
    
    if (!message) return;
    
    addUserMessage('web', message);
    userInput.value = '';
    
    const loadingId = addBotMessage('web', 'Searching the web...', true);
    
    fetch('/api/websearch/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        removeMessage(loadingId);
        
        if (data.error) {
            addBotMessage('web', 'Error: ' + data.error);
        } else {
            addBotMessage('web', data.response);
        }
    })
    .catch(error => {
        removeMessage(loadingId);
        addBotMessage('web', 'Error: ' + error.message);
    });
}

function handleKeyPress(event, type) {
    if (event.key === 'Enter') {
        if (type === 'pdf') {
            sendPDFMessage();
        } else {
            sendWebMessage();
        }
    }
}

function addUserMessage(type, message) {
    const chatMessages = type === 'pdf' 
        ? document.getElementById('pdfChatMessages')
        : document.getElementById('webChatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    messageDiv.innerHTML = `<div class="message-label">You:</div><div>${escapeHtml(message)}</div>`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addBotMessage(type, message, isLoading = false) {
    const chatMessages = type === 'pdf' 
        ? document.getElementById('pdfChatMessages')
        : document.getElementById('webChatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    const messageId = 'msg-' + Date.now() + '-' + Math.random();
    messageDiv.id = messageId;
    
    if (isLoading) {
        messageDiv.innerHTML = `<div class="message-label">Research Chatbot:</div><div class="message-content">${escapeHtml(message)}<span class="loading"></span></div>`;
    } else {
        messageDiv.innerHTML = `<div class="message-label">Research Chatbot:</div><div class="message-content markdown">${renderMarkdown(message)}</div>`;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageId;
}

function removeMessage(messageId) {
    const messageDiv = document.getElementById(messageId);
    if (messageDiv) {
        messageDiv.remove();
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function renderMarkdown(text) {
    if (!text) return '';
    
    // Process markdown patterns first (before escaping HTML)
    let html = text;
    
    // Code blocks first (to avoid processing markdown inside code)
    const codeBlocks = [];
    html = html.replace(/```([\s\S]*?)```/g, (match, code) => {
        const id = `CODE_BLOCK_${codeBlocks.length}`;
        codeBlocks.push(escapeHtml(code));
        return id;
    });
    
    // Inline code
    const inlineCodes = [];
    html = html.replace(/`([^`\n]+)`/g, (match, code) => {
        const id = `INLINE_CODE_${inlineCodes.length}`;
        inlineCodes.push(escapeHtml(code));
        return id;
    });
    
    // Headings (process from largest to smallest)
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // Horizontal rule (---)
    html = html.replace(/^---$/gim, '<hr class="markdown-hr">');
    
    // Bold (**text**) - process first to avoid conflicts
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Italic (*text*) - process after bold, matching single asterisks
    html = html.replace(/(^|[^*])\*([^*\n]+?)\*([^*]|$)/g, '$1<em>$2</em>$3');
    
    // Links [text](url)
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    
    // Bullet points (- item) - process line by line
    const lines = html.split('\n');
    const processedLines = [];
    let inList = false;
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line.match(/^- (.+)$/)) {
            if (!inList) {
                processedLines.push('<ul>');
                inList = true;
            }
            processedLines.push(`<li>${line.substring(2)}</li>`);
        } else {
            if (inList) {
                processedLines.push('</ul>');
                inList = false;
            }
            processedLines.push(line);
        }
    }
    if (inList) {
        processedLines.push('</ul>');
    }
    html = processedLines.join('\n');
    
    // Numbered lists (1. item)
    html = html.replace(/^\d+\. (.+)$/gim, '<li>$1</li>');
    // Wrap consecutive numbered list items
    html = html.replace(/(<li>.*<\/li>\n?)+/g, (match) => {
        if (match.includes('<ul>') || match.includes('</ul>')) return match;
        return '<ol>' + match + '</ol>';
    });
    
    // Restore code blocks
    codeBlocks.forEach((code, index) => {
        html = html.replace(`CODE_BLOCK_${index}`, `<pre><code>${code}</code></pre>`);
    });
    
    // Restore inline codes
    inlineCodes.forEach((code, index) => {
        html = html.replace(`INLINE_CODE_${index}`, `<code class="inline-code">${code}</code>`);
    });
    
    // Escape remaining HTML (but keep our markdown HTML)
    // Split by our HTML tags, escape text parts
    const parts = html.split(/(<[^>]+>)/);
    html = parts.map(part => {
        if (part.match(/^<[^>]+>$/)) {
            return part; // Keep HTML tags
        }
        return escapeHtml(part); // Escape text
    }).join('');
    
    // Line breaks (double newline = paragraph)
    html = html.split('\n\n').map(para => {
        para = para.trim();
        if (!para) return '';
        // Don't wrap if it's already a block element
        if (para.match(/^<(h[1-6]|ul|ol|pre|hr|p)/)) {
            return para;
        }
        return '<p>' + para + '</p>';
    }).join('');
    
    // Single line breaks (but not inside pre tags)
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

function loadChatHistory(type = 'all') {
    fetch(`/api/chats/history?type=${type}`, {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.chats && data.chats.length > 0) {
            // Sort by timestamp (oldest first for display)
            const sortedChats = data.chats.sort((a, b) => 
                new Date(a.timestamp) - new Date(b.timestamp)
            );
            
            if (type === 'all') {
                // Load both PDF and Web Search chats
                const pdfChats = sortedChats.filter(chat => chat.type === 'pdf_rag');
                const webChats = sortedChats.filter(chat => chat.type === 'web_search');
                
                renderChatHistory('pdf', pdfChats);
                renderChatHistory('web', webChats);
                
                // If there are PDF chats, set pdfUploaded to true
                if (pdfChats.length > 0) {
                    pdfUploaded = true;
                }
            } else if (type === 'pdf_rag') {
                renderChatHistory('pdf', sortedChats);
                // If there are PDF chats, set pdfUploaded to true
                if (sortedChats.length > 0) {
                    pdfUploaded = true;
                }
            } else if (type === 'web_search') {
                renderChatHistory('web', sortedChats);
            }
        }
    })
    .catch(error => {
        console.error('Error loading chat history:', error);
    });
}

function renderChatHistory(type, chats) {
    const chatMessages = type === 'pdf' 
        ? document.getElementById('pdfChatMessages')
        : document.getElementById('webChatMessages');
    
    // Clear existing messages
    chatMessages.innerHTML = '';
    
    // Render each chat
    chats.forEach(chat => {
        addUserMessage(type, chat.message);
        addBotMessage(type, chat.response);
    });
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

