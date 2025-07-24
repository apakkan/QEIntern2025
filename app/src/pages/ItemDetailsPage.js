import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

function ItemDetailsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showPopup, setShowPopup] = useState(false);
  const [relatedStories, setRelatedStories] = useState([]); // Initialize empty array
  const [testCases, setTestCases] = useState([]); // Initialize empty array
  const [testCaseLoading, setTestCaseLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const reqResponse = await fetch(`http://localhost:8000/requirements/${id}`);
        if (!reqResponse.ok) {
          if (reqResponse.status === 404) throw new Error('Requirement not found');
          throw new Error(`HTTP error! status: ${reqResponse.status}`);
        }
        const reqData = await reqResponse.json();
        setItem({
          id: reqData.id,
          name: reqData.user_story,
          description: reqData.description || 'No Description',
          functionality: reqData.functionality || 'Not Specified',
          risk_score: reqData.risk_score || 'Not Assessed',
          release: reqData.release || 'Not Set',
          project: reqData.project || 'Project 1'
        });

        const relatedResponse = await fetch(`http://localhost:8000/requirements/${id}/related-stories`);
        if (!relatedResponse.ok) throw new Error(`Error fetching related stories: ${relatedResponse.status}`);
        const relatedData = await relatedResponse.json();
        setRelatedStories(relatedData);

        setLoading(false);
      } catch (error) {
        setError(error.message);
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const getRiskColor = (riskScore) => {
    const score = parseInt(riskScore);
    if (isNaN(score)) return '#808080';
    if (score <= 3) return '#52c41a';
    if (score <= 7) return '#faad14';
    return '#ff4d4f';
  };

  const handleGenerateTestCases = async () => {
    setTestCaseLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/requirements/${item.id}/test-cases`);
      if (!response.ok) throw new Error('Failed to generate test cases');
      const data = await response.json();
      setTestCases(data);
      setShowPopup(false);
    } catch (error) {
      setError(error.message);
    }
    setTestCaseLoading(false);
  };

  const handleDownload = (type) => {
    setShowPopup(false);
    alert(`Download Test Cases as ${type}`);
  };

  const mappedTestCases = testCases.map(tc => ({
    id: tc.test_case_id || tc.id,
    title: tc.title,
    description: tc.test_description || tc.description,
    coverage: tc.coverage
  }));

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
      <div style={{
        width: '40px',
        height: '40px',
        border: '4px solid #f3f3f3',
        borderTop: '4px solid #0070AD',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite'
      }} />
      <span style={{ marginLeft: '1rem', color: '#0070AD' }}>Loading...</span>
    </div>
  );
  if (testCaseLoading) return <div style={{ padding: '2rem' }}>Generating test cases...</div>;
  if (error) return <div style={{ padding: '2rem' }}>Error: {error}</div>;
  if (!item) return <div style={{ padding: '2rem' }}>Item not found.</div>;

  return (
    <div style={styles.container}>
      <div style={{ display: 'flex', alignItems: 'flex-start' }}>
        <div style={{ flex: 1, padding: '2rem', fontFamily: 'Arial, sans-serif' }}>
          {/* Navigation Breadcrumb */}
          <nav style={{ marginBottom: '1rem', fontSize: '1rem', color: '#0070AD' }}>
            <button
              style={{
                backgroundColor: '#0070AD',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                fontWeight: 'bold',
                cursor: 'pointer',
                padding: '0.5rem 1rem',
                marginRight: '1rem'
              }}
              onClick={() => navigate(-1)}
            >
              Back
            </button>
            <span>{item?.name}</span>
          </nav>

          <h2>{item.name}</h2>
          <p><strong>ID:</strong> {item.id}</p>
          <p><strong>Description:</strong> {item.description}</p>
          <p><strong>Functionality:</strong> {item.functionality}</p>
          <p><strong>Project:</strong> {item.project}</p>
          <p><strong>Release:</strong> {item.release}</p>
          <p>
            <strong>Risk Score:</strong>{' '}
            <span style={{
              backgroundColor: getRiskColor(item.risk_score),
              color: item.risk_score === 'Not Assessed' ? 'black' : 'white',
              padding: '0.25rem 0.5rem',
              borderRadius: '4px',
              fontWeight: 'bold'
            }}>
              {item.risk_score}
            </span>
          </p>

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
              onClick={handleGenerateTestCases}
              disabled={testCaseLoading}
            >
              {testCaseLoading ? "Generating..." : "Generate Test Cases"}
            </button>
          </div>

          {/* Related Stories Table */}
          <h2 style={{ marginTop: '2rem' }}>Related Stories</h2>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>ID</th>
                <th style={styles.th}>Item</th>
                <th style={styles.th}>Description</th>
                <th style={styles.th}>Relationship %</th>
              </tr>
            </thead>
            <tbody>
              {relatedStories.map((story) => (
                <tr key={story.id}>
                  <td style={styles.td}>{story.id}</td>
                  <td style={styles.td}>{story.name}</td>
                  <td style={styles.td}>{story.description}</td>
                  <td style={styles.td}>{story.relationship}%</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Test Cases Table: Only show after Generating Test Cases */}
          {!testCaseLoading && testCases.length > 0 && (
            <>
              <h2 style={{ marginTop: '2rem' }}>Regression Test Cases</h2>
              <button
                style={{
                  marginBottom: '1rem',
                  padding: '0.5rem 1rem',
                  backgroundColor: '#0070AD',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                }}
                onClick={() => handleDownload('Excel/Word')}
              >
                Download Test Cases
              </button>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>Test Case ID</th>
                    <th style={styles.th}>Title</th>
                    <th style={styles.th}>Description</th>
                    <th style={styles.th}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {mappedTestCases.map((test) => (
                    <tr key={test.id}>
                      <td style={styles.td}>{test.id}</td>
                      <td style={styles.td}>{test.title}</td>
                      <td style={styles.td}>{test.description}</td>
                      <td style={styles.td}>
                        <button
                          title="Run this test case"
                          style={{
                            backgroundColor: '#0070AD',
                            color: '#fff',
                            border: 'none',
                            borderRadius: '4px',
                            fontWeight: 'bold',
                            cursor: 'pointer',
                            padding: '0.5rem 1rem'
                          }}
                        >
                          Run
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    backgroundColor: '#f5faff',
    minHeight: '100vh',
    padding: '2rem',
    fontFamily: 'Ubuntu, Arial, sans-serif',
    color: '#003366'
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    marginTop: '1rem',
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    overflow: 'hidden',
    boxShadow: '0 2px 8px rgba(0,112,173,0.08)'
  },
  th: {
    backgroundColor: '#0070AD',
    color: '#fff',
    border: 'none',
    padding: '0.75rem',
    textAlign: 'left'
  },
  td: {
    backgroundColor: '#f5faff',
    color: '#003366',
    border: 'none',
    padding: '0.75rem',
    textAlign: 'left'
  },
  actionButton: {
    backgroundColor: '#0070AD',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontWeight: 'bold',
    cursor: 'pointer',
    padding: '0.5rem 1rem'
  }
};

export default ItemDetailsPage;
