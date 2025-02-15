import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import axios from 'axios'; // Import axios
import Login from './components/Login';
import Register from './components/Register';
import DoctorDashboard from './components/DoctorDashboard';
import PatientDashboard from './components/PatientDashboard';
import Navbar from './components/Navbar';

const theme = createTheme({
  palette: {
    primary: {
      main: '#dc3545',
    },
    secondary: {
      main: '#6c757d',
    },
  },
});

function App() {
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user')));

  useEffect(() => {
    // Vulnerable - automatically use token from localStorage
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, []);

  const handleLogin = (userData) => {
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    setUser(null);
    // Clear token but leave cookie (vulnerable)
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Navbar user={user} onLogout={handleLogout} />
        <Routes>
          <Route path="/login" element={
            !user ? <Login onLogin={handleLogin} /> : <Navigate to="/dashboard" />
          } />
          <Route path="/register" element={
            !user ? <Register onLogin={handleLogin} /> : <Navigate to="/dashboard" />
          } />
          <Route path="/dashboard" element={
            user ? (
              user.role === 'doctor' ? 
                <DoctorDashboard user={user} /> : 
                <PatientDashboard user={user} />
            ) : <Navigate to="/login" />
          } />
          <Route path="/" element={<Navigate to={user ? "/dashboard" : "/login"} />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
