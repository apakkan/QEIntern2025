import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ItemDetailsPage from './pages/ItemDetailsPage';
import './App.css';

const styles = {
  header: {
    background: 'linear-gradient(90deg, #0070AD 30%, #12ABDB 70%)',
    color: '#fff',
    padding: '1rem 2rem',
    display: 'flex',
    alignItems: 'center',
    borderRadius: '0 0 8px 8px',
    boxShadow: '0 2px 8px rgba(0,112,173,0.08)',
  }
};

function App() {
  //reload
  useEffect(() => {
    localStorage.removeItem('homepageState');
    localStorage.removeItem('hasSeenWelcome');
  }, []);

  return (
    <Router>
      <header style={{
        background: 'linear-gradient(90deg, #0070AD 0%, #12ABDB 100%)',
        color: '#fff',
        padding: '1rem 2rem',
        display: 'flex',
        alignItems: 'center',
        borderRadius: '0 0 8px 8px',
        boxShadow: '0 2px 8px rgba(0,112,173,0.08)',
      }}>
        <img
          src="Capgemini_Spade_White_Mono_RGB.png"
          alt="Capgemini Logo"
          style={{ height: '40px', marginRight: '1rem' }}
        />
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