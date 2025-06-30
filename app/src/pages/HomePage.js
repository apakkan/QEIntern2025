import React, { useState } from 'react';

function DetailsPage() {
  const [release, setRelease] = useState('');
  const [functionality, setFunctionality] = useState('');

  const allData = [
  {
    id: 1,
    name: 'As a Case Worker, I want to intake a new Medicaid application so that I can begin the eligibility process.',
    release: 'Sprint 1',
    type: 'Story Only',
    functionality: 'Application Intake',
    description: 'Enable intake of new applications with basic applicant details.',
    priority: 'High',
  },
  {
    id: 2,
    name: 'As a Case Worker, I want to verify applicant identity using government ID so that I can ensure accurate records.',
    release: 'Sprint 2',
    type: 'Advanced',
    functionality: 'General Access & Eligibility',
    description: 'Integrate ID verification with DMV or SSA databases.',
    priority: 'Medium',
  },
  {
    id: 3,
    name: 'As a Case Worker, I want to check income eligibility using wage data so that I can determine financial qualification.',
    release: 'Sprint 3',
    type: 'Story Only',
    functionality: 'Eligibility Verification',
    description: 'Connect to income verification systems like The Work Number.',
    priority: 'Low',
  },
  {
    id: 4,
    name: 'As a Case Worker, I want to record household composition so that I can assess eligibility based on family size.',
    release: 'Sprint 1',
    type: 'Advanced',
    functionality: 'Eligibility Verification',
    description: 'Capture household members and their relationships.',
    priority: 'High',
  },
  {
    id: 5,
    name: 'As a Case Worker, I want to flag incomplete applications so that I can follow up with applicants.',
    release: 'Sprint 2',
    type: 'Story Only',
    functionality: 'Application Intake',
    description: 'System should highlight missing fields and documents.',
    priority: 'Medium',
  }, 

];
const functionalityImpactData = [
  { id: 1, functionality: 'Application Intake', risk: 'High' },
  { id: 2, functionality: 'General Access & Eligibility', risk: 'Medium' },
  { id: 3, functionality: 'Eligibility Verification', risk: 'Low' },
];

  const filteredData = allData.filter((item) => {
    return (
      (!release || item.release === release) &&
      (!functionality || item.functionality === functionality)
    );
  });

  return (
  <div style={styles.container}>
    <div style={styles.filterPanel}>
      <div style={styles.selectGroup}>
        <label style={styles.label}>Model:</label>
        <select value={release} onChange={(e) => setRelease(e.target.value)} style={styles.select}>
          <option value="">-- Select Model --</option>
          <option value="gpt-4o">gpt-4o</option>
          <option value="gpt-4">gpt-4</option>
          <option value="gpt-3.5">gpt-3.5</option>
        </select>
      </div>

      <div style={styles.selectGroup}>
        <label style={styles.label}>Project Name:</label>
        <select value={release} onChange={(e) => setRelease(e.target.value)} style={styles.select}>
          <option value="">-- Select Project --</option>
          <option value="Project X">Project X</option>
          <option value="Project Y">Project Y</option>
          <option value="Project Z">Project Z</option>
        </select>
      </div>

      <div style={styles.selectGroup}>
        <label style={styles.label}>Release:</label>
        <select value={release} onChange={(e) => setRelease(e.target.value)} style={styles.select}>
          <option value="">-- Select Release --</option>
          <option value="Sprint 1">Sprint 1</option>
          <option value="Sprint 2">Sprint 2</option>
          <option value="Sprint 3">Sprint 3</option>
        </select>
      </div>
 
      <div style={styles.selectGroup}>
        <label style={styles.label}>Functionality:</label>
        <select value={functionality} onChange={(e) => setFunctionality(e.target.value)} style={styles.select}>
          <option value="">-- Select Functionality --</option>
          <option value="Application Intake">Application Intake</option>
          <option value="General Access & Eligibility">General Access & Eligibility</option>
          <option value="Eligibility Verification">Eligibility Verification</option>
          <option value="Document Management">Document Management</option>
          <option value="Case Management">Case Management</option>
          <option value="Client Communication">Client Communication</option>
          <option value="Reporting & Audit">Reporting & Audit</option>
          <option value="Alerts & Notifications">Alerts & Notifications</option>
        </select>
      </div>
    </div>


    <h3>Filtered Feature Table</h3>
{filteredData.length > 0 ? (
 <table style={styles.table}>
  <thead>
    <tr>
      <th style={styles.th}>ID</th>
      <th style={styles.th}>Item</th>
      <th style={styles.th}>Description</th>
      <th style={styles.th}>Functionality</th>
      <th style={styles.th}>Risk Score</th>
      <th style={styles.th}></th>
    </tr>
  </thead>
  <tbody>
    {filteredData.length > 0 ? (
      filteredData.map((row) => {
        const impact = functionalityImpactData.find(
          (f) => f.functionality === row.functionality
        );
        return (
          <tr key={row.id}>
        <td style={styles.td}>{row.id}</td>
        <td style={styles.td}>{row.name}</td>
        <td style={styles.td}>{row.description || 'No description available'}</td>
        <td style={styles.td}>{row.functionality}</td>
        <td style={styles.td}>{impact ? impact.risk : 'N/A'}</td>
        <td style={styles.td}>
          <button style={styles.actionButton} onClick={() => window.location.href = `/item/${row.id}`}>
            View
          </button>
        </td>
      </tr>
        );
      })
    ) : (
      <tr>
        <td stylee={styles.td} colSpan={6}>No matching data found.</td>
      </tr>
    )}
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
