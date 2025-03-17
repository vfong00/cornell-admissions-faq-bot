document.getElementById("send-btn").addEventListener("click", sendMessage);

document.getElementById("user-input").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
});

window.onload = function () {
    setTimeout(() => {
        addMessage("Hello! How can I help you today?", "bot");
    }, 1000);
};

function sendMessage() {
    let inputField = document.getElementById("user-input");
    let message = inputField.value.trim();
    if (!message) return;

    addMessage(message, "user");
    fetch("/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: message }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.answer) {
            addMessage(data.answer, "bot", message);
        } else {
            addMessage("Sorry, I don't have a good answer to this question. Please try rephrasing it or consulting <a href='https://faq.enrollment.cornell.edu' target='_blank'>our page</a> for more help.", "bot");
        }
    })
    .catch(error => {
        console.error("Error:", error);
        addMessage("An error occurred. Please try again.", "bot");
    });

    inputField.value = "";
}

function addMessage(text, sender, query = "") {
    let chatBox = document.getElementById("chat-box");
    let messageDiv = document.createElement("div");
    messageDiv.classList.add("chat-message", sender, "fade-in");
    messageDiv.innerHTML = text;

    chatBox.appendChild(messageDiv);

    if (sender === "bot" && query) {
        let feedbackDiv = document.createElement("div");
        feedbackDiv.classList.add("feedback-buttons");

        let thumbsUp = document.createElement("button");
        thumbsUp.innerHTML = "🔺";
        thumbsUp.onclick = () => sendFeedback(query, text, 1);

        let thumbsDown = document.createElement("button");
        thumbsDown.innerHTML = "🔻";
        thumbsDown.onclick = () => sendFeedback(query, text, 0);

        feedbackDiv.appendChild(thumbsUp);
        feedbackDiv.appendChild(thumbsDown);
        messageDiv.appendChild(feedbackDiv);
    }

    chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "smooth" });
}

function sendFeedback(query, answer, feedbackType) {
    fetch("/log_feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            query: query,
            answer: answer,
            feedback: feedbackType
        }),
    })
    .then(response => response.json())
    .then(data => console.log("Feedback received:", data.message))
    .catch(error => console.error("Error logging feedback:", error));
}