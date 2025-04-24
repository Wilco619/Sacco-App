import React from 'react';
import { Outlet } from 'react-router-dom';
import { Box, Container, Paper } from '@mui/material';

/**
 * AuthLayout wraps authentication-related pages like login and OTP verification
 * Provides consistent styling and layout for the authentication flow
 */
const AuthLayout = () => {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: (theme) => theme.palette.grey[100]
      }}
    >
      <Container component="main" maxWidth="xs" sx={{ my: 4, flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <Paper
          elevation={3}
          sx={{
            borderRadius: 2,
            overflow: 'hidden'
          }}
        >
          <Outlet />
        </Paper>
      </Container>
      
      <Box
        component="footer"
        sx={{
          py: 3,
          px: 2,
          mt: 'auto',
          backgroundColor: (theme) => theme.palette.grey[200],
          textAlign: 'center',
          fontSize: '0.875rem',
          color: (theme) => theme.palette.text.secondary
        }}
      >
        © {new Date().getFullYear()} Your Company Name. All rights reserved.
      </Box>
    </Box>
  );
};

export default AuthLayout;