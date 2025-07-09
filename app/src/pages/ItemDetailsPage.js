import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

function ItemDetailsPage() {
  const { id } = useParams();
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showPopup, setShowPopup] = useState(false);
  const [relatedStories, setRelatedStories] = useState([]); // Initialize empty array
  const [testCases, setTestCases] = useState([]); // Initialize empty array

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch requirement details
        console.log('Fetching requirement details for ID:', id);
        const reqResponse = await fetch(`http://localhost:8000/requirements/${id}`);
        
        if (!reqResponse.ok) {
          if (reqResponse.status === 404) {
            throw new Error('Requirement not found');
          }
          throw new Error(`HTTP error! status: ${reqResponse.status}`);
        }
        
        const reqData = await reqResponse.json();
        setItem({
          id: reqData.id,
          name: reqData.user_story,
          description: reqData.description || 'No Description',
          functionality: reqData.functionality || 'Not Specified',
          priority: reqData.priority || 'Not Set',
          release: reqData.release || 'Not Set',
          project: reqData.project || 'Core System'
        });

        // Fetch related stories
        console.log('Fetching related stories...');
        const relatedResponse = await fetch(`http://localhost:8000/requirements/${id}/related-stories`);
        if (!relatedResponse.ok) {
          throw new Error(`Error fetching related stories: ${relatedResponse.status}`);
        }
        const relatedData = await relatedResponse.json();
        console.log('Found related stories:', relatedData);
        setRelatedStories(relatedData);
        
        setLoading(false);
      } catch (error) {
        console.error('Error:', error);
        setError(error.message);
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const getPriorityColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'high':
        return '#ff4d4f';
      case 'medium':
        return '#faad14';
      case 'low':
        return '#52c41a';
      default:
        return '#d9d9d9';
    }
  };

  if (loading) return <div style={{ padding: '2rem' }}>Loading...</div>;
  if (error) return <div style={{ padding: '2rem' }}>Error: {error}</div>;
  if (!item) return <div style={{ padding: '2rem' }}>Item not found.</div>;

  const handleDownload = (type) => {
    setShowPopup(false);
    alert(`Download Test Cases as ${type}`);
    //backend download logic here
  };
  const handleInsertDB = () => {
    setShowPopup(false);
    alert('Insert Test Cases into Database');
    //backend insert logic here
  };

  return (
    <div style={{ display: 'flex', alignItems: 'flex-start' }}>
      <div style={{ flex: 1, padding: '2rem', fontFamily: 'Arial, sans-serif' }}>
        <h2>{item.name}</h2>
        <p><strong>ID:</strong> {item.id}</p>
        <p><strong>Description:</strong> {item.description}</p>
        <p><strong>Functionality:</strong> {item.functionality}</p>
        <p><strong>Project:</strong> {item.project}</p>
        <p><strong>Release:</strong> {item.release}</p>
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
            style={{
              marginRight: '1rem',
              padding: '0.5rem 1rem',
              backgroundColor: '#ff4d4f',
              color: 'white',
              border: 'none',
              borderRadius: '4px'
            }}
            onClick={() => alert('This would delete the story')}
          >
            Delete
          </button>
          <button
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#0070AD', // Capgemini Blue
              color: 'white',
              border: 'none',
              borderRadius: '4px'
            }}
            onClick={() => alert('This would refine the story')}
          >
            Refine
          </button>
        </div>

      {/*TC Generation*/}
      <div style={{ marginTop: '2rem' }}>
          <button
            style={{
              padding: '0.5rem 1.5rem',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '1rem',
              cursor: 'pointer'
            }}
            onClick={() => setShowPopup(true)}
          >
            Generate Test Cases
          </button>
          </div>
          
        {/* Popup for Test Case Creation*/}
        {showPopup && (
          <div style={popupStyles.overlay}>
            <div style={popupStyles.popup}>
              <button
                style={popupStyles.button}
                onClick={() => handleDownload('Excel/Word')}
              >
                Download in Excel or Word
              </button>
              <button
                style={popupStyles.button}
                onClick={handleInsertDB}
              >
                Insert in Database
              </button>
              <button
                style={popupStyles.close}
                onClick={() => setShowPopup(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Related Stories Table */}
        <h2 style={{ marginTop: '2rem' }}>Related Stories</h2>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>ID</th>
              <th style={styles.th}>Item</th>
              <th style={styles.th}>Description</th>
              <th style={styles.th}>Relationship %</th>
              <th style={styles.th}>Action</th>
            </tr>
          </thead>
          <tbody>
            {relatedStories.map((story) => (
              <tr key={story.id}>
                <td style={styles.td}>{story.id}</td>
                <td style={styles.td}>{story.name}</td>
                <td style={styles.td}>{story.description}</td>
                <td style={styles.td}>{story.relationship}%</td>
                <td style={styles.td}>
                  <button
                    style={{
                      ...styles.button,
                      backgroundColor: '#0070AD', // Capgemini Blue for View
                    }}
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Test Cases Table */}
        <h2 style={{ marginTop: '2rem' }}>Regression Test Cases</h2>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Test Case ID</th>
              <th style={styles.th}>Title</th>
              <th style={styles.th}>Description</th>
              <th style={styles.th}>Coverage %</th>
              <th style={styles.th}>Action</th>
            </tr>
          </thead>
          <tbody>
            {testCases.map((test) => (
              <tr key={test.id}>
                <td style={styles.td}>{test.id}</td>
                <td style={styles.td}>{test.title}</td>
                <td style={styles.td}>{test.description}</td>
                <td style={styles.td}>{test.coverage}%</td>
                <td style={styles.td}>
                  <button
                    style={{
                      ...styles.button,
                      backgroundColor: '#0070AD', // Capgemini Blue for Run
                    }}
                  >
                    Run
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* ChatBot Component */}
    </div>
  );
}

const styles = {
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    marginTop: '1rem',
  },
  th: {
    border: '1px solid #ccc',
    padding: '0.75rem',
    backgroundColor: '#f0f0f0',
    textAlign: 'left',
  },
  td: {
    border: '1px solid #ccc',
    padding: '0.75rem',
    textAlign: 'left',
  },
  button: {
    padding: '0.5rem 1rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
};

const popupStyles = {
  overlay: {
    position: 'fixed',
    top: 0, left: 0, right: 0, bottom: 0,
    background: 'rgba(0,0,0,0.3)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  popup: {
    background: 'white',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 2px 12px rgba(0,0,0,0.2)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    minWidth: '320px',
  },
  button: {
    margin: '1rem 0',
    padding: '0.75rem 1.5rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '1rem',
    cursor: 'pointer',
    width: '100%',
  },
  close: {
    marginTop: '1rem',
    padding: '0.5rem 1.5rem',
    backgroundColor: '#888',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '1rem',
    cursor: 'pointer',
    width: '100%',
  }
};

export default ItemDetailsPage;
