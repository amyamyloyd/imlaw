import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Button,
  CssBaseline,
  ThemeProvider,
  createTheme,
} from '@mui/material';
import { FormFieldMapper } from './components/FormFieldMapper';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true
        }}
      >
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100vh' }}>
          <AppBar position="static">
            <Toolbar>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                Imlaw PDF Field Mapper
              </Typography>
              <Button color="inherit" component={Link} to="/mapper">
                Field Mapper
              </Button>
            </Toolbar>
          </AppBar>
          
          <Box sx={{ flex: 1, overflow: 'hidden' }}>
            <Routes>
              <Route path="/" element={<Navigate to="/mapper" replace />} />
              <Route path="/mapper" element={<FormFieldMapper />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
