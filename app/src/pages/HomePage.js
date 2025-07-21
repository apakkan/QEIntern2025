import React, { useState, useEffect } from 'react';

function DetailsPage() {
  const [model, setModel] = useState('');
  const [project, setProject] = useState('');
  const [functionality, setFunctionality] = useState('');
  // Removed release filter
  const [requirements, setRequirements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dbStatus, setDbStatus] = useState(null);

  // Add new state variables for dropdown options
  const [modelOptions, setModelOptions] = useState(['OpenAI']);
  const [projectOptions, setProjectOptions] = useState([]);
  // Removed releaseOptions state
  const [functionalityOptions, setFunctionalityOptions] = useState([]);
  const [sortRiskHighToLow, setSortRiskHighToLow] = useState(false); // Risk sort
  const [sortSprintAsc, setSortSprintAsc] = useState(false); // Sprint sort

  useEffect(() => {
    const checkDatabaseStatus = async () => {
      try {
        console.log('Checking database status...');
        const response = await fetch('http://localhost:8000/');
        const data = await response.json();
        console.log('Database status:', data);
        setDbStatus(data);
        
        if (data.database_initialized) {
          console.log('Database initialized');
          return true;
        }
        throw new Error(`Database not properly initialized: ${JSON.stringify(data)}`);
      } catch (error) {
        console.error('Database check failed:', error);
        setError(`Database connection failed: ${error.message}. Please ensure the backend is running.`);
        setLoading(false);
        return false;
      }
    };

    // Add function to extract unique values for dropdowns
    const updateDropdownOptions = (data) => {
      const uniqueModels = [...new Set(data.map(req => req.model).filter(Boolean))];
      const uniqueProjects = [...new Set(data.map(req => req.project).filter(Boolean))];
      // Removed uniqueSprints extraction
      const uniqueFunctionalities = [...new Set(data.map(req => req.functionality).filter(Boolean))];

      setModelOptions(uniqueModels);
      setProjectOptions(uniqueProjects);
      // Removed setReleaseOptions
      setFunctionalityOptions(uniqueFunctionalities);
    };

 const fetchRequirements = async () => {
  try {
    console.log('Fetching requirements...');
    const response = await fetch('http://localhost:8000/requirements/');
    const data = await response.json();

    console.log('Raw API response:', data); 

    if (!Array.isArray(data)) {
      console.error('API returned non-array data:', data);
      setRequirements([]);
      setLoading(false);
      return;
    }

    const transformedData = data.map(req => ({
      id: req.id,
      title: req.user_story || 'Untitled',
      description: req.description || 'No Description',
      functionality: req.functionality || 'Not Specified',
      release: req.release || 'Not Set',
      risk_score: req.risk_score || 'Not Assessed',
      model: 'OpenAI',
      project: 'Project 1'
    }));

    console.log('Transformed data:', transformedData); // <-- ADD THIS

    setRequirements(transformedData);
    const uniqueFunctionalities = [...new Set(transformedData
      .map(req => req.functionality)
      .filter(f => f && f !== 'Not Specified'))];
    setFunctionalityOptions(uniqueFunctionalities);
    setLoading(false);
  } catch (error) {
    console.error('Error fetching requirements:', error);
    setError(error.message);
    setLoading(false);
  }
};

    const initializeData = async () => {
      const dbReady = await checkDatabaseStatus();
      if (dbReady) {
        await fetchRequirements();
      }
    };

    initializeData();
  }, []);
  

  const areSelectionsComplete = () => {
  const isComplete = model === 'OpenAI' && project === 'Project 1';
  console.log('Selection Check:', { 
    model, 
    project, 
    isComplete,
    requirementsCount: requirements.length,
    loading,
    error
  });
  return isComplete;
};

  let filteredRequirements = requirements.filter(req => {
    if (!areSelectionsComplete()) {
      return false;
    }
    const functionalityMatch = !functionality || 
      (req.functionality && req.functionality.toLowerCase() === functionality.toLowerCase());
    return functionalityMatch;
  });

  // Sort by risk score high to low if enabled
  if (sortRiskHighToLow) {
    filteredRequirements = [...filteredRequirements].sort((a, b) => {
      const scoreA = isNaN(parseInt(a.risk_score)) ? -1 : parseInt(a.risk_score);
      const scoreB = isNaN(parseInt(b.risk_score)) ? -1 : parseInt(b.risk_score);
      return scoreB - scoreA;
    });
  }

  // Sort by sprint (release) ascending if enabled
  if (sortSprintAsc) {
    filteredRequirements = [...filteredRequirements].sort((a, b) => {
      // Extract sprint number from release string
      const sprintA = a.release && /^Sprint\s*(\d+)$/i.test(a.release) ? parseInt(a.release.match(/^Sprint\s*(\d+)$/i)[1]) : 9999;
      const sprintB = b.release && /^Sprint\s*(\d+)$/i.test(b.release) ? parseInt(b.release.match(/^Sprint\s*(\d+)$/i)[1]) : 9999;
      return sprintA - sprintB;
    });
  }

console.log('Filtered requirements:', filteredRequirements); // <-- ADD THIS
  if (loading) {
    console.log('Loading requirements...');
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  // Add this helper function near the top of the DetailsPage component
  const getRiskColor = (riskScore) => {
    const score = parseInt(riskScore);
    if (isNaN(score)) return '#808080'; // gray for "Not Assessed"
    if (score <= 3) return '#52c41a';   // green for low risk (1-3)
    if (score <= 7) return '#faad14';   // yellow for medium risk (4-7)
    return '#ff4d4f';                   // red for high risk (8-10)
  };

  const handleModelChange = (e) => {
    const value = e.target.value;
    console.log('Setting model to:', value);
    setModel(value);
    setFunctionality('');
  };

  const handleProjectChange = (e) => {
    const value = e.target.value;
    console.log('Setting project to:', value);
    setProject(value);
    setFunctionality('');
  };

  // Removed handleReleaseChange

  const handleSortRiskChange = (e) => {
    setSortRiskHighToLow(e.target.checked);
  };

  const handleSortSprintChange = (e) => {
    setSortSprintAsc(e.target.checked);
  };

  const handleFunctionalityChange = (e) => {
    const value = e.target.value;
    console.log('Functionality selected:', value);
    setFunctionality(value);
  };

  return (
    <div style={styles.container}>
      {console.log('Render State:', {
      model,
      project,
      functionality,
      requirementsCount: requirements.length,
      filteredCount: filteredRequirements.length,
      loading,
      error,
      selectionsComplete: areSelectionsComplete()
    })}
      <div style={styles.filterPanel}>
        <div style={styles.selectGroup}>
          <label style={styles.label}>Model:</label>
          <select value={model} onChange={handleModelChange} style={styles.select}>
            <option value="">-- Select Model --</option>
            <option value="OpenAI">OpenAI</option>
          </select>
        </div>

        <div style={styles.selectGroup}>
          <label style={styles.label}>Project Name:</label>
          <select 
            value={project} 
            onChange={handleProjectChange} 
            style={styles.select}
          >
            <option value="">-- Select Project --</option>
            <option value="Project 1">Project 1</option>
          </select>
        </div>

        {areSelectionsComplete() && (
          <>
            <div style={styles.selectGroup}>
              <label style={styles.label}>Functionality:</label>
              <select value={functionality} onChange={handleFunctionalityChange} style={styles.select}>
                <option value="">-- Select Functionality --</option>
                {functionalityOptions.map(option => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </div>
            {/* Release filter removed */}
            <div style={styles.selectGroup}>
              <label style={styles.label}>Sort by Risk (High to Low):</label>
              <input
                type="checkbox"
                checked={sortRiskHighToLow}
                onChange={handleSortRiskChange}
                style={{ marginLeft: '16px', transform: 'scale(1.2)' }}
              />
            </div>
            <div style={styles.selectGroup}>
              <label style={styles.label}>Sort by Sprint (Ascending):</label>
              <input
                type="checkbox"
                checked={sortSprintAsc}
                onChange={handleSortSprintChange}
                style={{ marginLeft: '16px', transform: 'scale(1.2)' }}
              />
            </div>
          </>
        )}
      </div>
      
      {areSelectionsComplete() && (
        <>
          <h3>Requirements Table</h3>
          {loading ? (
            <div style={styles.loadingContainer}>
              <div style={styles.loadingText}>Loading requirements...</div>
              <div style={styles.loadingSpinner}></div>
            </div>
          ) : error ? (
            <div style={styles.errorContainer}>
              <div style={styles.errorMessage}>
                <h3>Error Loading Requirements</h3>
                <p>{error}</p>
                <div style={styles.errorDetails}>
                  <p>Please check:</p>
                  <ul>
                    <li>Backend server is running</li>
                    <li>Database connection is active</li>
                    <li>Requirements table exists and has data</li>
                  </ul>
                </div>
                <button 
                  style={styles.retryButton}
                  onClick={() => window.location.reload()}
                >
                  Retry
                </button>
              </div>
            </div>
          ) : filteredRequirements.length > 0 ? (
            <table style={styles.table}>
              <thead>
                <tr>
                  <th style={styles.th}>ID</th>
                  <th style={styles.th}>User Story</th>
                  <th style={styles.th}>Description</th>
                  <th style={styles.th}>Functionality</th>
                  <th style={styles.th}>Release</th>  {/* <-- changed from Release */}
                  <th style={styles.th}>Risk Score</th>
                  <th style={styles.th}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRequirements.map((row) => (
                  <tr key={row.id}>
                    <td style={styles.td}>{row.id}</td>
                    <td style={styles.td}>{row.title}</td>
                    <td style={styles.td}>{row.description}</td>
                    <td style={styles.td}>{row.functionality}</td>
                    <td style={styles.td}>{row.release}</td> {/* <-- changed from row.release */}
                    <td style={{
                      ...styles.td,
                      backgroundColor: getRiskColor(row.risk_score),
                      color: row.risk_score === 'Not Assessed' ? 'black' : 'white',
                      fontWeight: 'bold'
                    }}>
                      {row.risk_score}
                    </td>
                    <td style={styles.td}>
                      <button 
                        style={styles.actionButton} 
                        onClick={() => window.location.href = `/item/${row.id}`}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No requirements found.</p>
          )}
        </>
      )}
    </div>
  );
}

const styles = {
  container: {
    backgroundColor: '#f5faff',
    color: '#003366',
    fontFamily: 'Ubuntu, Arial, sans-serif',
    minHeight: '100vh',
    padding: '2rem'
  },
  filterPanel: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,112,173,0.08)',
    padding: '1.5rem',
    marginBottom: '2rem'
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
  },
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '2rem',
  },
  loadingSpinner: {
    width: '40px',
    height: '40px',
    margin: '20px',
    border: '4px solid #f3f3f3',
    borderTop: '4px solid #0070AD',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  errorContainer: {
    display: 'flex',
    justifyContent: 'center',
    padding: '2rem',
  },
  errorMessage: {
    backgroundColor: '#fff',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,112,173,0.08)',
    textAlign: 'center',
  },
  errorDetails: {
    marginTop: '1rem',
    padding: '1rem',
    backgroundColor: '#ffebee',
    borderRadius: '4px',
    color: '#c62828'
  },
  loadingText: {
    color: '#0070AD',
    marginBottom: '1rem'
  },
  retryButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#0070AD',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    marginTop: '1rem',
  }
};


export default DetailsPage;