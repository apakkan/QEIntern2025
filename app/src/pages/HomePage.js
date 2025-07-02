import React, { useState, useEffect } from 'react';

function DetailsPage() {
  const [model, setModel] = useState('');
  const [project, setProject] = useState('');
  const [release, setRelease] = useState('');
  const [functionality, setFunctionality] = useState('');
  const [allData, setAllData] = useState([]);

 useEffect(() => {
    fetch("http://localhost:5000/api/requirements")
      .then(res => res.json())
      .then(data => setAllData(Array.isArray(data) ? data : []))
      .catch(err => setAllData([]));
 }, []);

  //dropdown
  const models = Array.from(new Set(allData.map(item => item.model))).filter(Boolean);
  const projects = Array.from(new Set(allData.map(item => item.project))).filter(Boolean);
  const releases = Array.from(new Set(allData.map(item => item.release))).filter(Boolean);
  const functionalities = Array.from(new Set(allData.map(item => item.functionality))).filter(Boolean);

  // Filtering
  const filteredData = Array.isArray(allData) ? allData.filter((item) => {
    return (
      (!model || item.model === model) &&
      (!project || item.project === project) &&
      (!release || item.release === release) &&
      (!functionality || item.functionality === functionality)
    );
  }) : [];

  return (
    <div style={styles.container}>
      <div style={styles.filterPanel}>
        {/* Model Dropdown */}
        <div style={styles.selectGroup}>
          <label style={styles.label}>Model:</label>
          <select value={model} onChange={e => setModel(e.target.value)} style={styles.select}>
            <option value="">-- Select Model --</option>
            {models.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
        {/* Project Dropdown */}
        <div style={styles.selectGroup}>
          <label style={styles.label}>Project Name:</label>
          <select value={project} onChange={e => setProject(e.target.value)} style={styles.select}>
            <option value="">-- Select Project --</option>
            {projects.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        {/* Release Dropdown */}
        <div style={styles.selectGroup}>
          <label style={styles.label}>Release:</label>
          <select value={release} onChange={e => setRelease(e.target.value)} style={styles.select}>
            <option value="">-- Select Release --</option>
            {releases.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
        {/* Functionality Dropdown */}
        <div style={styles.selectGroup}>
          <label style={styles.label}>Functionality:</label>
          <select value={functionality} onChange={e => setFunctionality(e.target.value)} style={styles.select}>
            <option value="">-- Select Functionality --</option>
            {functionalities.map(f => <option key={f} value={f}>{f}</option>)}
          </select>
        </div>
      </div>

      {/* Table */}
      <h3>Filtered Feature Table</h3>
      {filteredData.length > 0 ? (
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>ID</th>
              <th style={styles.th}>Item</th>
              <th style={styles.th}>Description</th>
              <th style={styles.th}>Model</th>
              <th style={styles.th}>Project</th>
              <th style={styles.th}>Release</th>
              <th style={styles.th}>Functionality</th>
              <th style={styles.th}></th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map(row => (
              <tr key={row.id}>
                <td style={styles.td}>{row.id}</td>
                <td style={styles.td}>{row.name}</td>
                <td style={styles.td}>{row.description || 'No description available'}</td>
                <td style={styles.td}>{row.model}</td>
                <td style={styles.td}>{row.project}</td>
                <td style={styles.td}>{row.release}</td>
                <td style={styles.td}>{row.functionality}</td>
                <td style={styles.td}>
                  <button style={styles.actionButton} onClick={() => window.location.href = `/item/${row.id}`}>
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>No matching data found.</p>
      )}
    </div>
  );
}

const styles = {
  container: {
   padding: '2rem',
    fontFamily: 'Ubuntu, Arial, sans-serif',
    backgroundColor: '#F6F6F6', // Light blue background
    minHeight: '100vh',
    boxSizing: 'border-box', 
  },
  filterPanel: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-start',
    marginBottom: '2rem',
    maxWidth: '450px',
    backgroundColor: '#ffffff', // White panel background
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,112,173,0.08)',
    padding: '1.5rem',
  },
  selectGroup: {
    display: 'flex',
    alignItems: 'center',
    marginBottom: '1rem',
    width: '100%',
  },
  label: {
    width: '160px', 
    marginRight: '0', 
    textAlign: 'left', 
    fontWeight: 'bold',
    display: 'inline-block',
    color: '#0070AD' // Capgemini Blue for labels
  },
  select: {
    marginLeft: '16px', 
    padding: '0.5rem',
    fontSize: '1rem',
    width: '250px',
    maxWidth: '250px',
    boxSizing: 'border-box',
    display: 'inline-block',
     border: '1px solid #0070AD', // Dark blue border
    borderRadius: '4px',
    backgroundColor: '#ffffff', // white
    color: '#003366',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    marginTop: '1rem',
    backgroundColor: '#ffffff', // White table background
    borderRadius: '8px',
    overflow: 'hidden',
    boxShadow: '0 2px 8px rgba(0,112,173,0.08)'
  },
  th: {
    border: '1px solid #ccc',
    padding: '0.75rem',
    backgroundColor: '#0070AD', // Capgemini Blue
    color: '#fff', // white text
    textAlign: 'left',
  },
  td: {
    border: '1px solid #ccc',
    padding: '0.75rem',
    textAlign: 'left',
    backgroundColor: '#f5faff', // light blue row
    color: 'black' // text
  },
  actionButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#0070AD',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: 'bold',
    transition: 'background 0.2s'
  },
};


export default DetailsPage;
