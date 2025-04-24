import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';

// Material UI imports
import {
  Card,
  CardContent,
  CardHeader,
  CardActions,
  Typography,
  TextField,
  Button,
  Alert,
  Box,
  CircularProgress,
  Link,
  Avatar
} from '@mui/material';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';

const Login = () => {
  const [idNumber, setIdNumber] = useState('');
  const [password, setPassword] = useState('');
  const [formErrors, setFormErrors] = useState({});
  const { login, loading, error, setError } = useAuth();
  const navigate = useNavigate();

  const validateForm = () => {
    const errors = {};
    if (!idNumber.trim()) errors.idNumber = 'ID Number is required';
    if (!password) errors.password = 'Password is required';
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Clear previous errors
    setError(null);
    
    if (!validateForm()) return;
    
    try {
      const success = await login(idNumber, password);
      if (success) {
        toast.success('OTP sent successfully. Please verify to continue.');
        navigate('/verify-otp');
      }
    } catch (err) {
      toast.error('Login failed. Please check your credentials.');
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: 2
      }}
    >
      <Card sx={{ maxWidth: 400, width: '100%' }}>
        <CardHeader
          sx={{ textAlign: 'center' }}
          avatar={
            <Box sx={{ width: '100%', display: 'flex', justifyContent: 'center', mt: 2 }}>
              <img src="/logo.png" alt="Logo" style={{ height: '48px' }} />
            </Box>
          }
          title={
            <Box sx={{ mt: 2 }}>
              <Typography variant="h5" component="h2" sx={{ fontWeight: 'bold' }}>
                Login to Your Account
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Enter your credentials to access your account
              </Typography>
            </Box>
          }
        />
        <CardContent>
          <form onSubmit={handleSubmit}>
            <Box sx={{ mb: 2 }}>
              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}

              <TextField
                id="id-number"
                label="ID Number"
                fullWidth
                margin="normal"
                placeholder="Enter your ID number"
                value={idNumber}
                onChange={(e) => setIdNumber(e.target.value)}
                disabled={loading}
                error={!!formErrors.idNumber}
                helperText={formErrors.idNumber}
              />

              <TextField
                id="password"
                label="Password"
                type="password"
                fullWidth
                margin="normal"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                error={!!formErrors.password}
                helperText={formErrors.password}
              />

              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1, mb: 2 }}>
                <Link
                  href="#"
                  variant="body2"
                  onClick={(e) => {
                    e.preventDefault();
                    toast.error("Please contact an administrator to reset your password");
                  }}
                >
                  Forgot password?
                </Link>
              </Box>

              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={loading}
                sx={{ mt: 2 }}
              >
                {loading ? (
                  <>
                    <CircularProgress size={24} sx={{ mr: 1 }} color="inherit" />
                    Logging in...
                  </>
                ) : (
                  "Login"
                )}
              </Button>
            </Box>
          </form>
        </CardContent>
        <CardActions sx={{ justifyContent: 'center', pb: 3 }}>
          <Typography variant="body2" color="text.secondary">
            Don't have an account? Contact your administrator.
          </Typography>
        </CardActions>
      </Card>
    </Box>
  );
};

export default Login;