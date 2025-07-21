import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ItemDetailsPage from './pages/ItemDetailsPage';
import './App.css';

const styles = {
  disabledSelect: {
    backgroundColor: '#f5f5f5',
    cursor: 'not-allowed',
    opacity: 0.7
  }
};

function App() {
  return (
    <Router>
      <header style={{
  backgroundColor: '#0070AD',
  color: '#fff',
  padding: '1rem 2rem',
  display: 'flex',
  alignItems: 'center'
}}>
  <img src="/logo192.png" alt="Capgemini Logo" style={{ height: '40px', marginRight: '1rem' }} />
  <h1 style={{ fontSize: '2rem', fontWeight: 700 }}>Tessy</h1>
</header>
      <Routes>
        <Route path="/" element={<Navigate to="/home" replace />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/item/:id" element={<ItemDetailsPage />} />
        <Route path="*" element={<div>Not Found</div>} />
      </Routes>
    </Router>
  );
}

export default App;