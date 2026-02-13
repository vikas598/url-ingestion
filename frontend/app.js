const API_BASE = "http://localhost:8000/api/v1";

// --- CART LOGIC ---
let cart = JSON.parse(localStorage.getItem('cart')) || [];

function updateCartUI() {
    const el = document.getElementById('cart-count');
    if (el) el.innerText = `Cart (${cart.length})`;
}

function addToCart(product) {
    cart.push(product);
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartUI();
    alert(`Added "${product.title}" to cart!`);
}

// Initial update on load
document.addEventListener('DOMContentLoaded', updateCartUI);

// --- TABS ---
function switchTab(tabId) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

    // Show selected
    document.getElementById(`${tabId}-tab`).classList.add('active');

    // Find button to highlight
    const buttons = document.querySelectorAll('.nav-item');
    if (tabId === 'chat') buttons[0].classList.add('active');
    if (tabId === 'search') buttons[1].classList.add('active');
    if (tabId === 'scraper') buttons[2].classList.add('active');
}

// --- CHAT ---
const chatHistory = document.getElementById('chat-history');
const chatInput = document.getElementById('chat-input');

// Product Type Preference
let currentProductType = null;

function updateProductTypePreference() {
    const select = document.getElementById('product-type-select');
    currentProductType = select.value || null;
    console.log('Product type preference updated:', currentProductType);
}

function handleChatKey(e) {
    if (e.key === 'Enter') sendMessage();
}

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    // Add user message
    appendMessage('User', text, true);
    chatInput.value = '';

    // Show typing indicator
    const typingElement = showTypingIndicator();

    try {
        const res = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                product_type: currentProductType
            })
        });

        const data = await res.json();

        // Remove typing indicator
        removeTypingIndicator(typingElement);

        if (data.response) {
            appendMessage('AI', data.response, false, data.products || []);
        } else {
            appendMessage('AI', 'Error: ' + JSON.stringify(data), false);
        }

    } catch (err) {
        removeTypingIndicator(typingElement);
        appendMessage('AI', 'Network Error: ' + err.message, false);
    }
}

function showTypingIndicator() {
    const div = document.createElement('div');
    div.className = 'message ai-message typing-indicator-container';
    div.innerHTML = `
        <div class="avatar">AI</div>
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return div;
}

function removeTypingIndicator(element) {
    if (element && element.parentNode) {
        element.parentNode.removeChild(element);
    }
}

function appendMessage(sender, text, isUser, products = []) {
    const div = document.createElement('div');
    div.className = `message ${isUser ? 'user-message' : 'ai-message'}`;

    // Format markdown: bold and newlines
    const formattedText = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');

    let productsHtml = '';

    if (products && products.length > 0) {
        productsHtml = `<div class="chat-products-grid">`;
        products.forEach((p, index) => {
            console.log(`Product ${index}:`, p); // Debug: check product structure
            // Encode product object for onclick safely
            const productJson = JSON.stringify(p).replace(/"/g, '&quot;');

            const imageUrl = p.images && p.images.length > 0 ? p.images[0].url : null;
            console.log(`Image URL for ${p.title}:`, imageUrl); // Debug: check image URL

            productsHtml += `
                <div class="chat-product-card">
                    ${imageUrl ? `<img src="${imageUrl}" class="chat-product-image" alt="${p.title}" onerror="console.error('Failed to load image:', this.src)">` : '<div class="chat-product-image" style="background-color:#555;display:flex;align-items:center;justify-content:center;color:#999;font-size:10px;">No Image</div>'}
                    <div class="chat-product-title">${p.title}</div>
                    <div class="chat-product-price">₹${p.pricing?.price || (p.variants && p.variants.length > 0 ? p.variants[0].price : 'N/A')}</div>
                    <button class="add-to-cart-btn" onclick="addToCart(${productJson})">
                        Add to Cart
                    </button>
                    ${p.source_url ? `<a href="${p.source_url}" target="_blank" style="font-size:12px; color:#10A37F; text-decoration:none; display:block; margin-top:5px;">View Details &rarr;</a>` : ''}
                </div>
            `;
        });
        productsHtml += `</div>`;
    }

    div.innerHTML = `
        <div class="avatar">${isUser ? 'U' : 'AI'}</div>
        <div class="content">
            ${formattedText}
            ${productsHtml}
        </div>
    `;

    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// --- SEARCH ---
async function performSearch() {
    const query = document.getElementById('search-input').value;
    const resultsContainer = document.getElementById('search-results');

    resultsContainer.innerHTML = '<p>Searching...</p>';

    try {
        const res = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        const data = await res.json();
        const results = data.results || [];

        resultsContainer.innerHTML = '';

        if (results.length === 0) {
            resultsContainer.innerHTML = '<p>No results found.</p>';
            return;
        }

        results.forEach(item => {
            const card = document.createElement('div');
            card.className = 'result-card';

            // Handle different result structures (metadata vs direct)
            const title = item.metadata?.title || item.title || 'Unknown Product';
            const desc = item.metadata?.description || item.description || 'No description';
            const score = item.score ? `Score: ${item.score.toFixed(4)}` : '';

            card.innerHTML = `
                <h3>${title}</h3>
                <p>${desc.substring(0, 150)}...</p>
                <div class="result-meta">${score}</div>
            `;
            resultsContainer.appendChild(card);
        });

    } catch (err) {
        resultsContainer.innerHTML = `<p style="color:red">Error: ${err.message}</p>`;
    }
}

// --- SCRAPER ---
async function scrape(type) {
    const url = document.getElementById('scrape-url').value;
    const log = document.getElementById('scrape-status');

    if (!url) {
        alert('Please enter a URL');
        return;
    }

    log.innerText = `Starting ${type} scrape for ${url}...\n`;

    let endpoint = '';
    if (type === 'product') endpoint = '/millex/scrape/product';
    if (type === 'collection') endpoint = '/millex/scrape/collection';
    if (type === 'homepage') endpoint = '/millex/scrape/homepage';

    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        const data = await res.json();
        log.innerText += JSON.stringify(data, null, 2);

    } catch (err) {
        log.innerText += `\nError: ${err.message}`;
    }
}
