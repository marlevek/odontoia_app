// static/js/chat_odontoia.js
document.addEventListener("DOMContentLoaded", function () {
    // ======= ELEMENTOS =======
    const chatButton = document.createElement("button");
    const chatBox = document.createElement("div");
    const chatHeader = document.createElement("div");
    const chatMessages = document.createElement("div");
    const chatForm = document.createElement("form");
    const chatInput = document.createElement("input");
    const chatSend = document.createElement("button");
    const closeBtn = document.createElement("span");

    // ======= ESTILO =======
    chatButton.innerHTML = "💬";
    chatButton.id = "odontoia-chat-btn";
    Object.assign(chatButton.style, {
        position: "fixed", bottom: "25px", right: "25px", zIndex: "10000",
        border: "none", background: "#0b5394", color: "#fff", borderRadius: "50%",
        width: "60px", height: "60px", fontSize: "28px", cursor: "pointer",
        boxShadow: "0 4px 12px rgba(0,0,0,0.2)"
    });

    chatBox.id = "odontoia-chat";
    Object.assign(chatBox.style, {
        display: "none", position: "fixed", bottom: "90px", right: "25px",
        width: "340px", height: "460px", background: "#fff", border: "1px solid #ccc",
        borderRadius: "16px", boxShadow: "0 8px 18px rgba(0,0,0,0.2)",
        zIndex: "10000", display: "none", flexDirection: "column", overflow: "hidden"
    });

    Object.assign(chatHeader.style, {
        background: "#0b5394", color: "white", padding: "10px",
        display: "flex", justifyContent: "space-between", alignItems: "center"
    });
    chatHeader.innerHTML = "<strong>🤖 OdontoIA Assistente</strong>";

    closeBtn.innerHTML = "&times;";
    Object.assign(closeBtn.style, { cursor: "pointer", fontSize: "22px", marginLeft: "10px" });
    closeBtn.addEventListener("click", () => {
        chatBox.style.display = "none";
        chatButton.style.display = "block";
    });
    chatHeader.appendChild(closeBtn);

    Object.assign(chatMessages.style, {
        flex: "1", padding: "10px", overflowY: "auto", background: "#f8fafc"
    });
    chatMessages.innerHTML = "<div style='text-align:center;color:#777;'>💬 Como posso ajudar?</div>";

    Object.assign(chatForm.style, { display: "flex", padding: "10px", borderTop: "1px solid #ddd" });
    chatInput.type = "text";
    chatInput.placeholder = "Digite sua dúvida...";
    Object.assign(chatInput.style, {
        flex: "1", padding: "8px", border: "1px solid #ccc", borderRadius: "8px"
    });

    chatSend.innerText = "Enviar";
    chatSend.type = "submit";
    Object.assign(chatSend.style, {
        marginLeft: "8px", background: "#0b5394", color: "white", border: "none",
        padding: "8px 12px", borderRadius: "8px", cursor: "pointer"
    });

    chatForm.appendChild(chatInput);
    chatForm.appendChild(chatSend);
    chatBox.appendChild(chatHeader);
    chatBox.appendChild(chatMessages);
    chatBox.appendChild(chatForm);
    document.body.appendChild(chatButton);
    document.body.appendChild(chatBox);

    // ======= FUNÇÕES =======
    function addMessage(text, sender = "user") {
        const msg = document.createElement("div");
        Object.assign(msg.style, {
            margin: "6px 0", padding: "8px 10px", borderRadius: "10px",
            maxWidth: "80%", wordBreak: "break-word"
        });

        if (sender === "user") {
            Object.assign(msg.style, {
                background: "#0b5394", color: "white", alignSelf: "flex-end", marginLeft: "auto"
            });
        } else {
            Object.assign(msg.style, {
                background: "#e8eef7", color: "#222", alignSelf: "flex-start"
            });
        }
        msg.textContent = text;
        chatMessages.appendChild(msg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendMessageToAPI(message) {
        addMessage(message, "user");
        chatInput.value = "";

        const loading = document.createElement("div");
        loading.innerHTML = "<em>Digitando...</em>";
        loading.style.color = "#666";
        chatMessages.appendChild(loading);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch("/api/chat/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message }),
            });

            const isJSON = response.headers.get("content-type")?.includes("application/json");
            const data = isJSON ? await response.json() : {};

            loading.remove();

            if (response.ok && data.answer) {
                addMessage(data.answer, "bot");
            } else {
                const msg = data.error || `Erro HTTP ${response.status}`;
                console.error("Chat API error:", msg);
                addMessage(`❌ ${msg}`, "bot");
            }
        } catch (error) {
            loading.remove();
            console.error("Chat fetch error:", error);
            addMessage("⚠️ Não consegui responder agora. Tente novamente.", "bot");
        }
    }

    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const text = chatInput.value.trim();
        if (text !== "") sendMessageToAPI(text);
    });

    chatButton.addEventListener("click", () => {
        // abre o chat
        chatButton.style.display = "none";
        chatBox.style.display = "flex";
        chatInput.focus();
    });
});
