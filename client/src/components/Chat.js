import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom"; 

const Chat = ({ friend, chatHistory, currentUser }) => {
    const [messageInput, setMessageInput] = useState("");
    const chatHistoryRef = useRef(null);
    const navigate = useNavigate(); // Change 'history' to 'navigate'

    useEffect(() => {
        // Scroll to the bottom on component load
        if (chatHistoryRef.current) {
            chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
        }
    }, [chatHistory]);

    const handleMessageSend = (e) => {
        e.preventDefault();
        axios.post("/api/chat", { message: messageInput })
            .then((response) => {
                setMessageInput("");
                // Optionally handle successful message send
            })
            .catch((error) => {
                console.error("Error sending message:", error);
            });
    };

    const suggestMessage = () => {
        axios.post("/api/suggest_message")
            .then((response) => {
                if (response.data.suggestion) {
                    setMessageInput(response.data.suggestion);
                } else {
                    alert("Error: " + response.data.error);
                }
            })
            .catch((error) => {
                console.error("Error suggesting message:", error);
            });
    };

    return (
        <div id="chat-container">
            {/* Back button */}
            <button onClick={() => navigate('/friends')} className="back-button">
                Back to Friends
            </button>

            <h1>Chat with {friend.name}</h1>
            
            <div id="chat-history" ref={chatHistoryRef}>
                {chatHistory.reduce((acc, message, index) => {
                    const messageDate = new Date(message.timestamp).toDateString();
                    const lastMessageDate = index > 0 ? new Date(chatHistory[index - 1].timestamp).toDateString() : null;
                    
                    if (lastMessageDate !== messageDate) {
                        acc.push(
                            <div key={`date-${index}`} className="date-separator">
                                {messageDate}
                            </div>
                        );
                    }

                    acc.push(
                        <div key={message.id} className={`message ${message.sender_id === currentUser.id ? "sent" : "received"}`}>
                            <div className="meta">
                                {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </div>
                            <div className="text">{message.message}</div>
                        </div>
                    );
                    return acc;
                }, [])}
            </div>

            {/* Suggest Message Button */}
            <button type="button" id="suggest-button" onClick={suggestMessage}>
                Suggest a Message
            </button>

            {/* Chat input and send button */}
            <form onSubmit={handleMessageSend} id="message-input">
                <textarea
                    id="message-input-text"
                    name="message"
                    rows="2"
                    placeholder="Type your message here..."
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                />
                <button type="submit">Send</button>
            </form>
        </div>
    );
};

export default Chat;
