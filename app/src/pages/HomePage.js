import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

function HomePage() {
  const [model, setModel] = useState('');
  const [project, setProject] = useState('');
  const [functionality, setFunctionality] = useState('');
  const [requirements, setRequirements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filtersRestored, setFiltersRestored] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showWelcome, setShowWelcome] = useState(() => !localStorage.getItem('hasSeenWelcome'));
  const [sortRiskHighToLow, setSortRiskHighToLow] = useState(false);
  const [sortSprintAsc, setSortSprintAsc] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  const [modelOptions, setModelOptions] = useState(['OpenAI']);
  const [projectOptions, setProjectOptions] = useState([]);
  const [functionalityOptions, setFunctionalityOptions] = useState([]);
  const pageSize = 10;
  const navigate = useNavigate();

  // Restore filters and UI state from localStorage on first mount
  useEffect(() => {
    const saved = localStorage.getItem('homepageState');
    if (saved) {
      const state = JSON.parse(saved);
      setModel(state.model ?? '');
      setProject(state.project ?? '');
      setFunctionality(state.functionality ?? '');
      setSortRiskHighToLow(!!state.sortRiskHighToLow);
      setSortSprintAsc(!!state.sortSprintAsc);
      setSearchTerm(state.searchTerm ?? '');
      setCurrentPage(state.currentPage ?? 1);
    }
    setFiltersRestored(true);
  }, []);

  // Save filters and UI state to localStorage whenever they change
  useEffect(() => {
    // Only save if filters have been restored (prevents overwriting with initial empty state)
    if (filtersRestored) {
      localStorage.setItem('homepageState', JSON.stringify({
        model,
        project,
        functionality,
        sortRiskHighToLow,
        sortSprintAsc,
        searchTerm,
        currentPage
      }));
    }
  }, [model, project, functionality, sortRiskHighToLow, sortSprintAsc, searchTerm, currentPage, filtersRestored]);

  // Fetch requirements ONLY after filters are restored
  useEffect(() => {
    if (!filtersRestored) return;
    setLoading(true);
    const fetchRequirements = async () => {
      try {
        const response = await fetch('http://localhost:8000/requirements/');
        const data = await response.json();
        if (!Array.isArray(data)) {
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
          model: req.model || 'OpenAI',
          project: req.project || 'Project 1'
        }));
        setRequirements(transformedData);
        const uniqueFunctionalities = [...new Set(transformedData
          .map(req => req.functionality)
          .filter(f => f && f !== 'Not Specified'))];
        setFunctionalityOptions(uniqueFunctionalities);
        setLoading(false);
      } catch (error) {
        setError(error.message);
        setLoading(false);
      }
    };
    fetchRequirements();
  }, [filtersRestored]);

  const areSelectionsComplete = () => {
    return model === 'OpenAI' && project === 'Project 1';
  };

  let filteredRequirements = requirements.filter(req => {
    if (!areSelectionsComplete()) {
      return false;
    }
    const functionalityMatch = !functionality ||
      (req.functionality && req.functionality.toLowerCase() === functionality.toLowerCase());
    return functionalityMatch;
  });

  if (sortRiskHighToLow) {
    filteredRequirements = [...filteredRequirements].sort((a, b) => {
      const scoreA = isNaN(parseInt(a.risk_score)) ? -1 : parseInt(a.risk_score);
      const scoreB = isNaN(parseInt(b.risk_score)) ? -1 : parseInt(b.risk_score);
      return scoreB - scoreA;
    });
  }

  if (sortSprintAsc) {
    filteredRequirements = [...filteredRequirements].sort((a, b) => {
      const sprintA = a.release && /^Sprint\s*(\d+)$/i.test(a.release) ? parseInt(a.release.match(/^Sprint\s*(\d+)$/i)[1]) : 9999;
      const sprintB = b.release && /^Sprint\s*(\d+)$/i.test(b.release) ? parseInt(b.release.match(/^Sprint\s*(\d+)$/i)[1]) : 9999;
      return sprintA - sprintB;
    });
  }

  const getRiskColor = (riskScore) => {
    const score = parseInt(riskScore);
    if (isNaN(score)) return '#808080';
    if (score <= 3) return '#52c41a';
    if (score <= 7) return '#faad14';
    return '#ff4d4f';
  };

  const handleModelChange = (e) => {
    setModel(e.target.value);
    setFunctionality('');
  };

  const handleProjectChange = (e) => {
    setProject(e.target.value);
    setFunctionality('');
  };

  const handleSortRiskChange = (e) => {
    setSortRiskHighToLow(e.target.checked);
  };

  const handleSortSprintChange = (e) => {
    setSortSprintAsc(e.target.checked);
  };

  const handleFunctionalityChange = (e) => {
    setFunctionality(e.target.value);
  };

  const handleGetStarted = () => {
    setShowWelcome(false);
    localStorage.setItem('hasSeenWelcome', 'true');
  };

  // Block rendering until filters are restored and requirements are fetched
  if (!filtersRestored || loading) {
    return (
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
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  const paginatedRequirements = filteredRequirements.slice((currentPage-1)*pageSize, currentPage*pageSize);
  const searchedRequirements = paginatedRequirements.filter(req =>
    req.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    req.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div style={styles.container}>
      {/* Welcome Modal */}
      {showWelcome && (
        <div style={styles.welcomeOverlay}>
          <div style={styles.welcomeModal}>
            <h2>Welcome to Tessy!</h2>
            <p>
              This is your requirements dashboard.<br />
              Use the filters to find and manage requirements.<br />
            </p>
            <button
              style={styles.actionButton}
              onClick={handleGetStarted}
            >
              Get Started
            </button>
          </div>
        </div>
      )}
      <div style={styles.filterPanel}>
        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', marginBottom: '1rem' }}>
          <input
            type="text"
            placeholder="Search requirements..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            style={styles.searchBarSmall}
            aria-label="Search requirements"
          />
        </div>
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
          {filteredRequirements.length > 0 ? (
            <>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>ID</th>
                    <th style={styles.th}>User Story</th>
                    <th style={styles.th}>Description</th>
                    <th style={styles.th}>Functionality</th>
                    <th style={styles.th}>Release</th>
                    <th style={styles.th}>Risk Score</th>
                    <th style={styles.th}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {searchedRequirements.map((row) => (
                    <tr key={row.id}>
                      <td style={styles.td}>{row.id}</td>
                      <td style={styles.td}>{row.title}</td>
                      <td style={styles.td}>{row.description}</td>
                      <td style={styles.td}>{row.functionality}</td>
                      <td style={styles.td}>{row.release}</td>
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
                          onClick={() => navigate(`/item/${row.id}`)}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ marginTop: '1rem', textAlign: 'center' }}>
                <button
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage(currentPage - 1)}
                  style={{ marginRight: '1rem' }}
                >
                  Previous
                </button>
                <span>Page {currentPage} of {Math.ceil(filteredRequirements.length / pageSize)}</span>
                <button
                  disabled={currentPage === Math.ceil(filteredRequirements.length / pageSize)}
                  onClick={() => setCurrentPage(currentPage + 1)}
                  style={{ marginLeft: '1rem' }}
                >
                  Next
                </button>
              </div>
            </>
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
    color: '#0070AD',
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
    color: '#0070AD'
  },
  select: {
    marginLeft: '16px',
    padding: '0.5rem',
    fontSize: '1rem',
    width: '250px',
    maxWidth: '250px',
    boxSizing: 'border-box',
    display: 'inline-block',
    border: '1px solid #0070AD',
    borderRadius: '4px',
    backgroundColor: '#ffffff',
    color: '#003366',
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
  },
  searchBar: {
    width: '100%',
    padding: '0.75rem 1.5rem',
    marginBottom: '1.5rem',
    borderRadius: '24px',
    border: '1px solid #0070AD',
    fontSize: '1.1rem',
    background: '#f0f6fb',
    color: '#0070AD',
    outline: 'none',
    boxShadow: '0 2px 8px rgba(0,112,173,0.05)',
    transition: 'border 0.2s',
    marginTop: '0',
    marginLeft: '0',
  },
  searchBarSmall: {
    width: '220px',
    padding: '0.5rem 1rem',
    borderRadius: '18px',
    border: '1px solid #0070AD',
    fontSize: '1rem',
    background: '#f0f6fb',
    color: '#0070AD',
    outline: 'none',
    boxShadow: '0 2px 8px rgba(0,112,173,0.05)',
    transition: 'border 0.2s',
    marginTop: '0',
    marginLeft: '0',
  },
  welcomeOverlay: {
    position: 'fixed',
    top: 0, left: 0, right: 0, bottom: 0,
    background: 'rgba(0,112,173,0.15)',
    zIndex: 1000,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  welcomeModal: {
    background: '#fff',
    borderRadius: '12px',
    boxShadow: '0 4px 24px rgba(0,112,173,0.15)',
    padding: '2rem 2.5rem',
    textAlign: 'center',
    maxWidth: '400px'
  },
};

export default HomePage;