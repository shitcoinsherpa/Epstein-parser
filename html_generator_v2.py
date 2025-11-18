import json
import os
from datetime import datetime
from typing import Dict, List

class MessagingHTMLGenerator:
    """Generate iMessage/WhatsApp style HTML viewer for emails"""

    def __init__(self, emails: List[Dict], threads: List[Dict], stats: Dict):
        self.emails = emails
        self.threads = threads
        self.stats = stats

    def generate(self, output_dir: str):
        """Generate all HTML files and assets"""
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/assets/css", exist_ok=True)
        os.makedirs(f"{output_dir}/assets/js", exist_ok=True)

        self.generate_index_html(output_dir)
        self.generate_messaging_css(output_dir)
        self.generate_javascript(output_dir)

        print(f"Messaging-style HTML generated in {output_dir}/")

    def generate_index_html(self, output_dir: str):
        """Generate main HTML file with messaging interface"""

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Epstein Email Archive - House Oversight</title>
    <link rel="stylesheet" href="assets/css/messaging.css">
</head>
<body>
    <div class="app-container">
        <!-- Header -->
        <header class="app-header">
            <div class="header-content">
                <h1>📧 Epstein Email Archive</h1>
                <div class="stats">
                    <span class="stat-pill">📨 {self.stats.get('emails_found', 0)} Emails</span>
                    <span class="stat-pill epstein">🔴 {self.stats.get('epstein_sent', 0)} from Epstein</span>
                    <span class="stat-pill">👥 {self.stats.get('unique_senders', 0)} Senders</span>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <div class="main-content">
            <!-- Sidebar with Conversations List -->
            <aside class="conversations-sidebar">
                <div class="sidebar-header">
                    <h2>Conversations</h2>
                    <input type="text" id="global-search" placeholder="Search all emails (keyword or exact phrase)..." class="search-box">
                </div>

                <div class="filter-tabs">
                    <button class="filter-tab active" data-filter="from">From Epstein</button>
                    <button class="filter-tab" data-filter="to">To Epstein</button>
                </div>

                <div class="sender-list" id="sender-list">
                    <!-- Populated by JS -->
                </div>
            </aside>

            <!-- Messages Display -->
            <main class="messages-panel">
                <div class="messages-header" id="messages-header">
                    <div class="header-title">
                        <h2>Select a conversation</h2>
                    </div>
                    <div class="header-controls">
                        <span class="metadata-info" id="metadata-info"></span>
                    </div>
                </div>

                <div class="messages-container" id="messages-container">
                    <div class="empty-state">
                        <p>👈 Select a sender from the left to view their conversation with Epstein</p>
                    </div>
                </div>

                <div class="message-controls">
                    <button id="export-conversation" class="btn-secondary">Export Current Conversation</button>
                    <button id="export-all" class="btn-secondary">Export All as CSV</button>
                </div>
            </main>
        </div>
    </div>

    <script src="assets/js/data.js"></script>
    <script src="assets/js/messaging.js"></script>
</body>
</html>'''

        with open(f"{output_dir}/index.html", 'w', encoding='utf-8') as f:
            f.write(html)

    def generate_messaging_css(self, output_dir: str):
        """Generate messaging app style CSS"""

        css = '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: #f0f2f5;
    height: 100vh;
    overflow: hidden;
}

.app-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
}

/* Header */
.app-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem 2rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.header-content h1 {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}

.stats {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.stat-pill {
    background: rgba(255,255,255,0.2);
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.85rem;
    backdrop-filter: blur(10px);
}

.stat-pill.epstein {
    background: rgba(255,100,100,0.3);
}

/* Main Layout */
.main-content {
    display: flex;
    flex: 1;
    overflow: hidden;
}

/* Sidebar */
.conversations-sidebar {
    width: 350px;
    background: white;
    border-right: 1px solid #e0e0e0;
    display: flex;
    flex-direction: column;
}

.sidebar-header {
    padding: 1rem;
    border-bottom: 1px solid #e0e0e0;
}

.sidebar-header h2 {
    font-size: 1.2rem;
    margin-bottom: 0.75rem;
    color: #333;
}

.search-box {
    width: 100%;
    padding: 0.5rem;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 0.9rem;
}

.search-box:focus {
    outline: none;
    border-color: #667eea;
}

.filter-tabs {
    display: flex;
    border-bottom: 1px solid #e0e0e0;
}

.filter-tab {
    flex: 1;
    padding: 0.75rem;
    border: none;
    background: white;
    cursor: pointer;
    font-weight: 500;
    color: #666;
    transition: all 0.2s;
}

.filter-tab.active {
    color: #667eea;
    border-bottom: 2px solid #667eea;
}

.filter-tab:hover {
    background: #f5f5f5;
}

.sender-list {
    flex: 1;
    overflow-y: auto;
}

.sender-item {
    padding: 1rem;
    border-bottom: 1px solid #f0f0f0;
    cursor: pointer;
    transition: background 0.2s;
}

.sender-item:hover {
    background: #f8f9fa;
}

.sender-item.active {
    background: #e3f2fd;
    border-left: 3px solid #667eea;
}

.sender-name {
    font-weight: 600;
    color: #333;
    margin-bottom: 0.25rem;
}

.sender-preview {
    font-size: 0.85rem;
    color: #777;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.sender-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 0.25rem;
}

.sender-count {
    font-size: 0.75rem;
    background: #667eea;
    color: white;
    padding: 0.125rem 0.5rem;
    border-radius: 10px;
}

.sender-date {
    font-size: 0.75rem;
    color: #999;
}

/* Messages Panel */
.messages-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: #e5ddd5;
    position: relative;
}

.messages-header {
    background: white;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #e0e0e0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
}

.header-title h2 {
    color: #333;
    font-size: 1.1rem;
    margin: 0;
}

.header-controls {
    display: flex;
    gap: 1rem;
    align-items: center;
}

.metadata-info {
    font-size: 0.8rem;
    color: #666;
    padding: 0.25rem 0.75rem;
    background: #f5f5f5;
    border-radius: 12px;
}

.messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 2rem;
    background-image: repeating-linear-gradient(
        0deg,
        rgba(255,255,255,0.03),
        rgba(255,255,255,0.03) 1px,
        transparent 1px,
        transparent 2px
    );
}

.empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #999;
    font-size: 1.1rem;
}

/* Message Bubbles - Gmail-style Threading */
.message-group {
    margin-bottom: 2rem;
}

.message-date-divider {
    text-align: center;
    margin: 1.5rem 0;
}

.date-badge {
    display: inline-block;
    background: rgba(0,0,0,0.2);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
}

.message-bubble {
    margin-bottom: 0.75rem;
    display: flex;
    flex-direction: column;
    animation: fadeIn 0.3s ease-in;
    position: relative;
    padding-left: 0;
}

/* Threading indentation */
.message-bubble[data-reply-depth="1"] { padding-left: 2rem; }
.message-bubble[data-reply-depth="2"] { padding-left: 4rem; }
.message-bubble[data-reply-depth="3"] { padding-left: 6rem; }
.message-bubble[data-reply-depth="4"] { padding-left: 8rem; }
.message-bubble[data-reply-depth="5"] { padding-left: 10rem; }

/* Threading line indicator */
.message-bubble[data-reply-depth]::before {
    content: '';
    position: absolute;
    left: 1rem;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #e0e0e0;
}

.message-bubble[data-reply-depth="2"]::before { left: 3rem; }
.message-bubble[data-reply-depth="3"]::before { left: 5rem; }
.message-bubble[data-reply-depth="4"]::before { left: 7rem; }
.message-bubble[data-reply-depth="5"]::before { left: 9rem; }

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Epstein's messages - Purple gradient border */
.message-bubble.epstein-sent .bubble-content {
    background: white;
    color: #333;
    border-left: 4px solid #667eea;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* Messages to Epstein - Gray border */
.message-bubble.epstein-received .bubble-content {
    background: white;
    color: #333;
    border-left: 4px solid #9e9e9e;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* Forward emails - Orange border */
.message-bubble.is-forward .bubble-content {
    border-left-color: #ff9800 !important;
}

.bubble-content {
    padding: 0.75rem 1rem;
    word-wrap: break-word;
}

.bubble-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.25rem;
    font-size: 0.75rem;
    opacity: 0.9;
    flex-wrap: wrap;
}

.bubble-sender {
    font-weight: 600;
}

.bubble-badge {
    padding: 0.125rem 0.5rem;
    border-radius: 10px;
    font-size: 0.65rem;
    background: rgba(0,0,0,0.1);
    font-weight: 500;
}

.bubble-text {
    line-height: 1.4;
    white-space: pre-wrap;
}

.bubble-footer {
    font-size: 0.7rem;
    margin-top: 0.25rem;
    opacity: 0.7;
    text-align: right;
}

.message-subject {
    font-weight: 600;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    opacity: 0.9;
}

/* Controls */
.message-controls {
    background: white;
    padding: 1rem;
    border-top: 1px solid #e0e0e0;
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
}

.btn-secondary {
    padding: 0.5rem 1rem;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background 0.2s;
}

.btn-secondary:hover {
    background: #5568d3;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #555;
}

/* Responsive */
@media (max-width: 768px) {
    .conversations-sidebar {
        width: 100%;
        position: absolute;
        z-index: 10;
        height: 100%;
    }

    .conversations-sidebar.hidden {
        display: none;
    }

    .message-bubble {
        max-width: 85%;
    }
}
'''

        with open(f"{output_dir}/assets/css/messaging.css", 'w', encoding='utf-8') as f:
            f.write(css)

    def generate_javascript(self, output_dir: str):
        """Generate JavaScript with embedded data (works offline)"""

        # Embed data directly in data.js for offline compatibility
        # Note: For production with web server, could switch to lazy loading
        data_js = f'''// Email data (embedded for offline use)
const emailData = {json.dumps(self.emails, ensure_ascii=False)};
const statistics = {json.dumps(self.stats, ensure_ascii=False)};
'''

        with open(f"{output_dir}/assets/js/data.js", 'w', encoding='utf-8') as f:
            f.write(data_js)

        # Generate messaging.js
        messaging_js = '''// Messaging app logic
let currentSender = null;
let filteredEmails = [];
let filterMode = 'from';

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    // Check if emailData is loaded
    if (typeof emailData === 'undefined' || !emailData || emailData.length === 0) {
        console.error('Email data not loaded. Please ensure data.js is loaded correctly.');
        document.getElementById('sender-list').innerHTML = '<div style="padding: 1rem; text-align: center; color: #f44336;">⚠️ Error: Email data failed to load. Please refresh the page.</div>';
        return;
    }

    console.log(`Loaded ${emailData.length} emails`);
    filteredEmails = emailData;

    attachEventListeners();
    applyFilter('from');
    populateSenderList();
});

function attachEventListeners() {
    // Filter tabs
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            applyFilter(this.dataset.filter);
        });
    });

    // Global search
    document.getElementById('global-search').addEventListener('input', debounce(function(e) {
        globalSearch(e.target.value);
    }, 300));

    // Export buttons
    document.getElementById('export-conversation').addEventListener('click', exportCurrentConversation);
    document.getElementById('export-all').addEventListener('click', exportAll);
}

function applyFilter(mode) {
    filterMode = mode;
    if (mode === 'from') {
        // Show only emails FROM Epstein
        filteredEmails = emailData.filter(e => e.is_epstein_sender);
    } else if (mode === 'to') {
        // Show only emails TO Epstein
        filteredEmails = emailData.filter(e => e.is_epstein_recipient && !e.is_epstein_sender);
    } else {
        filteredEmails = emailData;
    }
    // Rebuild search index when filter changes
    searchIndex = null;
    populateSenderList();
}

function globalSearch(query) {
    query = query.trim();

    if (!query) {
        // If search is cleared, restore normal view and clear highlighting
        currentSearchTerm = '';
        populateSenderList();
        return;
    }

    // Store search term for highlighting
    currentSearchTerm = query;
    const queryLower = query.toLowerCase();

    // Search across all emails in current filter
    const matchingEmails = filteredEmails.filter(email => {
        const searchableText = [
            email.from || '',
            email.to || '',
            email.subject || '',
            email.body || ''
        ].join(' ').toLowerCase();

        return searchableText.includes(queryLower);
    });

    if (matchingEmails.length === 0) {
        const list = document.getElementById('sender-list');
        list.innerHTML = '<div style="padding: 1rem; text-align: center; color: #999;">No results found for "' + escapeHtml(query) + '"</div>';
        return;
    }

    // Group results by person (sender or recipient depending on mode)
    const resultsMap = new Map();
    matchingEmails.forEach(email => {
        // In "from" mode, process all recipients from to_list
        if (filterMode === 'from') {
            const recipients = email.to_list || [email.to || 'Unknown Recipient'];
            recipients.forEach(person => {
                if (!person) person = 'Unknown Recipient';
                const cleanedName = cleanSenderName(person);
                const normalizedKey = normalizeName(cleanedName);


                if (!resultsMap.has(normalizedKey)) {
                    resultsMap.set(normalizedKey, {
                        name: person,
                        count: 0,
                        latestDate: email.timestamp || 0,
                        preview: '',
                        matchingEmails: []
                    });
                }
                const data = resultsMap.get(normalizedKey);
                data.count++;
                data.matchingEmails.push(email);

                if ((email.timestamp || 0) > data.latestDate) {
                    data.latestDate = email.timestamp || 0;
                    // Show snippet with match context
                    const bodyPreview = email.body || '';
                    const matchIndex = bodyPreview.toLowerCase().indexOf(queryLower);
                    if (matchIndex > -1) {
                        const start = Math.max(0, matchIndex - 30);
                        const end = Math.min(bodyPreview.length, matchIndex + queryLower.length + 30);
                        data.preview = '...' + bodyPreview.substring(start, end) + '...';
                    } else {
                        data.preview = bodyPreview.substring(0, 50) + '...';
                    }
                }
            });
        } else {
            // In "to" mode, just show the sender
            let person = email.from || 'Unknown';
            const cleanedName = cleanSenderName(person);
            const normalizedKey = normalizeName(cleanedName);


            if (!resultsMap.has(normalizedKey)) {
                resultsMap.set(normalizedKey, {
                    name: person,
                    count: 0,
                    latestDate: email.timestamp || 0,
                    preview: '',
                    matchingEmails: []
                });
            }
            const data = resultsMap.get(normalizedKey);
            data.count++;
            data.matchingEmails.push(email);

            if ((email.timestamp || 0) > data.latestDate) {
                data.latestDate = email.timestamp || 0;
                // Show snippet with match context
                const bodyPreview = email.body || '';
                const matchIndex = bodyPreview.toLowerCase().indexOf(queryLower);
                if (matchIndex > -1) {
                    const start = Math.max(0, matchIndex - 30);
                    const end = Math.min(bodyPreview.length, matchIndex + queryLower.length + 30);
                    data.preview = '...' + bodyPreview.substring(start, end) + '...';
                } else {
                    data.preview = bodyPreview.substring(0, 50) + '...';
                }
            }
        }
    });

    const results = Array.from(resultsMap.values())
        .sort((a, b) => {
            // Always put "Unknown Recipient" at the top
            if (a.name === 'Unknown Recipient') return -1;
            if (b.name === 'Unknown Recipient') return 1;
            // Then sort by latest date
            return b.latestDate - a.latestDate;
        });

    const list = document.getElementById('sender-list');
    list.innerHTML = '<div style="padding: 0.5rem 1rem; background: #e3f2fd; font-size: 0.85rem; color: #1976d2; border-bottom: 1px solid #e0e0e0;">' +
        '🔍 ' + matchingEmails.length + ' results in ' + results.length + ' conversations</div>' +
        results.map(sender => `
            <div class="sender-item" data-sender="${escapeHtml(sender.name)}" onclick="selectSender('${escapeHtml(sender.name)}')">
                <div class="sender-name">${escapeHtml(sender.name)}</div>
                <div class="sender-preview">${escapeHtml(sender.preview)}</div>
                <div class="sender-meta">
                    <span class="sender-count">${sender.count} matches</span>
                    <span class="sender-date">${formatDate(sender.latestDate)}</span>
                </div>
            </div>
        `).join('');
}

function populateSenderList() {
    if (!filteredEmails || filteredEmails.length === 0) {
        console.warn('No emails to display');
        const list = document.getElementById('sender-list');
        list.innerHTML = '<div style="padding: 1rem; text-align: center; color: #999;">No emails found</div>';
        return;
    }

    const senderMap = new Map();

    filteredEmails.forEach(email => {
        // In "from" mode, show ALL recipients (people Epstein sent TO) from to_list
        // In "to" mode, show senders (people who sent TO Epstein)
        if (filterMode === 'from') {
            // Process all recipients in to_list
            const recipients = email.to_list || [email.to || 'Unknown Recipient'];
            recipients.forEach(person => {
                if (!person) person = 'Unknown Recipient';
                const cleanedName = cleanSenderName(person);
                const normalizedKey = normalizeName(cleanedName);


                if (!senderMap.has(normalizedKey)) {
                    senderMap.set(normalizedKey, {
                        name: cleanedName,
                        count: 0,
                        latestDate: email.timestamp || 0,
                        preview: email.body ? email.body.substring(0, 50) + '...' : ''
                    });
                }
                const data = senderMap.get(normalizedKey);
                data.count++;
                if ((email.timestamp || 0) > data.latestDate) {
                    data.latestDate = email.timestamp || 0;
                    data.preview = email.body ? email.body.substring(0, 50) + '...' : '';
                }
            });
        } else {
            // In "to" mode, just show the sender
            let person = email.from || 'Unknown';
            const cleanedName = cleanSenderName(person);
            const normalizedKey = normalizeName(cleanedName);


            if (!senderMap.has(normalizedKey)) {
                senderMap.set(normalizedKey, {
                    name: cleanedName,
                    count: 0,
                    latestDate: email.timestamp || 0,
                    preview: email.body ? email.body.substring(0, 50) + '...' : ''
                });
            }
            const data = senderMap.get(normalizedKey);
            data.count++;
            if ((email.timestamp || 0) > data.latestDate) {
                data.latestDate = email.timestamp || 0;
                data.preview = email.body ? email.body.substring(0, 50) + '...' : '';
            }
        }
    });

    const senders = Array.from(senderMap.values())
        .sort((a, b) => {
            // Always put "Unknown Recipient" at the top
            if (a.name === 'Unknown Recipient') return -1;
            if (b.name === 'Unknown Recipient') return 1;
            // Then sort alphabetically
            return a.name.localeCompare(b.name);
        });

    renderSenderList(senders);
}

function renderSenderList(senders) {
    const list = document.getElementById('sender-list');
    list.innerHTML = senders.map(sender => `
        <div class="sender-item" data-sender="${escapeHtml(sender.name)}" onclick="selectSender('${escapeHtml(sender.name)}')">
            <div class="sender-name">${escapeHtml(sender.name)}</div>
            <div class="sender-preview">${escapeHtml(sender.preview)}</div>
            <div class="sender-meta">
                <span class="sender-count">${sender.count} messages</span>
                <span class="sender-date">${formatDate(sender.latestDate)}</span>
            </div>
        </div>
    `).join('');
}

function selectSender(sender) {
    currentSender = sender;

    // Update UI
    document.querySelectorAll('.sender-item').forEach(item => item.classList.remove('active'));
    document.querySelector(`[data-sender="${sender}"]`)?.classList.add('active');

    // Load conversation
    loadConversation(sender);
}

function loadConversation(sender) {
    // Get all emails involving this sender (check both 'to' and 'to_list')
    let emails = filteredEmails.filter(e =>
        e.from === sender ||
        e.to === sender ||
        (e.to_list && e.to_list.includes(sender))
    );

    // Group by SOURCE FILE to show threaded conversations
    const fileGroups = {};
    emails.forEach(email => {
        const fileKey = email.source_file || 'unknown';
        if (!fileGroups[fileKey]) {
            fileGroups[fileKey] = [];
        }
        fileGroups[fileKey].push(email);
    });

    // Sort emails within each file by timestamp (chronological order)
    Object.keys(fileGroups).forEach(fileKey => {
        fileGroups[fileKey].sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
    });

    // Convert to array of thread objects for easier handling
    const threads = Object.entries(fileGroups).map(([sourceFile, threadEmails]) => ({
        sourceFile,
        emails: threadEmails,
        isConversation: threadEmails.length > 1,
        earliestTimestamp: Math.min(...threadEmails.map(e => e.timestamp || 0))
    }));

    // Sort threads by earliest timestamp
    threads.sort((a, b) => a.earliestTimestamp - b.earliestTimestamp);

    // Deduplicate: find threads with identical content
    const signatureMap = new Map();
    const deduplicatedThreads = [];

    threads.forEach(thread => {
        if (thread.emails.length > 0) {
            const first = thread.emails[0];
            const sig = `${first.from}|${first.to}|${first.timestamp}|${(first.body || '').substring(0, 50)}`;

            if (signatureMap.has(sig)) {
                // This is a duplicate - add source file to existing list
                signatureMap.get(sig).duplicateSources.push(thread.sourceFile);
            } else {
                // First occurrence - store it
                thread.duplicateSources = [thread.sourceFile];
                signatureMap.set(sig, thread);
                deduplicatedThreads.push(thread);
            }
        }
    });

    if (emails.length === 0) {
        document.getElementById('messages-container').innerHTML = '<div class="empty-state"><p>No messages found</p></div>';
        return;
    }

    // Get date range for metadata
    const timestamps = emails.map(e => e.timestamp || 0).filter(t => t > 0);
    const dateRange = timestamps.length > 0
        ? `${formatDate(Math.min(...timestamps))} - ${formatDate(Math.max(...timestamps))}`
        : 'Unknown dates';

    // Update header with metadata (use deduplicated count)
    document.getElementById('messages-header').innerHTML = `
        <div class="header-title">
            <h2>${escapeHtml(sender)} <span style="color: #999; font-size: 0.9rem;">(${emails.length} messages in ${deduplicatedThreads.length} ${deduplicatedThreads.length === 1 ? 'thread' : 'threads'})</span></h2>
        </div>
        <div class="header-controls">
            <span class="metadata-info">${dateRange}</span>
        </div>
    `;

    // Build HTML for threaded display
    let html = '';
    let threadIndex = 0;

    deduplicatedThreads.forEach(thread => {
        threadIndex++;

        // Add conversation header for multi-message threads
        if (thread.isConversation) {
            const hasDuplicates = thread.duplicateSources && thread.duplicateSources.length > 1;
            const otherSources = hasDuplicates ? thread.duplicateSources.filter(s => s !== thread.sourceFile) : [];

            html += `
                <div class="conversation-header" style="background: rgba(102, 126, 234, 0.1); padding: 0.75rem 1rem; margin: 1.5rem 0 0.75rem 0; border-radius: 8px; border-left: 4px solid #667eea;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; font-weight: 600; color: #667eea;">
                        <span>💬</span>
                        <span>Conversation ${threadIndex} (${thread.emails.length} messages)</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #666; margin-top: 0.25rem;">
                        Source: ${escapeHtml(thread.sourceFile)}
                    </div>
                    ${hasDuplicates ? `
                        <div style="font-size: 0.75rem; color: #888; margin-top: 0.5rem; padding: 0.5rem; background: rgba(0,0,0,0.05); border-radius: 4px; opacity: 0.8;">
                            ℹ️ <em>Additional copies of this conversation found in: ${otherSources.map(s => escapeHtml(s)).join(', ')}</em>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        // Display each message in the thread
        thread.emails.forEach((email, msgIndex) => {
            const isEpsteinSent = email.is_epstein_sender;
            const bubbleClass = isEpsteinSent ? 'epstein-sent' : 'epstein-received';
            const isForward = email.is_forward ? 'is-forward' : '';
            const replyDepth = email.reply_depth || 0;
            const isEmbedded = email.is_embedded || false;

            const recipientDisplay = email.to && email.to !== 'Unknown Recipient'
                ? escapeHtml(email.to)
                : `<span class="editable-recipient" contenteditable="true" data-email-id="${email.id}" style="color: #ff9800; font-style: italic; cursor: text;" title="Click to edit recipient">Unknown Recipient ✏️</span>`;

            // Add message number for conversations
            const messageLabel = thread.isConversation ? `<span class="bubble-badge" style="background: #667eea; color: white;">Message ${msgIndex + 1}</span>` : '';
            const embeddedLabel = isEmbedded ? `<span class="bubble-badge" style="background: #4caf50; color: white;">📨 Embedded</span>` : '';

            html += `
                <div class="message-bubble ${bubbleClass} ${isForward}" data-reply-depth="${replyDepth}" data-email-id="${email.id}">
                    <div class="bubble-content">
                        <div class="bubble-meta">
                            <span class="bubble-sender" style="color: ${isEpsteinSent ? '#667eea' : '#666'}; font-weight: 700;">
                                ${isEpsteinSent ? 'Jeffrey Epstein' : escapeHtml(email.from || 'Unknown')}
                            </span>
                            <span style="color: #999;">to ${recipientDisplay}</span>
                            ${messageLabel}
                            ${embeddedLabel}
                            ${email.format ? `<span class="bubble-badge">${email.format}</span>` : ''}
                            ${!thread.isConversation && email.source_file ? `<span class="bubble-badge" title="Source: ${email.source_file}">📄 ${email.source_file}</span>` : ''}
                            ${replyDepth > 0 ? `<span class="bubble-badge" title="Reply depth">↩️ ${replyDepth}</span>` : ''}
                            ${email.is_forward ? `<span class="bubble-badge" style="background: #ff9800; color: white;">FWD</span>` : ''}
                        </div>
                        ${email.subject_clean ? `<div class="message-subject">📧 ${currentSearchTerm ? highlightText(email.subject_clean, currentSearchTerm) : escapeHtml(email.subject_clean)}</div>` : email.subject ? `<div class="message-subject">📧 ${currentSearchTerm ? highlightText(email.subject, currentSearchTerm) : escapeHtml(email.subject)}</div>` : ''}
                        ${email.body ? `<div class="bubble-text">${currentSearchTerm ? highlightText(email.body, currentSearchTerm) : escapeHtml(email.body)}</div>` : (!email.disclaimer ? `<div class="bubble-text" style="font-style: italic; opacity: 0.7;">(No content)</div>` : '')}
                        ${email.disclaimer ? `<div class="disclaimer-text" style="font-size: 0.75rem; font-style: italic; opacity: 0.6; margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(0,0,0,0.1);">${!email.body ? `<strong>BODY:</strong> <em style="opacity: 0.8;">[Message contained only legal disclaimer]</em><br><br>` : ''}<em>${escapeHtml(email.disclaimer.substring(0, 200))}${email.disclaimer.length > 200 ? '...' : ''}</em></div>` : ''}
                        ${email.duplicate_sources && email.duplicate_sources.length > 1 ? `
                            <div style="font-size: 0.7rem; color: #888; margin-top: 0.5rem; padding: 0.5rem; background: rgba(0,0,0,0.05); border-radius: 4px;">
                                ℹ️ <em>Also found in: ${email.duplicate_sources.filter(s => s !== email.source_file).map(s => escapeHtml(s)).join(', ')}</em>
                            </div>
                        ` : ''}
                        <div class="bubble-footer" style="color: #999; font-size: 0.7rem;">
                            ${formatDateTime(email.timestamp)}
                            ${email.to_list && email.to_list.length > 1 ? `<span style="margin-left: 0.5rem;" title="Recipients: ${email.to_list.join(', ')}">👥 ${email.to_list.length}</span>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });

        // Add separator between threads
        if (threadIndex < deduplicatedThreads.length) {
            html += `<div style="height: 1px; background: #e0e0e0; margin: 1.5rem 0;"></div>`;
        }
    });

    document.getElementById('messages-container').innerHTML = html;
    document.getElementById('messages-container').scrollTop = document.getElementById('messages-container').scrollHeight;

    // Attach event listeners to editable recipients
    document.querySelectorAll('.editable-recipient').forEach(el => {
        el.addEventListener('blur', function() {
            const emailId = this.getAttribute('data-email-id');
            const newRecipient = this.textContent.trim().replace(' ✏️', '');

            // Update the email data
            const email = emailData.find(e => e.id === emailId);
            if (email && newRecipient) {
                email.to = newRecipient;
                email.to_list = [newRecipient];
                console.log(`Updated recipient for email ${emailId} to: ${newRecipient}`);

                // Visual feedback
                this.style.color = '#4caf50';
                this.style.fontStyle = 'normal';
                this.textContent = newRecipient;

                setTimeout(() => {
                    this.style.color = '#999';
                }, 1000);
            }
        });

        el.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.blur();
            }
        });
    });
}

function groupByDate(emails) {
    const groups = {};
    emails.forEach(email => {
        const date = new Date((email.timestamp || 0) * 1000);
        const dateKey = date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
        if (!groups[dateKey]) groups[dateKey] = [];
        groups[dateKey].push(email);
    });
    return groups;
}

// Build search index for faster lookups
let searchIndex = null;
let currentSearchTerm = '';  // Store current search term for highlighting

// Highlight search terms in text
function highlightText(text, searchTerm) {
    if (!searchTerm || !text) return escapeHtml(text);

    // Escape HTML first
    const escapedText = escapeHtml(text);

    // Create case-insensitive regex, escape special regex characters
    const escapedTerm = searchTerm.replace(/[.*+?^${}()|[\]\\\\]/g, '\\\\$&');
    const regex = new RegExp(`(${escapedTerm})`, 'gi');

    // Wrap matches in <mark> tags
    return escapedText.replace(regex, '<mark style="background-color: #ffeb3b; padding: 2px 4px; border-radius: 2px; font-weight: 600;">$1</mark>');
}

function buildSearchIndex() {
    searchIndex = filteredEmails.map((email, idx) => ({
        idx,
        searchText: [
            email.from || '',
            email.to || '',
            email.subject || '',
            email.subject_clean || '',
            email.body || ''
        ].join(' ').toLowerCase()
    }));
}

function searchSenders(query) {
    if (!query) {
        populateSenderList();
        return;
    }

    const senderMap = new Map();
    const queryLower = query.toLowerCase();
    const isExactMatch = query.startsWith('"') && query.endsWith('"');
    const searchQuery = isExactMatch ? query.slice(1, -1).toLowerCase() : queryLower;

    // Use search index if available
    if (!searchIndex) buildSearchIndex();

    const matchingIndices = searchIndex
        .filter(item => isExactMatch ? item.searchText.includes(searchQuery) : item.searchText.includes(queryLower))
        .map(item => item.idx);

    matchingIndices.forEach(idx => {
        const email = filteredEmails[idx];
        const sender = email.from || 'Unknown';

        if (!senderMap.has(sender)) {
            senderMap.set(sender, {
                name: sender,
                count: 0,
                latestDate: email.timestamp || 0,
                preview: email.body ? email.body.substring(0, 50) + '...' : ''
            });
        }
        senderMap.get(sender).count++;
    });

    const senders = Array.from(senderMap.values())
        .sort((a, b) => b.latestDate - a.latestDate);

    renderSenderList(senders);
}

function exportCurrentConversation() {
    if (!currentSender) return;

    const emails = filteredEmails.filter(e => e.from === currentSender || e.to === currentSender)
        .sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));

    const csv = [
        ['Date', 'From', 'To', 'Subject', 'Message'],
        ...emails.map(e => [
            formatDateTime(e.timestamp),
            e.from || '',
            e.to || '',
            e.subject || '',
            (e.body || '').replace(/"/g, '""')
        ])
    ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\\n');

    downloadCSV(csv, `conversation_${currentSender.replace(/[^a-z0-9]/gi, '_')}.csv`);
}

function exportAll() {
    const csv = [
        ['Date', 'From', 'To', 'Subject', 'Message'],
        ...filteredEmails.map(e => [
            formatDateTime(e.timestamp),
            e.from || '',
            e.to || '',
            e.subject || '',
            (e.body || '').replace(/"/g, '""')
        ])
    ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\\n');

    downloadCSV(csv, 'epstein_emails_all.csv');
}

function downloadCSV(csv, filename) {
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function formatDate(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diff = now - date;

    if (diff < 86400000) return 'Today';
    if (diff < 172800000) return 'Yesterday';
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function formatDateTime(timestamp) {
    if (!timestamp) return 'Unknown date';
    const date = new Date(timestamp * 1000);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function cleanSenderName(name) {
    if (!name) return name;

    // Strip OCR garbage in brackets
    const bracketMatch = name.match(/^(.+?)\\s*\\[([^\\]]+)\\]\\s*$/);
    if (bracketMatch) {
        const namePart = bracketMatch[1].trim();
        const bracketContent = bracketMatch[2].trim();
        const emailPattern = /^[\\w\\.\\-+]+@[\\w\\.\\-]+\\.[a-zA-Z]{2,}$/;
        if (!emailPattern.test(bracketContent)) {
            name = namePart;
        }
    }

    return name.trim();
}

function normalizeName(name) {
    // Normalize for grouping: lowercase
    if (!name) return name;
    return cleanSenderName(name).toLowerCase().trim();
}

function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}
'''

        with open(f"{output_dir}/assets/js/messaging.js", 'w', encoding='utf-8') as f:
            f.write(messaging_js)
