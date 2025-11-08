import { useState, useEffect } from 'react'
import './Dashboard.css'
import RevenueChart from './RevenueChart'

interface DashboardProps {
  results: any
  dualAIResults: any
  onBack: () => void
}

interface MetricsData {
  totalDocuments: number
  activeCompanies: number
  totalRevenue: number
  recentInvoices: number
  validationRate: number
}

interface Invoice {
  invoice_id: number
  invoice_num: string
  invoice_date: string
  supplier_name: string
  total_value: number
  status: string
}

interface Company {
  company_id: number
  legal_name: string
  gstin: string | null
  city: string
  total_invoices: number
}

interface RevenueData {
  month: string
  revenue: number
  tax_amount: number
}

interface ComplianceData {
  total_companies: number
  with_gstin: number
  validation_success: number
  duplicate_detection: number
}

const Dashboard: React.FC<DashboardProps> = ({ results, dualAIResults, onBack }) => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null)
  const [recentInvoices, setRecentInvoices] = useState<Invoice[]>([])
  const [topCompanies, setTopCompanies] = useState<Company[]>([])
  const [revenueData, setRevenueData] = useState<RevenueData[]>([])
  const [complianceData, setComplianceData] = useState<ComplianceData | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeDataTab, setActiveDataTab] = useState<'invoices' | 'companies' | 'products' | 'payments' | 'reports'>('invoices')

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      
      // Fetch all dashboard data in parallel
      const [metricsRes, invoicesRes, companiesRes, revenueRes, complianceRes] = await Promise.all([
        fetch('/api/dashboard/metrics'),
        fetch('/api/dashboard/invoices/recent'),
        fetch('/api/dashboard/companies/top'),
        fetch('/api/dashboard/revenue/trends'),
        fetch('/api/dashboard/compliance')
      ])

      if (metricsRes.ok) {
        const metricsData = await metricsRes.json()
        setMetrics(metricsData)
      }

      if (invoicesRes.ok) {
        const invoicesData = await invoicesRes.json()
        setRecentInvoices(invoicesData)
      }

      if (companiesRes.ok) {
        const companiesData = await companiesRes.json()
        setTopCompanies(companiesData)
      }

      if (revenueRes.ok) {
        const revenueData = await revenueRes.json()
        setRevenueData(revenueData)
      }

      if (complianceRes.ok) {
        const complianceData = await complianceRes.json()
        setComplianceData(complianceData)
      }

    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    })
  }

  const getStatusBadge = (status: string) => {
    const statusClass = status.toLowerCase().replace(/[^a-z]/g, '-')
    return <span className={`status-badge ${statusClass}`}>{status}</span>
  }

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-header">
          <button onClick={onBack} className="back-button">← Back to Results</button>
          <h2>📊 Financial Dashboard</h2>
        </div>
        <div className="dashboard-loading">
          <div className="spinner"></div>
          <p>Loading dashboard data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <button onClick={onBack} className="back-button">← Back to Results</button>
        <h2>📊 Financial Dashboard</h2>
        <button onClick={fetchDashboardData} className="refresh-button">🔄 Refresh</button>
      </div>

      {/* Key Metrics Cards */}
      {metrics && (
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-icon">📄</div>
            <div className="metric-content">
              <div className="metric-value">{metrics.totalDocuments}</div>
              <div className="metric-label">Total Documents</div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-icon">🏢</div>
            <div className="metric-content">
              <div className="metric-value">{metrics.activeCompanies}</div>
              <div className="metric-label">Active Companies</div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-icon">💰</div>
            <div className="metric-content">
              <div className="metric-value">{formatCurrency(metrics.totalRevenue)}</div>
              <div className="metric-label">Total Revenue</div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-icon">⚡</div>
            <div className="metric-content">
              <div className="metric-value">{metrics.recentInvoices}</div>
              <div className="metric-label">Recent Invoices</div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-icon">🎯</div>
            <div className="metric-content">
              <div className="metric-value">{metrics.validationRate}%</div>
              <div className="metric-label">Validation Rate</div>
            </div>
          </div>
        </div>
      )}

      {/* Main Dashboard Grid */}
      <div className="dashboard-grid">
        {/* Left Column - Recent Transactions */}
        <div className="dashboard-column">
          <div className="dashboard-card">
            <h3>📋 Recent Invoices</h3>
            <div className="recent-invoices">
              {recentInvoices.length > 0 ? (
                <div className="invoices-table">
                  {recentInvoices.map((invoice) => (
                    <div key={invoice.invoice_id} className="invoice-row">
                      <div className="invoice-info">
                        <div className="invoice-number">{invoice.invoice_num}</div>
                        <div className="invoice-supplier">{invoice.supplier_name}</div>
                        <div className="invoice-date">{formatDate(invoice.invoice_date)}</div>
                      </div>
                      <div className="invoice-amount">
                        {formatCurrency(invoice.total_value)}
                      </div>
                      <div className="invoice-status">
                        {getStatusBadge(invoice.status)}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-data">No recent invoices found</div>
              )}
            </div>
          </div>
        </div>

        {/* Middle Column - Analytics */}
        <div className="dashboard-column">
          <div className="dashboard-card">
            <h3>📈 Revenue Trends</h3>
            <div className="revenue-chart">
              <RevenueChart 
                data={revenueData} 
                formatCurrency={formatCurrency}
              />
            </div>
          </div>

          {/* Compliance Section */}
          {complianceData && (
            <div className="dashboard-card">
              <h3>🛡️ GST Compliance</h3>
              <div className="compliance-stats">
                <div className="compliance-item">
                  <div className="compliance-label">Companies with GSTIN</div>
                  <div className="compliance-value">
                    {complianceData.with_gstin} / {complianceData.total_companies}
                    <span className="compliance-percentage">
                      ({Math.round((complianceData.with_gstin / complianceData.total_companies) * 100)}%)
                    </span>
                  </div>
                </div>
                <div className="compliance-item">
                  <div className="compliance-label">Validation Success</div>
                  <div className="compliance-value">
                    {complianceData.validation_success}%
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Business Intelligence */}
        <div className="dashboard-column">
          <div className="dashboard-card">
            <h3>🏆 Top Suppliers</h3>
            <div className="top-companies">
              {topCompanies.length > 0 ? (
                <div className="companies-list">
                  {topCompanies.map((company, index) => (
                    <div key={company.company_id} className="company-row">
                      <div className="company-rank">#{index + 1}</div>
                      <div className="company-info">
                        <div className="company-name">{company.legal_name}</div>
                        <div className="company-details">
                          {company.city} • {company.total_invoices} invoices
                        </div>
                      </div>
                      <div className="company-gstin">
                        {company.gstin ? (
                          <span className="gstin-badge valid">✓ GST</span>
                        ) : (
                          <span className="gstin-badge invalid">✗ No GST</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-data">No company data available</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Data Tables Section */}
      <div className="data-tables-section">
        <div className="data-tabs">
          {(['invoices', 'companies', 'products', 'payments', 'reports'] as const).map((tab) => (
            <button
              key={tab}
              className={`data-tab ${activeDataTab === tab ? 'active' : ''}`}
              onClick={() => setActiveDataTab(tab)}
            >
              {tab === 'invoices' && '📋'} 
              {tab === 'companies' && '🏢'} 
              {tab === 'products' && '🛍️'} 
              {tab === 'payments' && '💳'} 
              {tab === 'reports' && '📊'} 
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        <div className="data-content">
          {activeDataTab === 'invoices' && (
            <div className="data-table-container">
              <h4>All Invoices</h4>
              <div className="table-placeholder">
                Detailed invoices table will be loaded here...
              </div>
            </div>
          )}
          
          {activeDataTab === 'companies' && (
            <div className="data-table-container">
              <h4>Company Directory</h4>
              <div className="table-placeholder">
                Company directory with GST validation status...
              </div>
            </div>
          )}
          
          {activeDataTab === 'products' && (
            <div className="data-table-container">
              <h4>Product Catalog</h4>
              <div className="table-placeholder">
                Products with HSN codes and tax rates...
              </div>
            </div>
          )}
          
          {activeDataTab === 'payments' && (
            <div className="data-table-container">
              <h4>Payment Tracking</h4>
              <div className="table-placeholder">
                Payment records and reconciliation...
              </div>
            </div>
          )}
          
          {activeDataTab === 'reports' && (
            <div className="data-table-container">
              <h4>Business Reports</h4>
              <div className="table-placeholder">
                Analytics and compliance reports...
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard