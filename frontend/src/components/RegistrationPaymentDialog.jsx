import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel
} from '@mui/material';
import { useMpesa } from '../hooks/useMpesa';

const RegistrationPaymentDialog = ({ open, onClose }) => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [activeStep, setActiveStep] = useState(0);
  const [requestIds, setRequestIds] = useState({
    checkoutRequestId: null,
    merchantRequestId: null
  });
  
  const { 
    initiateMpesaPayment, 
    checkPaymentStatus, 
    loading, 
    error, 
    paymentStatus, 
    checkoutId,
    setError 
  } = useMpesa();

  const steps = ['Enter Phone Number', 'Confirm Payment', 'Payment Status'];

  useEffect(() => {
    let statusCheck;
    let attempts = 0;
    const MAX_ATTEMPTS = 20;
    
    if (checkoutId) {
      statusCheck = setInterval(async () => {
        attempts++;
        const result = await checkPaymentStatus(checkoutId);
        
        switch(result.status) {
          case 'completed':
            clearInterval(statusCheck);
            onClose(true);
            break;
            
          case 'cancelled':
          case 'failed':
          case 'timeout':
            clearInterval(statusCheck);
            setError(result.message);
            setActiveStep(2);
            break;
            
          case 'pending':
            if (attempts >= MAX_ATTEMPTS) {
              clearInterval(statusCheck);
              setError('Payment request timed out. Please try again.');
              setActiveStep(2);
            }
            break;
        }
      }, 3000);
    }

    return () => {
      if (statusCheck) clearInterval(statusCheck);
    };
  }, [checkoutId]);

  const handlePaymentRetry = () => {
    setActiveStep(0);
    setPhoneNumber('');
  };

  const handleInitiatePayment = async (e) => {
    e.preventDefault();
    if (!phoneNumber) {
      setError('Phone number is required');
      return;
    }

    try {
      const formattedPhone = formatPhoneNumber(phoneNumber);
      console.log('Initiating payment with phone:', formattedPhone);
      
      const response = await initiateMpesaPayment(formattedPhone, 1, 'REGISTRATION');
      if (response.success) {
        setRequestIds({
          checkoutRequestId: response.checkout_request_id,
          merchantRequestId: response.merchant_request_id
        });
        setActiveStep(1);
      } else {
        setError(response.message || 'Failed to initiate payment');
      }
    } catch (err) {
      console.error('Payment initiation failed:', err);
      setError(err.message || 'Failed to initiate payment');
    }
  };

  const validatePhoneNumber = (number) => {
    // Remove any spaces or special characters
    const cleaned = number.replace(/\D/g, '');
    
    // Check if it starts with 254 or 0
    if (cleaned.startsWith('254')) {
      return cleaned.length === 12;
    } else if (cleaned.startsWith('0')) {
      return cleaned.length === 10;
    }
    return false;
  };

  const formatPhoneNumber = (number) => {
    // Remove any non-digit characters
    const cleaned = number.replace(/\D/g, '');
    
    // Handle different formats
    if (cleaned.startsWith('254')) {
      return cleaned;
    } else if (cleaned.startsWith('0')) {
      return '254' + cleaned.substring(1);
    } else if (cleaned.startsWith('7') || cleaned.startsWith('1')) {
      return '254' + cleaned;
    }
    return cleaned;
  };

  const handlePhoneNumberChange = (e) => {
    const value = e.target.value;
    if (value.length <= 12) {
      setPhoneNumber(value);
      setError(null);
    }
  };

  const renderProcessingState = () => (
    <Box sx={{ textAlign: 'center', py: 3 }}>
      <Typography variant="h6" gutterBottom>
        Processing Payment
      </Typography>
      <CircularProgress sx={{ my: 2 }} />
      <Typography variant="body2" color="text.secondary">
        Please check your phone for the M-Pesa prompt
      </Typography>
      {requestIds.checkoutRequestId && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
          Request ID: {requestIds.checkoutRequestId}
        </Typography>
      )}
      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
        Payment will timeout after 10 seconds of inactivity
      </Typography>
    </Box>
  );

  const renderPaymentStatus = () => {
    const renderRetryButton = (message = 'Try Again') => (
      <Button
        variant="contained"
        onClick={handlePaymentRetry}
        fullWidth
        sx={{ mt: 2 }}
        color={paymentStatus === 'cancelled' ? 'warning' : 'primary'}
      >
        {message}
      </Button>
    );

    const renderActionButtons = (canRetry = true) => (
      <Box sx={{ mt: 2 }}>
        {canRetry && renderRetryButton()}
        <Button
          variant="outlined"
          onClick={() => onClose(false)}
          fullWidth
          sx={{ mt: 1 }}
        >
          Close
        </Button>
      </Box>
    );

    if (paymentStatus === 'completed') {
      return (
        <Box>
          <Alert severity="success" sx={{ mb: 2 }}>
            <AlertTitle>Payment Successful!</AlertTitle>
            Your registration is now complete. You can now proceed to use the system.
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              Transaction ID: {requestIds.checkoutRequestId}
            </Typography>
          </Alert>
        </Box>
      );
    }

    if (error) {
      const resultCode = error?.response?.data?.status?.ResultCode;
      const canRetry = MPESA_RETRY_ALLOWED[resultCode] !== false;
      const severity = paymentStatus === 'cancelled' ? 'warning' : 'error';
      const message = MPESA_MESSAGES[resultCode] || error;

      return (
        <Box>
          <Alert severity={severity} sx={{ mb: 2 }}>
            <AlertTitle>
              {paymentStatus === 'cancelled' ? 'Payment Cancelled' : 'Payment Failed'}
            </AlertTitle>
            {message}
            {requestIds.checkoutRequestId && (
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                Reference: {requestIds.checkoutRequestId}
              </Typography>
            )}
          </Alert>
          {renderActionButtons(canRetry)}
        </Box>
      );
    }

    return null;
  };

  const PaymentInstructions = () => (
    <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
      <Typography variant="subtitle2" gutterBottom>
        Payment Instructions:
      </Typography>
      <Typography variant="body2" component="ol" sx={{ pl: 2 }}>
        <li>Enter your M-Pesa registered phone number</li>
        <li>Click "Pay Now" to receive the payment prompt</li>
        <li>Enter your M-Pesa PIN when prompted</li>
        <li>Wait for confirmation message</li>
      </Typography>
    </Box>
  );

  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Box component="form" onSubmit={handleInitiatePayment}>
            <Typography variant="body1" gutterBottom>
              Please enter your M-PESA phone number to pay the registration fee of KSH 1,000.
            </Typography>
            <TextField
              autoFocus
              label="Phone Number"
              fullWidth
              value={phoneNumber}
              onChange={handlePhoneNumberChange}
              required
              disabled={loading}
              helperText="Format: 07XXXXXXXX or 254XXXXXXXXX"
              sx={{ mt: 2 }}
            />
            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
            <PaymentInstructions />
          </Box>
        );
      case 1:
        return renderProcessingState();
      case 2:
        return (
          <Box sx={{ py: 3 }}>
            {renderPaymentStatus()}
          </Box>
        );
      default:
        return null;
    }
  };

  const handlePaymentComplete = (success) => {
    if (success) {
        onClose();
        navigate('/', { 
            replace: true, 
            state: { 
                paymentSuccess: true 
            } 
        });
    } else {
        onClose();
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={() => !loading && onClose(false)} 
      maxWidth="sm" 
      fullWidth
    >
      <DialogTitle>Registration Payment</DialogTitle>
      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ py: 3 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
        {renderStepContent(activeStep)}
      </DialogContent>
      <DialogActions>
        {activeStep === 0 && (
          <>
            <Button onClick={() => onClose(false)}>Cancel</Button>
            <Button
              variant="contained"
              onClick={handleInitiatePayment}
              disabled={loading || !phoneNumber || !validatePhoneNumber(phoneNumber)}
            >
              {loading ? <CircularProgress size={24} /> : 'Pay Now'}
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default RegistrationPaymentDialog;