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
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { Search, TrendingUp } from '@mui/icons-material';
import axios from 'axios';

const News = () => {
  const [newsData, setNewsData] = useState([]);
  const [trendingNews, setTrendingNews] = useState([]);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchSymbol, setSearchSymbol] = useState('');
  const [selectedSource, setSelectedSource] = useState('');

  useEffect(() => {
    fetchNewsData();
  }, []);

  const fetchNewsData = async () => {
    try {
      setLoading(true);
      
      // Fetch trending news
      const trendingResponse = await axios.get('http://localhost:8000/api/news/trending?limit=10');
      setTrendingNews(trendingResponse.data);
      
      // Fetch news sources
      const sourcesResponse = await axios.get('http://localhost:8000/api/news/sources');
      setSources(sourcesResponse.data);
      
    } catch (err) {
      setError('Failed to fetch news data');
      console.error('Error fetching news data:', err);
    } finally {
      setLoading(false);
    }
  };

  const searchNews = async () => {
    if (!searchSymbol) return;
    
    try {
      setLoading(true);
      const response = await axios.get(`http://localhost:8000/api/news/${searchSymbol}`);
      setNewsData(response.data);
    } catch (err) {
      setError(`Failed to fetch news for ${searchSymbol}`);
      console.error('Error fetching news:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'POSITIVE':
        return 'success';
      case 'NEGATIVE':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading && newsData.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Market News & Sentiment
      </Typography>

      {/* Search Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Search News by Stock Symbol
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          <TextField
            label="Stock Symbol (e.g., RELIANCE)"
            value={searchSymbol}
            onChange={(e) => setSearchSymbol(e.target.value.toUpperCase())}
            size="small"
            sx={{ minWidth: 300 }}
          />
          <Button
            variant="contained"
            onClick={searchNews}
            startIcon={<Search />}
            disabled={!searchSymbol}
          >
            Search
          </Button>
        </Box>
      </Paper>

      {error && (
        <Box mb={3}>
          <Alert severity="error">{error}</Alert>
        </Box>
      )}

      {/* Trending News */}
      <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
        Trending News
      </Typography>
      <Grid container spacing={3}>
        {trendingNews.map((news, index) => (
          <Grid item xs={12} md={6} key={index}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                  <Box>
                    <Typography variant="subtitle2" color="primary">
                      {news.symbol} • {news.name}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {formatDate(news.published_at)}
                    </Typography>
                  </Box>
                  <Chip
                    label={news.sentiment_label}
                    color={getSentimentColor(news.sentiment_label)}
                    size="small"
                  />
                </Box>
                <Typography variant="body1" gutterBottom>
                  {news.title}
                </Typography>
                <Box display="flex" alignItems="center" gap={2}>
                  <Typography variant="body2" color="textSecondary">
                    Source: {news.source}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Relevance: {news.relevance_score?.toFixed(2)}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* News Sources */}
      <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
        News Sources
      </Typography>
      <Grid container spacing={2}>
        {sources.map((source, index) => (
          <Grid item xs={12} md={4} key={index}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {source.source}
                </Typography>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  {source.article_count} articles
                </Typography>
                <Typography variant="body2">
                  Avg Sentiment: {source.average_sentiment}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Search Results */}
      {newsData.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h5" gutterBottom>
            News for {searchSymbol}
          </Typography>
          <Grid container spacing={3}>
            {newsData.map((news, index) => (
              <Grid item xs={12} key={index}>
                <Card>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                      <Typography variant="caption" color="textSecondary">
                        {formatDate(news.published_at)}
                      </Typography>
                      <Chip
                        label={news.sentiment_label}
                        color={getSentimentColor(news.sentiment_label)}
                        size="small"
                      />
                    </Box>
                    <Typography variant="h6" gutterBottom>
                      {news.title}
                    </Typography>
                    {news.content && (
                      <Typography variant="body1" paragraph>
                        {news.content}
                      </Typography>
                    )}
                    <Box display="flex" alignItems="center" gap={2}>
                      <Typography variant="body2" color="textSecondary">
                        Source: {news.source}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Sentiment Score: {news.sentiment_score?.toFixed(2)}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Relevance: {news.relevance_score?.toFixed(2)}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
    </Box>
  );
};

export default News;