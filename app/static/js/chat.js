// Personal Finance Advisor Bot - Interactive AI Advisor Chat

document.addEventListener("DOMContentLoaded", function () {
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const chatMessages = document.getElementById("chatMessages");
  const sendBtn = document.getElementById("sendBtn");

  if (!chatForm || !chatInput || !chatMessages) return;

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
  scrollToBottom();

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.innerText = text;
    return div.innerHTML;
  }

  function formatMarkdown(text) {
    // Basic Markdown formatter for bold, bullets, headers
    let formatted = escapeHtml(text);
    // Bold
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    // Italics
    formatted = formatted.replace(/\*(.*?)\*/g, "<em>$1</em>");
    // Bullet lists
    formatted = formatted.replace(/^- (.*$)/gim, "<li>$1</li>");
    // Headers
    formatted = formatted.replace(/^### (.*$)/gim, "<h6 class='fw-bold mt-2 mb-1'>$1</h6>");
    formatted = formatted.replace(/^## (.*$)/gim, "<h5 class='fw-bold mt-2 mb-1'>$1</h5>");
    // Convert newlines
    formatted = formatted.replace(/\n/g, "<br>");
    return formatted;
  }

  function appendMessage(role, content, timeStr) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${role}`;
    
    if (role === "assistant") {
      bubble.innerHTML = `
        <div class="d-flex align-items-center gap-1 mb-1 text-primary fw-semibold small">
          <i class="bi bi-robot"></i> Financial Advisor
        </div>
        <div>${formatMarkdown(content)}</div>
        <div class="text-end text-muted mt-1" style="font-size: 0.72rem;">${timeStr || "Just now"}</div>
      `;
    } else {
      bubble.innerHTML = `
        <div>${escapeHtml(content)}</div>
        <div class="text-end text-light mt-1" style="font-size: 0.72rem; opacity: 0.85;">${timeStr || "Just now"}</div>
      `;
    }

    chatMessages.appendChild(bubble);
    scrollToBottom();
    return bubble;
  }

  chatForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (!message) return;

    // Display user message
    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    appendMessage("user", message, timeStr);

    chatInput.value = "";
    chatInput.disabled = true;
    sendBtn.disabled = true;

    // Add typing indicator
    const typingIndicator = document.createElement("div");
    typingIndicator.className = "chat-bubble assistant";
    typingIndicator.id = "typingIndicator";
    typingIndicator.innerHTML = `
      <div class="d-flex align-items-center gap-2 text-muted small">
        <span class="spinner-border spinner-border-sm" role="status"></span>
        <span>Analyzing your financial data...</span>
      </div>
    `;
    chatMessages.appendChild(typingIndicator);
    scrollToBottom();

    try {
      const response = await fetch("/advisor/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify({ message: message })
      });

      const indicator = document.getElementById("typingIndicator");
      if (indicator) indicator.remove();

      if (response.ok) {
        const data = await response.json();
        appendMessage("assistant", data.reply, data.created_at);
      } else {
        appendMessage("assistant", "I encountered an issue analyzing your request. Please try asking again in a moment.", "Now");
      }
    } catch (err) {
      const indicator = document.getElementById("typingIndicator");
      if (indicator) indicator.remove();
      appendMessage("assistant", "Unable to connect to financial advisory service. Please check your connection.", "Now");
    } finally {
      chatInput.disabled = false;
      sendBtn.disabled = false;
      chatInput.focus();
      scrollToBottom();
    }
  });

  // Handle prompt suggestions
  window.askQuickQuestion = function (questionText) {
    chatInput.value = questionText;
    chatForm.dispatchEvent(new Event("submit"));
  };
});
