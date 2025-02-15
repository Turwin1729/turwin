import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import hospitalLogo from '../assets/hospital.png';

function Navbar({ user, onLogout }) {
  const navigate = useNavigate();

  return (
    <AppBar position="static">
      <Toolbar>
        <img 
          src={hospitalLogo} 
          alt="Hospital Logo" 
          style={{ height: 40, marginRight: 16 }}
        />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Turwin Medical Center
        </Typography>
        {user ? (
          <>
            <Button color="inherit" onClick={() => navigate('/dashboard')}>
              Dashboard
            </Button>
            <Button color="inherit" onClick={onLogout}>
              Logout
            </Button>
          </>
        ) : (
          <>
            <Button color="inherit" onClick={() => navigate('/login')}>
              Login
            </Button>
            <Button color="inherit" onClick={() => navigate('/register')}>
              Register
            </Button>
          </>
        )}
      </Toolbar>
    </AppBar>
  );
}

export default Navbar;
