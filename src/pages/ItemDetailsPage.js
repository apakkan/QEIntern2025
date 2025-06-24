// src/pages/ItemDetailsPage.js
import React from 'react';
import { useParams } from 'react-router-dom';
import ChatBot from '../components/ChatBot';
import { useNavigate } from 'react-router-dom';

const mockData = [
  {
    id: 1,
    name: 'As a Case Worker, I want to intake a new Medicaid application so that I can begin the eligibility process.',
    functionality: 'Application Intake',
    description: 'Enable intake of new applications with basic applicant details.',
    priority: 'High',
  },
  {
    id: 2,
    name: 'As a Case Worker, I want to verify applicant identity using government ID so that I can ensure accurate records.',
    functionality: 'General Access & Eligibility',
    description: 'Integrate ID verification with DMV or SSA databases.',
    priority: 'Medium',
  },
  {
    id: 3,
    name: 'As a Case Worker, I want to check income eligibility using wage data so that I can determine financial qualification.',
    functionality: 'Eligibility Verification',
    description: 'Connect to income verification systems like The Work Number.',
    priority: 'Low',
  },
  {
    id: 4,
    name: 'As a Case Worker, I want to record household composition so that I can assess eligibility based on family size.',
    functionality: 'Eligibility Verification',
    description: 'Capture household members and their relationships.',
    priority: 'High',
  },
  {
    id: 5,
    name: 'As a Case Worker, I want to flag incomplete applications so that I can follow up with applicants.',
    functionality: 'Application Intake',
    description: 'System should highlight missing fields and documents.',
    priority: 'Medium',
  }
  
];

function ItemDetailsPage() {
  const { id } = useParams();
  const item = mockData.find((d) => d.id === parseInt(id));
  const navigate = useNavigate();


  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'High':
        return '#ff4d4f';
      case 'Medium':
        return '#faad14';
      case 'Low':
        return '#52c41a';
      default:
        return '#d9d9d9';
    }
  };

  if (!item) return <p style={{ padding: '2rem' }}>Item not found.</p>;

  return (
    <div style={{ display: 'flex', alignItems: 'flex-start' }}>
      <div style={{ flex: 1, padding: '2rem', fontFamily: 'Arial, sans-serif' }}>
        <h2>{item.name}</h2>
        <p><strong>ID:</strong> {item.id}</p>
        <p><strong>Description:</strong> {item.description}</p>
        <p><strong>Functionality:</strong> {item.functionality}</p>
        <p>
          <strong>Priority:</strong>{' '}
          <span style={{
            backgroundColor: getPriorityColor(item.priority),
            color: 'white',
            padding: '0.25rem 0.5rem',
            borderRadius: '4px'
          }}>
            {item.priority}
          </span>
        </p>
        <div style={{ marginTop: '2rem' }}>
          <button
            style={{ marginRight: '1rem', padding: '0.5rem 1rem', backgroundColor: '#ff4d4f', color: 'white', border: 'none', borderRadius: '4px' }}
            onClick={() => alert('This would delete the story')}
          >
            Delete
          </button>
          <button
            style={{ padding: '0.5rem 1rem', backgroundColor: '#1890ff', color: 'white', border: 'none', borderRadius: '4px' }}
            onClick={() => alert('This would refine the story')}
          >
            Refine
          </button>
        </div>
        <div style={{ marginTop: '1rem' }}>
  <button
    style={{
      padding: '0.5rem 1rem',
      backgroundColor: '#6c757d',
      color: 'white',
      border: 'none',
      borderRadius: '4px',
      cursor: 'pointer',
    }}
    onClick={() => navigate('/related-stories')}
  >
    View Related Stories & Test Cases
  </button>
</div>

      </div>
      <ChatBot />
    </div>
  );
}

export default ItemDetailsPage;
