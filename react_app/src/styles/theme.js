import { createGlobalStyle } from 'styled-components';

export const theme = {
  colors: {
    primary: '#1E2A38',
    secondary: '#E0E0E0',
    accent: '#00ADB5',
    darkNavy: '#16202C',
    darkGray: '#2C3E50',
    transparent: 'rgba(46, 64, 83, 0.8)',
  },
  borderRadius: '8px',
  transitions: {
    default: '0.3s ease-in-out',
  },
};

export const GlobalStyle = createGlobalStyle`
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
  
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, ${props => props.theme.colors.primary} 0%, ${props => props.theme.colors.darkNavy} 100%);
    color: ${props => props.theme.colors.secondary};
    min-height: 100vh;
  }

  button {
    font-family: 'Inter', sans-serif;
    cursor: pointer;
    border: none;
    outline: none;
    transition: ${props => props.theme.transitions.default};
  }

  input {
    font-family: 'Inter', sans-serif;
  }
`;
