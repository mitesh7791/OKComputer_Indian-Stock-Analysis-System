import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';

import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import StockDetail from './pages/StockDetail';
import MarketOverview from './pages/MarketOverview';
import News from './pages/News';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    success: {
      main: '#4caf50',
    },
    warning: {
      main: '#ff9800',
    },
    error: {
      main: '#f44336',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ flexGrow: 1 }}>
          <Header />
          <Box sx={{ p: 2 }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/stock/:symbol" element={<StockDetail />} />
              <Route path="/market" element={<MarketOverview />} />
              <Route path="/news" element={<News />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;