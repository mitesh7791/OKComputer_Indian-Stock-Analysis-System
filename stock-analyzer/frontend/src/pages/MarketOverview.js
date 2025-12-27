import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Box,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import axios from 'axios';

const MarketOverview = () => {
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchMarketData();
  }, []);

  const fetchMarketData = async () => {
    try {
      setLoading(true);
      
      const response = await axios.get('http://localhost:8000/api/market/overview');
      setMarketData(response.data);
      
    } catch (err) {
      setError('Failed to fetch market data');
      console.error('Error fetching market data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!marketData) {
    return (
      <Box p={3}>
        <Alert severity="warning">No market data available</Alert>
      </Box>
    );
  }

  // Prepare data for pie chart
  const sentimentData = [
    { name: 'Bullish', value: marketData.market_status.bullish_stocks, color: '#4caf50' },
    { name: 'Bearish', value: marketData.market_status.bearish_stocks, color: '#f44336' },
    { name: 'Neutral', value: marketData.market_status.neutral_stocks, color: '#9e9e9e' },
  ];

  // Prepare data for sector performance chart
  const sectorData = marketData.sector_performance.map(sector => ({
    sector: sector.sector,
    score: sector.average_score,
    stocks: sector.stock_count,
  }));

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Market Overview
      </Typography>

      {/* Market Status Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary" gutterBottom>
                {marketData.market_status.overall_sentiment}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Overall Sentiment
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="success.main" gutterBottom>
                {marketData.buy_signals}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Buy Signals
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="error.main" gutterBottom>
                {marketData.sell_signals}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Sell Signals
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {marketData.market_status.total_stocks_analyzed}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Stocks Analyzed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Market Sentiment Pie Chart */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Market Sentiment Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {sentimentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Sector Performance */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Sector Performance
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={sectorData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="sector" angle={-45} textAnchor="end" height={80} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="score" fill="#1976d2" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Top Performers */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Top Performers
            </Typography>
            {marketData.top_performers.map((stock, index) => (
              <Box
                key={index}
                display="flex"
                justifyContent="space-between"
                alignItems="center"
                py={1}
                borderBottom="1px solid #eee"
              >
                <Box>
                  <Typography variant="subtitle2">{stock.symbol}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {stock.name}
                  </Typography>
                </Box>
                <Box display="flex" alignItems="center" gap={1}>
                  <Typography variant="body2">{stock.score}</Typography>
                  {stock.signal && (
                    <Chip
                      label={stock.signal}
                      color={stock.signal === 'BUY' ? 'success' : 'error'}
                      size="small"
                    />
                  )}
                </Box>
              </Box>
            ))}
          </Paper>
        </Grid>

        {/* Bottom Performers */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Bottom Performers
            </Typography>
            {marketData.bottom_performers.map((stock, index) => (
              <Box
                key={index}
                display="flex"
                justifyContent="space-between"
                alignItems="center"
                py={1}
                borderBottom="1px solid #eee"
              >
                <Box>
                  <Typography variant="subtitle2">{stock.symbol}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {stock.name}
                  </Typography>
                </Box>
                <Box display="flex" alignItems="center" gap={1}>
                  <Typography variant="body2">{stock.score}</Typography>
                  {stock.signal && (
                    <Chip
                      label={stock.signal}
                      color={stock.signal === 'BUY' ? 'success' : 'error'}
                      size="small"
                    />
                  )}
                </Box>
              </Box>
            ))}
          </Paper>
        </Grid>

        {/* Sector Cards */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Sector Analysis
          </Typography>
          <Grid container spacing={2}>
            {marketData.sector_performance.map((sector, index) => (
              <Grid item xs={12} md={4} key={index}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {sector.sector}
                    </Typography>
                    <Typography variant="h4" color="primary">
                      {sector.average_score}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Average Score • {sector.stock_count} stocks
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MarketOverview;