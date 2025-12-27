import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Box,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Button,
} from '@mui/material';
import { TrendingUp, TrendingDown, AttachMoney, ShowChart } from '@mui/icons-material';
import { Link } from 'react-router-dom';
import axios from 'axios';

const Dashboard = () => {
  const [topStocks, setTopStocks] = useState([]);
  const [marketSentiment, setMarketSentiment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch top stocks
      const topStocksResponse = await axios.get('http://localhost:8000/api/analysis/top-stocks?limit=5');
      setTopStocks(topStocksResponse.data);
      
      // Fetch market sentiment
      const sentimentResponse = await axios.get('http://localhost:8000/api/analysis/market-sentiment');
      setMarketSentiment(sentimentResponse.data);
      
    } catch (err) {
      setError('Failed to fetch dashboard data');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSignalColor = (signal) => {
    switch (signal) {
      case 'BUY':
        return 'success';
      case 'SELL':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStrengthColor = (strength) => {
    switch (strength) {
      case 'STRONG':
        return '#4caf50';
      case 'MODERATE':
        return '#ff9800';
      case 'WEAK':
        return '#f44336';
      default:
        return '#9e9e9e';
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

  return (
    <Box>
      {/* Disclaimer */}
      <Box className="disclaimer" mb={3}>
        <Typography variant="body2">
          <strong>Disclaimer:</strong> Not SEBI registered. For educational purposes only. Not financial advice.
        </Typography>
      </Box>

      {/* Market Sentiment Card */}
      {marketSentiment && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Market Sentiment - {marketSentiment.trading_date}
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary">
                    {marketSentiment.overall_sentiment}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Overall Sentiment
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4">
                    {marketSentiment.average_score}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Average Score
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="success.main">
                    {marketSentiment.bullish_stocks}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Bullish Stocks
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="error.main">
                    {marketSentiment.bearish_stocks}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Bearish Stocks
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Top 5 Stock Picks */}
      <Typography variant="h5" gutterBottom sx={{ mt: 3, mb: 2 }}>
        Top 5 Stock Picks
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Stock</TableCell>
              <TableCell>Signal</TableCell>
              <TableCell>Strength</TableCell>
              <TableCell>Entry</TableCell>
              <TableCell>Target 1</TableCell>
              <TableCell>Target 2</TableCell>
              <TableCell>Stop Loss</TableCell>
              <TableCell>R:R Ratio</TableCell>
              <TableCell>Score</TableCell>
              <TableCell>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {topStocks.map((stock) => (
              <TableRow key={stock.symbol}>
                <TableCell>
                  <Box>
                    <Typography variant="subtitle2">{stock.symbol}</Typography>
                    <Typography variant="body2" color="textSecondary">
                      {stock.name}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    label={stock.signal_type}
                    color={getSignalColor(stock.signal_type)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Typography
                    variant="body2"
                    sx={{ color: getStrengthColor(stock.signal_strength), fontWeight: 'bold' }}
                  >
                    {stock.signal_strength}
                  </Typography>
                </TableCell>
                <TableCell>₹{stock.entry_price}</TableCell>
                <TableCell>₹{stock.target_1}</TableCell>
                <TableCell>₹{stock.target_2}</TableCell>
                <TableCell>₹{stock.stop_loss}</TableCell>
                <TableCell>{stock.reward_ratio_1?.toFixed(2)}</TableCell>
                <TableCell>
                  <Box display="flex" alignItems="center">
                    <Box
                      width={40}
                      height={8}
                      bgcolor="#e0e0e0"
                      borderRadius={4}
                      mr={1}
                    >
                      <Box
                        width={`${stock.score}%`}
                        height="100%"
                        bgcolor={stock.score >= 70 ? '#4caf50' : stock.score >= 50 ? '#ff9800' : '#f44336'}
                        borderRadius={4}
                      />
                    </Box>
                    <Typography variant="body2">{stock.score}</Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Button
                    component={Link}
                    to={`/stock/${stock.symbol}`}
                    size="small"
                    variant="outlined"
                  >
                    View
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Quick Stats */}
      <Grid container spacing={3} sx={{ mt: 3 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TrendingUp color="success" sx={{ mr: 2 }} />
                <Box>
                  <Typography variant="h6">{marketSentiment?.buy_signals || 0}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Buy Signals Today
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TrendingDown color="error" sx={{ mr: 2 }} />
                <Box>
                  <Typography variant="h6">{marketSentiment?.sell_signals || 0}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Sell Signals Today
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <ShowChart color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography variant="h6">
                    {marketSentiment?.total_stocks_analyzed || 0}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Stocks Analyzed
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;