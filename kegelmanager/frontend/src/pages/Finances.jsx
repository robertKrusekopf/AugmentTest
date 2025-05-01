import { useState, useEffect } from 'react';
import './Finances.css';

const Finances = () => {
  const [loading, setLoading] = useState(true);
  const [finances, setFinances] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Simulierte Daten für die Demonstration
  useEffect(() => {
    // In einer echten Anwendung würden wir hier die API aufrufen
    
    // Simulierte Daten
    setTimeout(() => {
      const mockFinances = {
        balance: 1250000,
        income: {
          total: 125000,
          breakdown: {
            tickets: 50000,
            sponsorship: 40000,
            merchandise: 20000,
            transfers: 15000
          }
        },
        expenses: {
          total: 100000,
          breakdown: {
            salaries: 70000,
            facilities: 15000,
            transfers: 10000,
            other: 5000
          }
        },
        history: [
          { month: 'Jan', balance: 1000000, income: 120000, expenses: 95000 },
          { month: 'Feb', balance: 1025000, income: 122000, expenses: 97000 },
          { month: 'Mär', balance: 1050000, income: 123000, expenses: 98000 },
          { month: 'Apr', balance: 1075000, income: 124000, expenses: 99000 },
          { month: 'Mai', balance: 1100000, income: 125000, expenses: 100000 },
          { month: 'Jun', balance: 1125000, income: 125000, expenses: 100000 },
          { month: 'Jul', balance: 1150000, income: 125000, expenses: 100000 },
          { month: 'Aug', balance: 1175000, income: 125000, expenses: 100000 },
          { month: 'Sep', balance: 1200000, income: 125000, expenses: 100000 },
          { month: 'Okt', balance: 1225000, income: 125000, expenses: 100000 },
          { month: 'Nov', balance: 1250000, income: 125000, expenses: 100000 },
          { month: 'Dez', balance: 1275000, income: 125000, expenses: 100000 }
        ],
        transactions: [
          { id: 1, date: '2025-07-15', description: 'Spielergehälter', amount: -70000, category: 'salaries' },
          { id: 2, date: '2025-07-15', description: 'Ticketeinnahmen vs Kegel SV', amount: 15000, category: 'tickets' },
          { id: 3, date: '2025-07-15', description: 'Sponsoreneinnahmen', amount: 40000, category: 'sponsorship' },
          { id: 4, date: '2025-07-20', description: 'Merchandiseverkäufe', amount: 20000, category: 'merchandise' },
          { id: 5, date: '2025-07-22', description: 'Ticketeinnahmen vs SC Kegeltal', amount: 18000, category: 'tickets' },
          { id: 6, date: '2025-07-25', description: 'Anlagenunterhalt', amount: -15000, category: 'facilities' },
          { id: 7, date: '2025-07-28', description: 'Ticketeinnahmen vs Kegel Union', amount: 17000, category: 'tickets' },
          { id: 8, date: '2025-07-30', description: 'Sonstige Ausgaben', amount: -5000, category: 'other' }
        ],
        budget: {
          income: {
            tickets: { budgeted: 600000, actual: 150000, remaining: 450000 },
            sponsorship: { budgeted: 480000, actual: 120000, remaining: 360000 },
            merchandise: { budgeted: 240000, actual: 60000, remaining: 180000 },
            transfers: { budgeted: 180000, actual: 45000, remaining: 135000 }
          },
          expenses: {
            salaries: { budgeted: 840000, actual: 210000, remaining: 630000 },
            facilities: { budgeted: 180000, actual: 45000, remaining: 135000 },
            transfers: { budgeted: 120000, actual: 30000, remaining: 90000 },
            other: { budgeted: 60000, actual: 15000, remaining: 45000 }
          }
        }
      };
      
      setFinances(mockFinances);
      setLoading(false);
    }, 1000);
  }, []);
  
  if (loading) {
    return <div className="loading">Lade Finanzdaten...</div>;
  }
  
  if (!finances) {
    return <div className="error">Finanzdaten konnten nicht geladen werden</div>;
  }
  
  return (
    <div className="finances-page">
      <h1 className="page-title">Finanzen</h1>
      
      <div className="finance-summary-cards">
        <div className="summary-card balance">
          <div className="card-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="1" x2="12" y2="23"></line>
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
            </svg>
          </div>
          <div className="card-content">
            <h3>Kontostand</h3>
            <div className="amount">€{finances.balance.toLocaleString()}</div>
          </div>
        </div>
        
        <div className="summary-card income">
          <div className="card-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
              <polyline points="17 6 23 6 23 12"></polyline>
            </svg>
          </div>
          <div className="card-content">
            <h3>Monatliche Einnahmen</h3>
            <div className="amount positive">+€{finances.income.total.toLocaleString()}</div>
          </div>
        </div>
        
        <div className="summary-card expenses">
          <div className="card-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline>
              <polyline points="17 18 23 18 23 12"></polyline>
            </svg>
          </div>
          <div className="card-content">
            <h3>Monatliche Ausgaben</h3>
            <div className="amount negative">-€{finances.expenses.total.toLocaleString()}</div>
          </div>
        </div>
        
        <div className="summary-card profit">
          <div className="card-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
            </svg>
          </div>
          <div className="card-content">
            <h3>Monatlicher Gewinn</h3>
            <div className="amount positive">+€{(finances.income.total - finances.expenses.total).toLocaleString()}</div>
          </div>
        </div>
      </div>
      
      <div className="finance-tabs card">
        <div className="tabs">
          <div 
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Übersicht
          </div>
          <div 
            className={`tab ${activeTab === 'income' ? 'active' : ''}`}
            onClick={() => setActiveTab('income')}
          >
            Einnahmen
          </div>
          <div 
            className={`tab ${activeTab === 'expenses' ? 'active' : ''}`}
            onClick={() => setActiveTab('expenses')}
          >
            Ausgaben
          </div>
          <div 
            className={`tab ${activeTab === 'transactions' ? 'active' : ''}`}
            onClick={() => setActiveTab('transactions')}
          >
            Transaktionen
          </div>
          <div 
            className={`tab ${activeTab === 'budget' ? 'active' : ''}`}
            onClick={() => setActiveTab('budget')}
          >
            Budget
          </div>
        </div>
        
        <div className="tab-content">
          {activeTab === 'overview' && (
            <div className="overview-tab">
              <div className="chart-container">
                <h3>Kontostand (Jahresverlauf)</h3>
                <div className="chart-placeholder">
                  [Hier würde ein Finanz-Chart angezeigt werden]
                </div>
              </div>
              
              <div className="finance-breakdown">
                <div className="breakdown-section">
                  <h3>Einnahmen</h3>
                  <div className="breakdown-chart">
                    <div className="chart-placeholder">
                      [Hier würde ein Einnahmen-Kreisdiagramm angezeigt werden]
                    </div>
                  </div>
                  <div className="breakdown-list">
                    {Object.entries(finances.income.breakdown).map(([key, value]) => (
                      <div key={key} className="breakdown-item">
                        <span className="item-label">{key.charAt(0).toUpperCase() + key.slice(1)}</span>
                        <span className="item-value">€{value.toLocaleString()}</span>
                        <span className="item-percentage">
                          {Math.round((value / finances.income.total) * 100)}%
                        </span>
                      </div>
                    ))}
                    <div className="breakdown-item total">
                      <span className="item-label">Gesamt</span>
                      <span className="item-value">€{finances.income.total.toLocaleString()}</span>
                      <span className="item-percentage">100%</span>
                    </div>
                  </div>
                </div>
                
                <div className="breakdown-section">
                  <h3>Ausgaben</h3>
                  <div className="breakdown-chart">
                    <div className="chart-placeholder">
                      [Hier würde ein Ausgaben-Kreisdiagramm angezeigt werden]
                    </div>
                  </div>
                  <div className="breakdown-list">
                    {Object.entries(finances.expenses.breakdown).map(([key, value]) => (
                      <div key={key} className="breakdown-item">
                        <span className="item-label">{key.charAt(0).toUpperCase() + key.slice(1)}</span>
                        <span className="item-value">€{value.toLocaleString()}</span>
                        <span className="item-percentage">
                          {Math.round((value / finances.expenses.total) * 100)}%
                        </span>
                      </div>
                    ))}
                    <div className="breakdown-item total">
                      <span className="item-label">Gesamt</span>
                      <span className="item-value">€{finances.expenses.total.toLocaleString()}</span>
                      <span className="item-percentage">100%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'income' && (
            <div className="income-tab">
              <div className="chart-container">
                <h3>Einnahmen (Jahresverlauf)</h3>
                <div className="chart-placeholder">
                  [Hier würde ein Einnahmen-Chart angezeigt werden]
                </div>
              </div>
              
              <div className="income-details">
                <h3>Einnahmenquellen</h3>
                <table className="table finance-table">
                  <thead>
                    <tr>
                      <th>Quelle</th>
                      <th>Monatlich</th>
                      <th>Jährlich (geschätzt)</th>
                      <th>Anteil</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(finances.income.breakdown).map(([key, value]) => (
                      <tr key={key}>
                        <td>{key.charAt(0).toUpperCase() + key.slice(1)}</td>
                        <td>€{value.toLocaleString()}</td>
                        <td>€{(value * 12).toLocaleString()}</td>
                        <td>{Math.round((value / finances.income.total) * 100)}%</td>
                      </tr>
                    ))}
                    <tr className="total-row">
                      <td>Gesamt</td>
                      <td>€{finances.income.total.toLocaleString()}</td>
                      <td>€{(finances.income.total * 12).toLocaleString()}</td>
                      <td>100%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
          
          {activeTab === 'expenses' && (
            <div className="expenses-tab">
              <div className="chart-container">
                <h3>Ausgaben (Jahresverlauf)</h3>
                <div className="chart-placeholder">
                  [Hier würde ein Ausgaben-Chart angezeigt werden]
                </div>
              </div>
              
              <div className="expenses-details">
                <h3>Ausgabenkategorien</h3>
                <table className="table finance-table">
                  <thead>
                    <tr>
                      <th>Kategorie</th>
                      <th>Monatlich</th>
                      <th>Jährlich (geschätzt)</th>
                      <th>Anteil</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(finances.expenses.breakdown).map(([key, value]) => (
                      <tr key={key}>
                        <td>{key.charAt(0).toUpperCase() + key.slice(1)}</td>
                        <td>€{value.toLocaleString()}</td>
                        <td>€{(value * 12).toLocaleString()}</td>
                        <td>{Math.round((value / finances.expenses.total) * 100)}%</td>
                      </tr>
                    ))}
                    <tr className="total-row">
                      <td>Gesamt</td>
                      <td>€{finances.expenses.total.toLocaleString()}</td>
                      <td>€{(finances.expenses.total * 12).toLocaleString()}</td>
                      <td>100%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
          
          {activeTab === 'transactions' && (
            <div className="transactions-tab">
              <h3>Letzte Transaktionen</h3>
              <table className="table transactions-table">
                <thead>
                  <tr>
                    <th>Datum</th>
                    <th>Beschreibung</th>
                    <th>Kategorie</th>
                    <th>Betrag</th>
                  </tr>
                </thead>
                <tbody>
                  {finances.transactions.map(transaction => (
                    <tr key={transaction.id}>
                      <td>{new Date(transaction.date).toLocaleDateString('de-DE')}</td>
                      <td>{transaction.description}</td>
                      <td>{transaction.category.charAt(0).toUpperCase() + transaction.category.slice(1)}</td>
                      <td className={transaction.amount > 0 ? 'positive' : 'negative'}>
                        {transaction.amount > 0 ? '+' : ''}€{transaction.amount.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          
          {activeTab === 'budget' && (
            <div className="budget-tab">
              <div className="budget-section">
                <h3>Einnahmenbudget</h3>
                <table className="table budget-table">
                  <thead>
                    <tr>
                      <th>Kategorie</th>
                      <th>Budgetiert (Jährlich)</th>
                      <th>Aktuell</th>
                      <th>Verbleibend</th>
                      <th>Fortschritt</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(finances.budget.income).map(([key, value]) => (
                      <tr key={key}>
                        <td>{key.charAt(0).toUpperCase() + key.slice(1)}</td>
                        <td>€{value.budgeted.toLocaleString()}</td>
                        <td>€{value.actual.toLocaleString()}</td>
                        <td>€{value.remaining.toLocaleString()}</td>
                        <td>
                          <div className="progress-bar">
                            <div 
                              className="progress-fill" 
                              style={{ width: `${(value.actual / value.budgeted) * 100}%` }}
                            ></div>
                          </div>
                          <span className="progress-text">
                            {Math.round((value.actual / value.budgeted) * 100)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              <div className="budget-section">
                <h3>Ausgabenbudget</h3>
                <table className="table budget-table">
                  <thead>
                    <tr>
                      <th>Kategorie</th>
                      <th>Budgetiert (Jährlich)</th>
                      <th>Aktuell</th>
                      <th>Verbleibend</th>
                      <th>Fortschritt</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(finances.budget.expenses).map(([key, value]) => (
                      <tr key={key}>
                        <td>{key.charAt(0).toUpperCase() + key.slice(1)}</td>
                        <td>€{value.budgeted.toLocaleString()}</td>
                        <td>€{value.actual.toLocaleString()}</td>
                        <td>€{value.remaining.toLocaleString()}</td>
                        <td>
                          <div className="progress-bar">
                            <div 
                              className="progress-fill" 
                              style={{ width: `${(value.actual / value.budgeted) * 100}%` }}
                            ></div>
                          </div>
                          <span className="progress-text">
                            {Math.round((value.actual / value.budgeted) * 100)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Finances;
