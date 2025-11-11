let currentUserId = null;

// Check admin authentication status on page load
document.addEventListener('DOMContentLoaded', function() {
    checkAdminStatus();
});

function checkAdminStatus() {
    fetch('/api/admin/status', {
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.authenticated) {
            showAdminDashboard(data.username);
        } else {
            showAdminLogin();
        }
    })
    .catch(error => {
        console.error('Error checking admin status:', error);
        showAdminLogin();
    });
}

function showAdminLogin() {
    document.getElementById('adminLoginModal').style.display = 'flex';
    document.getElementById('adminDashboard').style.display = 'none';
}

function showAdminDashboard(username) {
    document.getElementById('adminLoginModal').style.display = 'none';
    document.getElementById('adminDashboard').style.display = 'block';
    document.getElementById('adminUsernameDisplay').textContent = username;
    loadUsers();
}

function adminLogin() {
    const username = document.getElementById('adminUsername').value.trim();
    const password = document.getElementById('adminPassword').value;
    const errorDiv = document.getElementById('adminLoginError');
    
    if (!username || !password) {
        errorDiv.textContent = 'Username and password are required';
        return;
    }
    
    fetch('/api/admin/login', {
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
            showAdminDashboard(username);
        }
    })
    .catch(error => {
        errorDiv.textContent = 'Error: ' + error.message;
    });
}

function adminLogout() {
    fetch('/api/admin/logout', {
        method: 'POST',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        showAdminLogin();
    })
    .catch(error => {
        console.error('Error logging out:', error);
    });
}

function loadUsers() {
    fetch('/api/admin/users', {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error loading users:', data.error);
            if (response.status === 403) {
                showAdminLogin();
            }
            return;
        }
        renderUsers(data.users);
    })
    .catch(error => {
        console.error('Error loading users:', error);
    });
}

function renderUsers(users) {
    const usersList = document.getElementById('usersList');
    
    if (!users || users.length === 0) {
        usersList.innerHTML = '<div class="empty-state"><p>No users found</p></div>';
        return;
    }
    
    usersList.innerHTML = users.map(user => `
        <div class="user-card" onclick="viewUserDetails('${user._id}', '${escapeHtml(user.username)}')">
            <h3>${escapeHtml(user.username)}</h3>
            <p><strong>Email:</strong> ${escapeHtml(user.email || 'N/A')}</p>
            <p><strong>Joined:</strong> ${formatDate(user.created_at)}</p>
        </div>
    `).join('');
}

function viewUserDetails(userId, username) {
    currentUserId = userId;
    document.getElementById('userDetailName').textContent = `User: ${username}`;
    document.getElementById('usersView').classList.remove('active');
    document.getElementById('userDetailView').classList.add('active');
    switchUserTab('pdfs');
}

function showUsersList() {
    currentUserId = null;
    document.getElementById('usersView').classList.add('active');
    document.getElementById('userDetailView').classList.remove('active');
    loadUsers();
}

function switchUserTab(tab) {
    const tabs = document.querySelectorAll('#userDetailView .tab');
    const tabContents = document.querySelectorAll('#userDetailView .tab-content');
    
    tabs.forEach(t => t.classList.remove('active'));
    tabContents.forEach(tc => tc.classList.remove('active'));
    
    if (tab === 'pdfs') {
        tabs[0].classList.add('active');
        document.getElementById('pdfsTab').classList.add('active');
        loadUserPdfs();
    } else {
        tabs[1].classList.add('active');
        document.getElementById('chatsTab').classList.add('active');
        loadUserChats();
    }
}

function loadUserPdfs() {
    if (!currentUserId) return;
    
    const pdfsList = document.getElementById('userPdfsList');
    pdfsList.innerHTML = '<div class="empty-state"><p>Loading PDFs...</p></div>';
    
    fetch(`/api/admin/users/${currentUserId}/pdfs`, {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            console.error('Error loading PDFs:', data.error);
            pdfsList.innerHTML = `<div class="empty-state"><p>Error: ${data.error}</p></div>`;
            return;
        }
        renderUserPdfs(data.pdfs || []);
    })
    .catch(error => {
        console.error('Error loading PDFs:', error);
        pdfsList.innerHTML = `<div class="empty-state"><p>Error loading PDFs: ${error.message}</p></div>`;
    });
}

function renderUserPdfs(pdfs) {
    const pdfsList = document.getElementById('userPdfsList');
    
    if (!pdfs || pdfs.length === 0) {
        pdfsList.innerHTML = '<div class="empty-state"><p>No PDFs uploaded</p></div>';
        return;
    }
    
    pdfsList.innerHTML = pdfs.map(pdf => `
        <div class="content-item">
            <h4>${escapeHtml(pdf.filename || 'Unknown filename')}</h4>
            <p><strong>Chunks:</strong> ${pdf.chunks_count || 'N/A'}</p>
            <p class="timestamp"><strong>Uploaded:</strong> ${formatDate(pdf.uploaded_at)}</p>
        </div>
    `).join('');
}

function loadUserChats() {
    if (!currentUserId) return;
    
    fetch(`/api/admin/users/${currentUserId}/chats`, {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error loading chats:', data.error);
            return;
        }
        renderUserChats(data.chats);
    })
    .catch(error => {
        console.error('Error loading chats:', error);
    });
}

function renderUserChats(chats) {
    const chatsList = document.getElementById('userChatsList');
    
    if (!chats || chats.length === 0) {
        chatsList.innerHTML = '<div class="empty-state"><p>No chats found</p></div>';
        return;
    }
    
    // Sort by timestamp (newest first)
    const sortedChats = chats.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    chatsList.innerHTML = sortedChats.map(chat => `
        <div class="chat-item">
            <span class="chat-type">${chat.type === 'pdf_rag' ? 'PDF RAG' : 'Web Search'}</span>
            <div class="chat-message">
                <strong>User:</strong> ${escapeHtml(chat.message)}
            </div>
            <div class="chat-response">
                <strong>Bot:</strong> ${escapeHtml(chat.response)}
            </div>
            <p class="timestamp">${formatDate(chat.timestamp)}</p>
        </div>
    `).join('');
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Handle Enter key in login form
document.addEventListener('DOMContentLoaded', function() {
    const adminPassword = document.getElementById('adminPassword');
    if (adminPassword) {
        adminPassword.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                adminLogin();
            }
        });
    }
});

