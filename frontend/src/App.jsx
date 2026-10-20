import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Simulation from './pages/Simulation';
import Activities from './pages/Activities';
import Login from './pages/Login';
import Research from './pages/Research';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('sentinel_token'));
  const [role, setRole] = useState(localStorage.getItem('sentinel_role') || 'Admin');
  const [activeTab, setActiveTab] = useState('dashboard');

  const handleLoginSuccess = (userRole) => {
    setToken(localStorage.getItem('sentinel_token'));
    setRole(userRole);
  };

  const handleLogout = () => {
    localStorage.removeItem('sentinel_token');
    localStorage.removeItem('sentinel_role');
    setToken(null);
  };

  if (!token) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onLogout={handleLogout}
        userRole={role}
      />
      <main>
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'simulation' && <Simulation />}
        {activeTab === 'activities' && <Activities />}
        {activeTab === 'research' && <Research />}
      </main>
    </div>
  );
}