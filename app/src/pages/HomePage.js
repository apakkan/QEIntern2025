import React, { useState, useEffect } from 'react';

function DetailsPage() {
  const [model, setModel] = useState('');
  const [project, setProject] = useState('');
  const [release, setRelease] = useState('');
  const [functionality, setFunctionality] = useState('');
  const [requirements, setRequirements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dbStatus, setDbStatus] = useState(null);

  // Add new state variables for dropdown options
  const [modelOptions, setModelOptions] = useState([]);
  const [projectOptions, setProjectOptions] = useState([]);
  const [releaseOptions, setReleaseOptions] = useState([]);
  const [functionalityOptions, setFunctionalityOptions] = useState([]);

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
      const uniqueReleases = [...new Set(data.map(req => req.release).filter(Boolean))];
      const uniqueFunctionalities = [...new Set(data.map(req => req.functionality).filter(Boolean))];

      setModelOptions(uniqueModels);
      setProjectOptions(uniqueProjects);
      setReleaseOptions(uniqueReleases);
      setFunctionalityOptions(uniqueFunctionalities);
    };

    const fetchRequirements = async () => {
      try {
        console.log('Fetching requirements...');
        const response = await fetch('http://localhost:8000/requirements/');
        const data = await response.json();
        
        console.log('Raw data from API:', data); // Debug log
        
        // Update the fetchRequirements function's transformedData section
        const transformedData = data.map(req => {
            console.log('Processing requirement:', req);
            return {
                id: req.id,
                title: req.user_story,
                description: req.description || 'No Description',
                functionality: req.functionality || 'Not Specified',
                release: req.release || '',
                priority: req.priority || 'Not Set',
                model: req.model || '',
                project: req.project || 'Core System'
            };
        });
        
        console.log('Transformed data:', transformedData); // Debug log
        setRequirements(transformedData);

        // Update release options with improved filtering
        const uniqueReleases = transformedData
          .map(req => req.release)
          .filter(release => release && release.trim() !== '') // Remove empty and whitespace-only values
          .reduce((unique, release) => {
            if (!unique.includes(release)) {
              unique.push(release);
            }
            return unique;
          }, [])
          .sort();

        console.log('Filtered releases before setting state:', uniqueReleases); // Debug log
        setReleaseOptions(uniqueReleases);

        // Update functionality options
        const uniqueFunctionalities = transformedData
          .map(req => req.functionality)
          .filter(func => func && func !== 'Not Specified')
          .reduce((unique, func) => {
            if (!unique.includes(func)) {
              unique.push(func);
            }
            return unique;
          }, [])
          .sort();

        console.log('Filtered functionalities before setting state:', uniqueFunctionalities);
        setFunctionalityOptions(uniqueFunctionalities);

        // Update the project options filtering
        const uniqueProjects = [...new Set(transformedData
          .map(req => req.project)
          .filter(proj => proj && proj.trim() !== ''))]
          .sort();

        console.log('Available projects:', uniqueProjects);
        setProjectOptions(uniqueProjects);

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
  
  // Update the filtering logic
  const filteredRequirements = requirements.filter(req => {
    console.log('Filtering requirement:', {
        id: req.id,
        functionality: req.functionality,
        project: req.project,
        release: req.release,
        currentFilters: { functionality, project, release }
    });

    const functionalityMatch = !functionality || 
        (req.functionality && req.functionality.toLowerCase() === functionality.toLowerCase());
    const projectMatch = !project || 
        (req.project && req.project.toLowerCase() === project.toLowerCase());
    const releaseMatch = !release || 
        (req.release && req.release.toLowerCase() === release.toLowerCase());

    console.log('Matches:', { functionalityMatch, projectMatch, releaseMatch });
    return functionalityMatch && projectMatch && releaseMatch;
  });

  if (loading) {
    console.log('Loading requirements...');
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  // Update the select handlers to include console logging
  const handleModelChange = (e) => {
    console.log('Model selected:', e.target.value);
    setModel(e.target.value);
  };

  const handleProjectChange = (e) => {
    console.log('Project selected:', e.target.value);
    setProject(e.target.value);
  };

  const handleReleaseChange = (e) => {
    const value = e.target.value;
    console.log('Release selected:', value);
    setRelease(value);
  };

  const handleFunctionalityChange = (e) => {
    const value = e.target.value;
    console.log('Functionality selected:', value);
    setFunctionality(value);
  };

  return (
    <div style={styles.container}>
      <div style={styles.filterPanel}>
        <div style={styles.selectGroup}>
          <label style={styles.label}>Model:</label>
          <select value={model} onChange={handleModelChange} style={styles.select}>
            <option value="">-- Select Model --</option>
            {modelOptions.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </div>

        <div style={styles.selectGroup}>
          <label style={styles.label}>Project Name:</label>
          <select value={project} onChange={handleProjectChange} style={styles.select}>
            <option value="">-- Select Project --</option>
            {projectOptions.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </div>

        <div style={styles.selectGroup}>
          <label style={styles.label}>Release:</label>
          <select value={release} onChange={handleReleaseChange} style={styles.select}>
            <option value="">-- Select Release --</option>
            {releaseOptions.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </div>

        <div style={styles.selectGroup}>
          <label style={styles.label}>Functionality:</label>
          <select value={functionality} onChange={handleFunctionalityChange} style={styles.select}>
            <option value="">-- Select Functionality --</option>
            {functionalityOptions.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </div>
      </div>

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
              <th style={styles.th}>Release</th>
              <th style={styles.th}>Priority</th>
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
                <td style={styles.td}>{row.release}</td>
                <td style={styles.td}>{row.priority}</td>
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