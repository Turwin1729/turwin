import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from 'styled-components';
import { GlobalStyle, theme } from './styles/theme';
import HomePage from './pages/HomePage';
import VisualizationPage from './pages/VisualizationPage';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <GlobalStyle />
      <Router>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/visualization" element={<VisualizationPage />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
