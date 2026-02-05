import { useState } from 'react'
import axios from 'axios'
import { motion } from 'framer-motion'
import './index.css'

function App() {
  const [target, setTarget] = useState('')
  const [logs, setLogs] = useState([])
  const [scanStatus, setScanStatus] = useState('IDLE')

  // Store results for the viewer
  const [results, setResults] = useState({
    nmap: null,
    nuclei: null
  })

  // Track which result tab is active
  const [activeTab, setActiveTab] = useState('NMAP')

  const handleScan = async () => {
    if (!target) return

    // Reset state
    setScanStatus('SCANNING')
    setLogs([])
    setResults({ nmap: null, nuclei: null })

    addLog(`Info`, `Starting Assessment for: ${target}`)

    try {
      // --- STEP 1: Validation ---
      const valResponse = await axios.post('http://localhost:8000/validate', { target }, { timeout: 10000 })
      const valData = valResponse.data

      if (!valData.valid) {
        addLog(`Error`, `Validation Failed: ${valData.message}`)
        setScanStatus('ERROR')
        return
      }

      const cleanTarget = valData.cleaned_target
      addLog(`Success`, `Target Validated (${cleanTarget})`)

      // --- STEP 2: Recon (Step 2 Completion) ---
      addLog(`Info`, `[Phase 1] Complete Recon (Nmap, Subfinder, Amass, Tech) Started...`)
      const reconResponse = await axios.post('http://localhost:8000/scan/inventory', { target: cleanTarget }, { timeout: 300000 }) // 5 min timeout
      const reconData = reconResponse.data

      if (reconData.status === 'error') {
        addLog(`Error`, `Recon Failed: ${reconData.message}`)
      } else {
        setResults(prev => ({
          ...prev,
          nmap: { open_ports: reconData.data.infrastructure.main_target_ports, raw_output: "See Inventory for details" },
          inventory: reconData.data
        }))
        addLog(`Success`, `[Phase 1] Recon Completed. Found ${reconData.data.discovery.subdomains_count} subdomains.`)
      }

      // --- STEP 3: Vuln Scan (Step 3 Completion) ---
      addLog(`Info`, `[Phase 2] Automated Vulnerability Scan (Nuclei + Nikto + ZAP) Started...`)
      const vulnResponse = await axios.post('http://localhost:8000/scan/vuln', { target: cleanTarget }, { timeout: 900000 }) // 15 min timeout (ZAP is slow)
      const vulnData = vulnResponse.data

      if (vulnData.status === 'error') {
        addLog(`Error`, `Scan Failed: ${vulnData.message}`)
      } else {
        setResults(prev => ({
          ...prev,
          nuclei: vulnData.nuclei.findings,
          nikto: vulnData.nikto,
          zap: vulnData.zap
        }))
        addLog(`Success`, `[Phase 2] Scan Completed. Found ${vulnData.findings_count} Nuclei issues.`)
      }

      setScanStatus('READY')
      addLog(`Success`, `Assessment Finished. Check Results below.`)

    } catch (error) {
      addLog(`Critical`, `System Error: ${error.message}`)
      console.error(error)
      setScanStatus('ERROR')
    }
  }

  const addLog = (type, msg) => {
    const timestamp = new Date().toLocaleTimeString()
    setLogs(prev => [...prev, { time: timestamp, type, msg }])
  }

  const getStatusClass = (status) => {
    switch (status) {
      case 'SCANNING': return 'status-scanning';
      case 'READY': return 'status-ready';
      case 'ERROR': return 'status-error';
      default: return 'status-idle';
    }
  }

  return (
    <div className="container">
      {/* Header Card */}
      <motion.div
        className="card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div style={{ textAlign: 'center' }}>
          <h1>Auto_VAPT // Pro</h1>
          <p className="subtitle">AI-Driven Vulnerability Assessment Engine</p>
        </div>

        <div className="input-group">
          <input
            type="text"
            placeholder="Enter target (e.g., scanme.nmap.org)"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleScan()}
          />
          <button onClick={handleScan} disabled={scanStatus === 'SCANNING'}>
            {scanStatus === 'SCANNING' ? 'SCANNING...' : 'INITIATE ASSESSEMENT'}
          </button>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>System Status:</span>
          <span className={`status-badge ${getStatusClass(scanStatus)}`}>{scanStatus}</span>
        </div>
      </motion.div>

      {/* Logs Card */}
      <motion.div
        className="card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        style={{ padding: '0', minHeight: '100px' }}
      >
        <div style={{ padding: '1.5rem 2.5rem 0.5rem 2.5rem' }}>
          <h3 style={{ margin: 0, color: '#e2e8f0', fontSize: '1rem' }}>Activity Log</h3>
        </div>

        <div style={{ padding: '0 2.5rem 1.5rem 2.5rem' }}>
          <div className="logs-area" style={{ minHeight: '150px', maxHeight: '200px' }}>
            {logs.length === 0 && <div style={{ color: '#64748b', fontStyle: 'italic' }}>Ready...</div>}

            {logs.map((log, index) => (
              <div key={index} className="log-entry" style={{ padding: '4px 0', fontSize: '0.85rem' }}>
                <span className="log-time" style={{ minWidth: '70px' }}>[{log.time}]</span>
                <span style={{
                  color: log.type === 'Info' ? '#94a3b8' :
                    log.type === 'Success' ? '#10b981' :
                      log.type === 'Error' ? '#f43f5e' : '#e2e8f0',
                  fontWeight: 'bold',
                  marginRight: '10px'
                }}>
                  {log.type}:
                </span>
                <span>{log.msg}</span>
              </div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Results Viewer */}
      {(results.nmap || results.nuclei) && (
        <motion.div
          className="card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <div style={{ display: 'flex', gap: '20px', marginBottom: '20px', borderBottom: '1px solid var(--border-color)', paddingBottom: '10px' }}>
            <button
              onClick={() => setActiveTab('RECON')}
              style={{
                background: activeTab === 'RECON' ? 'var(--primary-gradient)' : 'transparent',
                padding: '8px 20px',
                border: activeTab === 'RECON' ? 'none' : '1px solid var(--border-color)',
                color: activeTab === 'RECON' ? '#fff' : 'var(--text-secondary)'
              }}
            >
              RECON INVENTORY
            </button>
            <button
              onClick={() => setActiveTab('NMAP')}
              style={{
                background: activeTab === 'NMAP' ? 'var(--primary-gradient)' : 'transparent',
                padding: '8px 20px',
                border: activeTab === 'NMAP' ? 'none' : '1px solid var(--border-color)',
                color: activeTab === 'NMAP' ? '#fff' : 'var(--text-secondary)'
              }}
            >
              PORTS
            </button>
            <button
              onClick={() => setActiveTab('NUCLEI')}
              style={{
                background: activeTab === 'NUCLEI' ? 'var(--primary-gradient)' : 'transparent',
                padding: '8px 20px',
                border: activeTab === 'NUCLEI' ? 'none' : '1px solid var(--border-color)',
                color: activeTab === 'NUCLEI' ? '#fff' : 'var(--text-secondary)'
              }}
            >
              VULNS
            </button>
            <button
              onClick={() => setActiveTab('ZAP')}
              style={{
                background: activeTab === 'ZAP' ? 'var(--primary-gradient)' : 'transparent',
                padding: '8px 20px',
                border: activeTab === 'ZAP' ? 'none' : '1px solid var(--border-color)',
                color: activeTab === 'ZAP' ? '#fff' : 'var(--text-secondary)'
              }}
            >
              OWASP ZAP
            </button>
          </div>

          <div className="results-content" style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {activeTab === 'ZAP' && (
              <div>
                <h4>OWASP ZAP Scan Details</h4>
                {results.zap?.error ? (
                  <div style={{ color: '#f43f5e', padding: '10px', background: 'rgba(244, 63, 94, 0.1)', borderRadius: '8px' }}>
                    <strong>Tool Error:</strong> {results.zap.error}
                  </div>
                ) : results.zap ? (
                  <div>
                    <div style={{ background: 'rgba(255,165,0,0.1)', padding: '15px', borderRadius: '8px', border: '1px solid rgba(255,165,0,0.3)', marginBottom: '15px' }}>
                      <p><strong>Status:</strong> Scan Complete</p>
                      <p><strong>Report:</strong> <a href={`http://localhost:8000/report/${results.zap.report_filename || results.zap.report_file?.split('\\').pop()}`} target="_blank" style={{ color: '#60a5fa' }}>Download Full HTML Report</a></p>
                    </div>
                    <pre style={{ background: '#000', padding: '15px', borderRadius: '8px', overflowX: 'auto', fontSize: '0.8rem', color: '#fbbf24' }}>
                      {results.zap.raw_output || "Processing scan data..."}
                    </pre>
                  </div>
                ) : (
                  <p>No ZAP data available.</p>
                )}
              </div>
            )}
            {activeTab === 'RECON' && results.inventory && (
              <div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                  <div>
                    <h4>Subdomains Found ({results.inventory.discovery.subdomains_count})</h4>
                    <ul style={{ listStyle: 'none', maxHeight: '200px', overflowY: 'auto', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', padding: '10px' }}>
                      {results.inventory.discovery.subdomains.map((sub, i) => (
                        <li key={i} style={{ fontSize: '0.85rem', padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>{sub}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4>Technologies Detected</h4>
                    <div style={{ background: 'rgba(0,0,0,0.2)', padding: '15px', borderRadius: '8px' }}>
                      <p><strong>Title:</strong> {results.inventory.infrastructure.technologies.title || 'N/A'}</p>
                      <p><strong>Server:</strong> {results.inventory.infrastructure.technologies.webserver || 'N/A'}</p>
                      <p><strong>Status:</strong> {results.inventory.infrastructure.technologies.status_code || 'N/A'}</p>
                      <div>
                        <strong>Stack:</strong>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginTop: '10px' }}>
                          {results.inventory.infrastructure.technologies.technologies?.map((t, i) => (
                            <span key={i} style={{ background: '#3b82f6', color: '#fff', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem' }}>{t}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            {activeTab === 'NMAP' && results.nmap && (
              <div>
                <h4>Open Ports Found: {results.nmap.open_ports?.length || 0}</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '10px', marginTop: '15px' }}>
                  {results.nmap.open_ports?.map((port, i) => (
                    <div key={i} style={{
                      background: 'rgba(15, 23, 42, 0.5)',
                      padding: '10px',
                      borderRadius: '8px',
                      border: '1px solid var(--success-color)',
                      textAlign: 'center'
                    }}>
                      <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#fff' }}>{port.port}</div>
                      <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{port.service}</div>
                    </div>
                  ))}
                </div>
                {results.nmap.raw_output && (
                  <details style={{ marginTop: '20px' }}>
                    <summary style={{ cursor: 'pointer', color: 'var(--text-secondary)' }}>View Raw Output</summary>
                    <pre style={{ background: '#000', padding: '15px', borderRadius: '8px', overflowX: 'auto', fontSize: '0.8rem' }}>
                      {results.nmap.raw_output}
                    </pre>
                  </details>
                )}
              </div>
            )}

            {activeTab === 'NUCLEI' && (
              <div>
                <h4>Vulnerabilities Found: {results.nuclei && Array.isArray(results.nuclei) ? results.nuclei.length : 0}</h4>

                {results.nuclei?.error ? (
                  <div style={{ color: '#f43f5e', padding: '10px', background: 'rgba(244, 63, 94, 0.1)', borderRadius: '8px' }}>
                    <strong>Tool Error:</strong> {results.nuclei.error}
                  </div>
                ) : Array.isArray(results.nuclei) && results.nuclei.length > 0 ? (
                  <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '15px', fontSize: '0.9rem' }}>
                    <thead>
                      <tr style={{ background: 'rgba(255,255,255,0.05)', textAlign: 'left' }}>
                        <th style={{ padding: '10px' }}>Severity</th>
                        <th style={{ padding: '10px' }}>Name</th>
                        <th style={{ padding: '10px' }}>Host</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.nuclei.map((vuln, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                          <td style={{ padding: '10px' }}>
                            <span style={{
                              color: vuln.info?.severity === 'critical' || vuln.info?.severity === 'high' ? '#f43f5e' :
                                vuln.info?.severity === 'medium' ? '#fbbf24' : '#94a3b8',
                              fontWeight: 'bold',
                              textTransform: 'uppercase'
                            }}>
                              {vuln.info?.severity || 'UNKNOWN'}
                            </span>
                          </td>
                          <td style={{ padding: '10px' }}>{vuln.info?.name || 'Unknown Issue'}</td>
                          <td style={{ padding: '10px', color: '#64748b' }}>{vuln.host}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p style={{ fontStyle: 'italic', color: '#64748b' }}>No vulnerabilities found or raw output format.</p>
                )}
              </div>
            )}

            {activeTab === 'NMAP' && !results.nmap && <p style={{ color: '#64748b' }}>No Nmap results yet.</p>}
            {activeTab === 'NUCLEI' && !results.nuclei && <p style={{ color: '#64748b' }}>No Nuclei results yet.</p>}
          </div>
        </motion.div>
      )}

    </div>
  )
}

export default App
