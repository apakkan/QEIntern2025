import React from 'react';


function RelatedStoriesPage() {
  const relatedStories = [
    {
      id: 1,
      name: 'Story 1',
      description: 'Handles user login flow.',
      relationship: 92,
    },
    {
      id: 2,
      name: 'Story 2',
      description: 'Handles password reset.',
      relationship: 78,
    },
  ];

  const testCases = [
    {
      id: 'TC-101',
      title: 'Login with valid credentials',
      description: 'Ensures user can log in with correct username and password.',
      coverage: 95,
    },
    {
      id: 'TC-102',
      title: 'Reset password flow',
      description: 'Tests the password reset email and confirmation.',
      coverage: 88,
    },
  ];

  return (
    <div style={styles.container}>
      <h2>Related Stories</h2>
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
                <button style={styles.button}>View</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 style={{ marginTop: '2rem' }}>Test Cases</h2>
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
                <button style={styles.button}>Run</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div style={{ marginTop: '2rem' }}>
        <button style={styles.testButton}>Test Code</button>
      </div>
    </div>
  );
}

const styles = {
  container: {
    padding: '2rem',
    fontFamily: 'Arial, sans-serif',
  },
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
  testButton: {
    padding: '0.75rem 2rem',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontSize: '1rem',
    cursor: 'pointer',
  },
};

export default RelatedStoriesPage;
