// src/pages/HomePage.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function HomePage() {
  const navigate = useNavigate();
  const [selectedModel, setSelectedModel] = useState('');

  const handleSubmit = () => {
    if (selectedModel) {
      navigate('/details', { state: { model: selectedModel } });
    } else {
      alert('Please select a model.');
    }
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Select a Model</h1>
      <select
        style={styles.select}
        value={selectedModel}
        onChange={(e) => setSelectedModel(e.target.value)}
      >
        <option value="">-- Choose a model --</option>
        <option value="gpt-4o">GPT-4o</option>
        <option value="gpt-4">GPT-4</option>
        <option value="gpt-3.5">GPT-3.5</option>
      </select>
      <br />
      <button style={styles.button} onClick={handleSubmit}>
        Continue
      </button>
    </div>
  );
}

const styles = {
  container: {
    textAlign: 'center',
    padding: '4rem',
    fontFamily: 'Arial, sans-serif',
  },
  title: {
    fontSize: '2rem',
    marginBottom: '2rem',
  },
  select: {
    padding: '0.5rem',
    fontSize: '1rem',
    marginBottom: '1rem',
    width: '200px',
  },
  button: {
    padding: '0.75rem 1.5rem',
    fontSize: '1rem',
    cursor: 'pointer',
    borderRadius: '6px',
    border: '1px solid #ccc',
    backgroundColor: '#007bff',
    color: 'white',
  },
};

export default HomePage;
