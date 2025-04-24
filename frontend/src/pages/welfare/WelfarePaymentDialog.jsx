import React, { useState } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    TextField,
    Typography,
    Box,
    CircularProgress,
    Alert,
    AlertTitle,
    Stepper,
    Step,
    StepLabel
} from '@mui/material';
import { axiosInstance } from '../../api/api';
import { 
    WELFARE_CONSTANTS, 
    MPESA_STATUS, 
    WELFARE_PAYMENT_MESSAGES,
    MPESA_CODES,
    MPESA_MESSAGES 
} from '../../constants/mpesaCodes';
import { useWelfare } from '../../contexts/WelfareContext';
import logger from '../../utils/logger';
import { WelfareAPI } from '../../api/api';
import { formatPhoneNumber, validatePhoneNumber } from '../../utils/validation';

const WelfarePaymentDialog = ({ open, onClose }) => {
    const [activeStep, setActiveStep] = useState(0);
    const [phoneNumber, setPhoneNumber] = useState('');
    const [error, setError] = useState(null);
    const [processing, setProcessing] = useState(false);
    const [paymentStatus, setPaymentStatus] = useState(null);
    const [checkoutId, setCheckoutId] = useState(null);

    const steps = ['Enter Details', 'Process Payment', 'Confirmation'];

    const { initiatePayment } = useWelfare();

    const handlePayment = async () => {
        setError(null);
        setProcessing(true);

        try {
            if (!validatePhoneNumber(phoneNumber)) {
                throw new Error('Please enter a valid Safaricom number');
            }

            const formattedPhone = formatPhoneNumber(phoneNumber);
            const response = await WelfareAPI.initiatePayment({
                phone_number: formattedPhone,
                amount: 300 // Fixed welfare amount
            });
            
            if (response.success) {
                setCheckoutId(response.checkoutRequestId);
                setActiveStep(1);
                startStatusCheck(response.checkoutRequestId);
            } else {
                setError(response.message || 'Failed to initiate payment');
                setActiveStep(0);
            }
        } catch (error) {
            setError(error.message || 'Failed to initiate payment');
            setActiveStep(0);
        } finally {
            setProcessing(false);
        }
    };

    const handlePaymentStatus = (resultCode) => {
        switch (resultCode) {
            case MPESA_CODES.SUCCESS:
                setPaymentStatus('completed');
                setError(null);
                break;
            case MPESA_CODES.USER_CANCELLED:
                setPaymentStatus('cancelled');
                setError(MPESA_MESSAGES[MPESA_CODES.USER_CANCELLED]);
                break;
            case MPESA_CODES.INSUFFICIENT_FUNDS:
                setPaymentStatus('failed');
                setError(MPESA_MESSAGES[MPESA_CODES.INSUFFICIENT_FUNDS]);
                break;
            case MPESA_CODES.WRONG_PIN:
                setPaymentStatus('failed');
                setError(MPESA_MESSAGES[MPESA_CODES.WRONG_PIN]);
                break;
            default:
                setPaymentStatus('failed');
                setError(MPESA_MESSAGES.default);
        }
    };

    const startStatusCheck = async (checkoutId) => {
        let attempts = 0;
        const maxAttempts = 20;
        const interval = setInterval(async () => {
            attempts++;
            try {
                const result = await WelfareAPI.checkPaymentStatus(checkoutId);
                
                logger.debug(`Status check attempt ${attempts}:`, result);
                
                if (result.status) {
                    clearInterval(interval);
                    handlePaymentStatus(result.status.ResultCode);
                    setActiveStep(2);
                    
                    if (result.status.ResultCode === MPESA_CODES.SUCCESS) {
                        refreshWelfare();
                        onClose(true);
                    }
                } else if (attempts >= maxAttempts) {
                    clearInterval(interval);
                    setError(MPESA_MESSAGES.TIMEOUT);
                    setPaymentStatus('timeout');
                    setActiveStep(2);
                }
            } catch (error) {
                logger.error('Status check error:', error);
                
                if (error.response?.status === 404 || 
                    error.response?.data?.message === "Transaction not found") {
                    clearInterval(interval);
                    setError(MPESA_MESSAGES.NOT_FOUND);
                    setPaymentStatus('not_found');
                    setActiveStep(2);
                }
            }
        }, 3000);

        return () => clearInterval(interval);
    };

    const renderPaymentStatus = () => {
        const severity = {
            completed: 'success',
            cancelled: 'warning',
            failed: 'error',
            timeout: 'error',
            not_found: 'warning'
        }[paymentStatus] || 'error';

        const title = {
            completed: WELFARE_PAYMENT_MESSAGES[MPESA_STATUS.COMPLETED],
            cancelled: 'Payment Cancelled',
            failed: 'Payment Failed',
            timeout: 'Payment Timeout',
            not_found: 'Transaction Not Found'
        }[paymentStatus] || 'Payment Error';

        return (
            <Alert severity={severity}>
                <AlertTitle>{title}</AlertTitle>
                {error || WELFARE_PAYMENT_MESSAGES[MPESA_STATUS.COMPLETED]}
            </Alert>
        );
    };

    const renderContent = () => {
        switch (activeStep) {
            case 0:
                return (
                    <Box sx={{ mt: 2 }}>
                        <Typography variant="body1" gutterBottom>
                            Monthly welfare contribution: {WELFARE_CONSTANTS.CURRENCY} {WELFARE_CONSTANTS.AMOUNT}
                        </Typography>
                        <TextField
                            fullWidth
                            label="Phone Number"
                            value={phoneNumber}
                            onChange={(e) => setPhoneNumber(e.target.value)}
                            disabled={processing}
                            sx={{ mt: 2 }}
                            placeholder="e.g., 254712345678"
                        />
                    </Box>
                );
            case 1:
                return (
                    <Box sx={{ mt: 2, textAlign: 'center' }}>
                        <CircularProgress />
                        <Typography sx={{ mt: 2 }}>
                            {WELFARE_PAYMENT_MESSAGES[MPESA_STATUS.PENDING]}
                        </Typography>
                    </Box>
                );
            case 2:
                return (
                    <Box sx={{ mt: 2 }}>
                        {renderPaymentStatus()}
                        {paymentStatus !== 'completed' && (
                            <Button
                                fullWidth
                                variant="outlined"
                                onClick={() => {
                                    setActiveStep(0);
                                    setError(null);
                                    setPaymentStatus(null);
                                }}
                                sx={{ mt: 2 }}
                            >
                                Try Again
                            </Button>
                        )}
                    </Box>
                );
            default:
                return null;
        }
    };

    return (
        <Dialog open={open} onClose={() => !processing && onClose()} maxWidth="sm" fullWidth>
            <DialogTitle>Welfare Contribution Payment</DialogTitle>
            <DialogContent>
                <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
                    {steps.map((label) => (
                        <Step key={label}>
                            <StepLabel>{label}</StepLabel>
                        </Step>
                    ))}
                </Stepper>

                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}

                {renderContent()}
            </DialogContent>
            <DialogActions>
                {activeStep === 0 && (
                    <>
                        <Button onClick={onClose} disabled={processing}>
                            Cancel
                        </Button>
                        <Button
                            variant="contained"
                            onClick={handlePayment}
                            disabled={processing || !phoneNumber}
                        >
                            Pay Now
                        </Button>
                    </>
                )}
            </DialogActions>
        </Dialog>
    );
};

export default WelfarePaymentDialog;