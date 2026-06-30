import React, { useState } from 'react';

function ChatBot() {
  const [messages, setMessages] = useState([
    { from: 'bot', text: 'Hi! How can I help you with this user story?' },
  ]);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;

    const newMessages = [...messages, { from: 'user', text: input }];
    setMessages(newMessages);
    setInput('');

    // Simulate bot response
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { from: 'bot', text: 'Thanks for your message! I’ll get back to you.' },
      ]);
    }, 1000);
  };

  return (
    <div style={styles.chatContainer}>
      <div style={styles.chatBox}>
        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              ...styles.message,
              alignSelf: msg.from === 'user' ? 'flex-end' : 'flex-start',
              backgroundColor: msg.from === 'user' ? '#007bff' : '#e0e0e0',
              color: msg.from === 'user' ? 'white' : 'black',
            }}
          >
            {msg.text}
          </div>
        ))}
      </div>
      <div style={styles.inputArea}>
        <input
          style={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
        />
        <button style={styles.sendButton} onClick={handleSend}>Send</button>
      </div>
    </div>
  );
}

const styles = {
  chatContainer: {
    width: '100%',
    maxWidth: '400px',
    display: 'flex',
    flexDirection: 'column',
    border: '1px solid #ccc',
    borderRadius: '8px',
    padding: '1rem',
    marginLeft: '2rem',
  },
  chatBox: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
    maxHeight: '300px',
    overflowY: 'auto',
    marginBottom: '1rem',
  },
  message: {
    padding: '0.5rem 1rem',
    borderRadius: '16px',
    maxWidth: '80%',
  },
  inputArea: {
    display: 'flex',
    gap: '0.5rem',
  },
  input: {
    flex: 1,
    padding: '0.5rem',
    borderRadius: '4px',
    border: '1px solid #ccc',
  },
  sendButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
};

export default ChatBot;
