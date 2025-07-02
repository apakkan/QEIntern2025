import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ItemDetailsPage from './pages/ItemDetailsPage';
import RelatedStoriesPage from './pages/RelatedStoriesPage';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/item/:id" element={<ItemDetailsPage />} />
        <Route path="*" element={<div>Not Found</div>} />
        <Route path="/related-stories" element={<RelatedStoriesPage />} />
      </Routes>
    </Router>
  );
}

export default App;
