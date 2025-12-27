import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
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
  Tab,
  Tabs,
} from '@mui/material';
import { 
  TrendingUp, 
  TrendingDown, 
  ShowChart, 
  AttachMoney,
  Timeline,
  Newspaper
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const StockDetail = () => {
  const { symbol } = useParams();
  const [stockData, setStockData] = useState(null);
  const [priceData, setPriceData] = useState([]);
  const [indicatorData, setIndicatorData] = useState([]);
  const [signals, setSignals] = useState([]);
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    fetchStockData();
  }, [symbol]);

  const fetchStockData = async () => {
    try {
      setLoading(true);
      
      // Fetch stock detail
      const stockResponse = await axios.get(`http://localhost:8000/api/stocks/${symbol}`);
      setStockData(stockResponse.data);
      
      // Fetch price data
      const priceResponse = await axios.get(`http://localhost:8000/api/stocks/${symbol}/prices?days=60`);
      setPriceData(priceResponse.data);
      
      // Fetch indicators
      const indicatorResponse = await axios.get(`http://localhost:8000/api/stocks/${symbol}/indicators?days=60`);
      setIndicatorData(indicatorResponse.data);
      
      // Fetch signals
      const signalResponse = await axios.get(`http://localhost:8000/api/stocks/${symbol}/signals`);
      setSignals(signalResponse.data);
      
      // Fetch news
      const newsResponse = await axios.get(`http://localhost:8000/api/news/${symbol}`);
      setNews(newsResponse.data);
      
    } catch (err) {
      setError('Failed to fetch stock data');
      console.error('Error fetching stock data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
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

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
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

  if (!stockData) {
    return (
      <Box p={3}>
        <Alert severity="warning">Stock not found</Alert>
      </Box>
    );
  }

  // Combine price and indicator data for chart
  const chartData = priceData.map((price, index) => {
    const indicator = indicatorData[index] || {};
    return {
      date: price.date,
      open: price.open,
      high: price.high,
      low: price.low,
      close: price.close,
      volume: price.volume,
      sma_20: indicator.sma_20,
      sma_50: indicator.sma_50,
      ema_20: indicator.ema_20,
      rsi_14: indicator.rsi_14,
    };
  });

  return (
    <Box>
      {/* Stock Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Typography variant="h4" gutterBottom>
              {stockData.symbol}
            </Typography>
            <Typography variant="h6" color="textSecondary">
              {stockData.name}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {stockData.sector} • {stockData.industry}
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box textAlign="right">
              <Typography variant="h4" color="primary">
                ₹{stockData.current_price || 'N/A'}
              </Typography>
              {stockData.latest_analysis && (
                <Box sx={{ mt: 1 }}>
                  <Chip
                    label={`${stockData.latest_analysis.signal_type} - ${stockData.latest_analysis.signal_strength}`}
                    color={getSignalColor(stockData.latest_analysis.signal_type)}
                    size="medium"
                  />
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Score: {stockData.latest_analysis.total_score}
                  </Typography>
                </Box>
              )}
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab icon={<ShowChart />} label="Price Chart" />
          <Tab icon={<Timeline />} label="Technical Indicators" />
          <Tab icon={<AttachMoney />} label="Signals" />
          <Tab icon={<Newspaper />} label="News" />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      {tabValue === 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Price Chart (60 Days)
          </Typography>
          <Box sx={{ height: 400 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={formatDate}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={formatDate}
                  formatter={(value) => [`₹${value}`, '']}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="close" 
                  stroke="#1976d2" 
                  strokeWidth={2}
                  name="Close Price"
                />
                {stockData.indicators?.sma_20 && (
                  <Line 
                    type="monotone" 
                    dataKey="sma_20" 
                    stroke="#4caf50" 
                    strokeWidth={1}
                    name="SMA 20"
                  />
                )}
                {stockData.indicators?.sma_50 && (
                  <Line 
                    type="monotone" 
                    dataKey="sma_50" 
                    stroke="#ff9800" 
                    strokeWidth={1}
                    name="SMA 50"
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </Box>
        </Paper>
      )}

      {tabValue === 1 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Technical Indicators
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>SMA 20</TableCell>
                  <TableCell>SMA 50</TableCell>
                  <TableCell>EMA 20</TableCell>
                  <TableCell>RSI</TableCell>
                  <TableCell>SuperTrend</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {indicatorData.slice(-10).reverse().map((indicator, index) => (
                  <TableRow key={index}>
                    <TableCell>{formatDate(indicator.date)}</TableCell>
                    <TableCell>{indicator.sma_20?.toFixed(2) || 'N/A'}</TableCell>
                    <TableCell>{indicator.sma_50?.toFixed(2) || 'N/A'}</TableCell>
                    <TableCell>{indicator.ema_20?.toFixed(2) || 'N/A'}</TableCell>
                    <TableCell>{indicator.rsi_14?.toFixed(2) || 'N/A'}</TableCell>
                    <TableCell>
                      <Chip
                        label={indicator.supertrend_direction}
                        color={indicator.supertrend_direction === 'BUY' ? 'success' : 'error'}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {tabValue === 2 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Trading Signals
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Signal</TableCell>
                  <TableCell>Entry</TableCell>
                  <TableCell>Target 1</TableCell>
                  <TableCell>Target 2</TableCell>
                  <TableCell>Stop Loss</TableCell>
                  <TableCell>R:R</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {signals.map((signal, index) => (
                  <TableRow key={index}>
                    <TableCell>{formatDate(signal.signal_date)}</TableCell>
                    <TableCell>
                      <Chip
                        label={signal.signal_type}
                        color={getSignalColor(signal.signal_type)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>₹{signal.entry_price}</TableCell>
                    <TableCell>₹{signal.target_1}</TableCell>
                    <TableCell>₹{signal.target_2}</TableCell>
                    <TableCell>₹{signal.stop_loss}</TableCell>
                    <TableCell>{signal.reward_ratio_1?.toFixed(2)}</TableCell>
                    <TableCell>
                      <Chip
                        label={signal.status}
                        color={signal.status === 'ACTIVE' ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {tabValue === 3 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Recent News
          </Typography>
          {news.length === 0 ? (
            <Typography variant="body2" color="textSecondary">
              No recent news available
            </Typography>
          ) : (
            news.map((article, index) => (
              <Card key={index} sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {article.title}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    {article.source} • {new Date(article.published_at).toLocaleString()}
                  </Typography>
                  {article.content && (
                    <Typography variant="body2" paragraph>
                      {article.content}
                    </Typography>
                  )}
                  <Box display="flex" gap={1} alignItems="center">
                    <Chip
                      label={article.sentiment_label}
                      color={article.sentiment_label === 'POSITIVE' ? 'success' : 
                             article.sentiment_label === 'NEGATIVE' ? 'error' : 'default'}
                      size="small"
                    />
                    <Typography variant="body2" color="textSecondary">
                      Score: {article.sentiment_score?.toFixed(2)}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            ))
          )}
        </Paper>
      )}
    </Box>
  );
};

export default StockDetail;