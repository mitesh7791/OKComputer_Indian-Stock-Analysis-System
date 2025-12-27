import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

const Header = () => {
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <TrendingUpIcon sx={{ mr: 2 }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Indian Stock Analyzer
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            color="inherit"
            component={Link}
            to="/"
            variant={isActive('/') ? 'outlined' : 'text'}
          >
            Dashboard
          </Button>
          <Button
            color="inherit"
            component={Link}
            to="/market"
            variant={isActive('/market') ? 'outlined' : 'text'}
          >
            Market
          </Button>
          <Button
            color="inherit"
            component={Link}
            to="/news"
            variant={isActive('/news') ? 'outlined' : 'text'}
          >
            News
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;