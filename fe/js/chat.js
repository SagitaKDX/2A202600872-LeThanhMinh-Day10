// Chatbot Logic Controller
function initChat() {
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatHistory = document.getElementById("chat-history-list");

    if (!chatForm) return;

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const msgText = chatInput.value.trim();
        if (!msgText) return;

        // 1. Add User message bubble
        appendMessage("user", msgText);
        chatInput.value = "";
        
        // Scroll to bottom
        chatHistory.scrollTop = chatHistory.scrollHeight;

        // 2. Add Agent thinking bubble
        const thinkingId = appendThinkingIndicator();
        chatHistory.scrollTop = chatHistory.scrollHeight;

        // 3. Request reply from API
        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ message: msgText })
            });

            removeElement(thinkingId);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Server error occurred");
            }

            const data = await response.json();
            appendMessage("agent", data.response);
        } catch (error) {
            removeElement(thinkingId);
            appendMessage("agent", `⚠️ Sorry, I encountered an error: ${error.message}. Please check if your LLM model is configured and running.`);
        }

        chatHistory.scrollTop = chatHistory.scrollHeight;
    });
}

// Helper to Append Chat Message Bubbles
function appendMessage(sender, text) {
    const chatHistory = document.getElementById("chat-history-list");
    if (!chatHistory) return;

    const bubble = document.createElement("div");
    bubble.className = `message-bubble ${sender}`;

    const avatarHtml = sender === "agent" 
        ? `<div class="bubble-avatar"><i class="fa-solid fa-robot"></i></div>` 
        : `<div class="bubble-avatar"><i class="fa-solid fa-user-ninja"></i></div>`;

    bubble.innerHTML = `
        ${avatarHtml}
        <div class="bubble-content">
            <p>${escapeHtml(text)}</p>
        </div>
    `;

    chatHistory.appendChild(bubble);
}

// Helper to Append Thinking Indicator Bubble
function appendThinkingIndicator() {
    const chatHistory = document.getElementById("chat-history-list");
    if (!chatHistory) return "";

    const id = "thinking-" + Date.now();
    const bubble = document.createElement("div");
    bubble.className = "message-bubble agent";
    bubble.id = id;

    bubble.innerHTML = `
        <div class="bubble-avatar"><i class="fa-solid fa-robot"></i></div>
        <div class="bubble-content thinking-bubble">
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
        </div>
    `;

    chatHistory.appendChild(bubble);
    return id;
}

// Helper to remove DOM Elements safely
function removeElement(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// Click Handler for Suggestion Tags
function useSuggestion(text) {
    const input = document.getElementById("chat-input");
    const form = document.getElementById("chat-form");
    if (input && form) {
        input.value = text;
        // Trigger submit event
        form.dispatchEvent(new Event("submit"));
    }
}

// Utility to escape HTML text to prevent scripting injection issues
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    // Replace newlines with break tags for formatting
    return text.replace(/[&<>"']/g, m => map[m]).replace(/\n/g, "<br>");
}
