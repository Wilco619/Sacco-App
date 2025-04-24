import React, { useState, useEffect } from 'react';
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
  Stack
} from '@mui/material';

const OTPVerification = () => {
  const [otp, setOtp] = useState('');
  const [countdown, setCountdown] = useState(60);
  const [canResend, setCanResend] = useState(false);
  const { verifyOTP, resendOTP, loading, error, setError } = useAuth();
  const navigate = useNavigate();

  // Countdown timer for resending OTP
  useEffect(() => {
    let timer;
    if (countdown > 0 && !canResend) {
      timer = setTimeout(() => setCountdown(countdown - 1), 1000);
    } else if (countdown === 0 && !canResend) {
      setCanResend(true);
    }
    
    return () => clearTimeout(timer);
  }, [countdown, canResend]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Clear previous errors
    setError(null);
    
    if (!otp.trim()) {
      setError('OTP is required');
      return;
    }
    
    try {
      const success = await verifyOTP(otp);
      if (success) {
        toast.success('Login successful!');
        navigate('/dashboard');
      }
    } catch (err) {
      toast.error('OTP verification failed. Please try again.');
    }
  };

  const handleResendOTP = async () => {
    if (!canResend) return;
    
    try {
      const success = await resendOTP();
      if (success) {
        toast.success('New OTP sent successfully!');
        setCountdown(60);
        setCanResend(false);
      }
    } catch (err) {
      toast.error('Failed to resend OTP. Please try again.');
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
                Verify OTP
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                A one-time password has been sent to your email
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
                id="otp"
                label="One-Time Password (OTP)"
                fullWidth
                margin="normal"
                placeholder="Enter the 6-digit code"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                inputProps={{ maxLength: 6 }}
                disabled={loading}
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={loading}
                sx={{ mt: 3 }}
              >
                {loading ? (
                  <>
                    <CircularProgress size={24} sx={{ mr: 1 }} color="inherit" />
                    Verifying...
                  </>
                ) : (
                  "Verify OTP"
                )}
              </Button>
            </Box>
          </form>
        </CardContent>
        <CardActions sx={{ flexDirection: 'column', pb: 3 }}>
          <Button
            color="primary"
            onClick={handleResendOTP}
            disabled={!canResend || loading}
            sx={{ mb: 1 }}
          >
            {canResend ? "Resend OTP" : `Resend OTP in ${countdown}s`}
          </Button>
          
          <Button
            color="inherit"
            onClick={() => navigate('/login')}
          >
            Back to Login
          </Button>
        </CardActions>
      </Card>
    </Box>
  );
};

export default OTPVerification;