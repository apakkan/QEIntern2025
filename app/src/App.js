import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import DetailsPage from './pages/DetailsPage';
import ItemDetailsPage from './pages/ItemDetailsPage';
import RelatedStoriesPage from './pages/RelatedStoriesPage';

//function for the app
//comment update
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/details" element={<DetailsPage />} />
        <Route path="/item/:id" element={<ItemDetailsPage />} />
        <Route path="*" element={<div>Not Found</div>} />
        <Route path="/related-stories" element={<RelatedStoriesPage />} />
      </Routes>
    </Router>
  );
}

export default App;
