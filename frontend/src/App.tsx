import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
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
import { CanonicalFieldsAdmin } from './pages/admin/CanonicalFieldsAdmin';

const theme = createTheme({
  palette: {
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
      <Router>
        <Box sx={{ flexGrow: 1 }}>
          <AppBar position="static">
            <Toolbar>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                ImLaw Admin
              </Typography>
              <Button color="inherit" component={Link} to="/">
                Home
              </Button>
              <Button color="inherit" component={Link} to="/admin/fields">
                Canonical Fields
              </Button>
            </Toolbar>
          </AppBar>

          <Container>
            <Routes>
              <Route path="/" element={
                <Box sx={{ mt: 4 }}>
                  <Typography variant="h4" gutterBottom>
                    Welcome to ImLaw Admin
                  </Typography>
                  <Typography variant="body1">
                    Use the navigation above to manage canonical fields and their mappings.
                  </Typography>
                </Box>
              } />
              <Route path="/admin/fields" element={<CanonicalFieldsAdmin />} />
            </Routes>
          </Container>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
