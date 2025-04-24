import React, { useState, useEffect } from 'react';
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
    StepLabel,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Grid
} from '@mui/material';
import { SharesAPI } from '../../api/api';
import { MPESA_CODES, MPESA_MESSAGES, MPESA_RETRY_ALLOWED } from '../../constants/mpesaCodes';
import { SHARE_CONSTANTS, SHARE_OPTIONS } from '../../constants/mpesaCodes';

const SharePurchaseDialog = ({ open, onClose }) => {
    const [activeStep, setActiveStep] = useState(0);
    const [phoneNumber, setPhoneNumber] = useState('');
    const [error, setError] = useState(null);
    const [processing, setProcessing] = useState(false);
    const [paymentStatus, setPaymentStatus] = useState(null);
    const [checkoutId, setCheckoutId] = useState(null);
    const [numberOfShares, setNumberOfShares] = useState(1);
    const [shareDetails, setShareDetails] = useState({
        amount: SHARE_CONSTANTS.VALUE,
        shares: 1
    });
    const [statusResult, setStatusResult] = useState(null);

    const steps = ['Enter Details', 'Process Payment', 'Confirmation'];

    const handleShareChange = (event) => {
        const shares = event.target.value;
        setNumberOfShares(shares);
        setShareDetails({
            shares: shares,
            amount: shares * SHARE_CONSTANTS.VALUE
        });
    };

    const handleRetry = () => {
        setError(null);
        setPaymentStatus(null);
        setActiveStep(0);
        setCheckoutId(null);
    };

    const renderActionButtons = (canRetry = true) => (
        <Box sx={{ mt: 2, display: 'flex', gap: 1, flexDirection: 'column' }}>
            {canRetry && (
                <Button
                    variant="contained"
                    onClick={handleRetry}
                    fullWidth
                    color="warning"
                >
                    Try Again
                </Button>
            )}
            <Button
                variant="outlined"
                onClick={() => onClose(false)}
                fullWidth
            >
                Close
            </Button>
        </Box>
    );

    const renderShareDetails = () => (
        <Box sx={{ mt: 2, mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="subtitle2" color="primary" gutterBottom>
                Share Purchase Details
            </Typography>
            <Grid container spacing={2}>
                <Grid item xs={6}>
                    <Typography variant="body2">
                        Number of Shares: {numberOfShares}
                    </Typography>
                </Grid>
                <Grid item xs={6}>
                    <Typography variant="body2">
                        Amount: {SHARE_CONSTANTS.CURRENCY} {(numberOfShares * SHARE_CONSTANTS.VALUE).toLocaleString()}
                    </Typography>
                </Grid>
            </Grid>
        </Box>
    );

    const renderContent = () => {
        switch (activeStep) {
            case 0:
                return (
                    <Box sx={{ mt: 2 }}>
                        <TextField
                            fullWidth
                            label="Phone Number"
                            value={phoneNumber}
                            onChange={(e) => setPhoneNumber(e.target.value)}
                            disabled={processing}
                            sx={{ mb: 2 }}
                        />
                        <FormControl fullWidth sx={{ mb: 2 }}>
                            <InputLabel>Number of Shares</InputLabel>
                            <Select
                                value={numberOfShares}
                                onChange={handleShareChange}
                                disabled={processing}
                                label="Number of Shares"
                            >
                                {SHARE_OPTIONS.map(({ value, label, amount }) => (
                                    <MenuItem key={value} value={value}>
                                        {label} - {SHARE_CONSTANTS.CURRENCY} {amount.toLocaleString()}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                        {renderShareDetails()}
                        <Typography variant="caption" color="textSecondary">
                            Each share is valued at KSH {SHARE_CONSTANTS.VALUE.toLocaleString()}
                        </Typography>
                    </Box>
                );
            case 1:
                return (
                    <Box sx={{ mt: 2, textAlign: 'center' }}>
                        <CircularProgress />
                        <Typography sx={{ mt: 2 }}>
                            Please check your phone for the STK push...
                        </Typography>
                        <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                            Purchasing {shareDetails.shares} {shareDetails.shares === 1 ? 'share' : 'shares'} 
                            for KSH {(shareDetails.shares * SHARE_CONSTANTS.VALUE).toLocaleString()}
                        </Typography>
                    </Box>
                );
            case 2:
                const severity = paymentStatus === 'completed' ? 'success' : 
                               paymentStatus === 'cancelled' ? 'warning' : 'error';
                               
                return (
                    <Box sx={{ mt: 2 }}>
                        <Alert severity={severity} sx={{ mb: 2 }}>
                            <AlertTitle>
                                {paymentStatus === 'completed' ? 'Success!' : 
                                 paymentStatus === 'cancelled' ? 'Payment Cancelled' : 'Payment Failed'}
                            </AlertTitle>
                            {error || MPESA_MESSAGES[MPESA_CODES.SUCCESS]}
                        </Alert>
                        {paymentStatus !== 'completed' && renderActionButtons(
                            MPESA_RETRY_ALLOWED[statusResult?.status?.ResultCode] !== false
                        )}
                    </Box>
                );
            default:
                return null;
        }
    };

    const handlePurchase = async () => {
        setError(null);
        setProcessing(true);

        try {
            const response = await SharesAPI.purchaseShares(
                shareDetails.amount,
                phoneNumber
            );

            if (response.success) {
                setCheckoutId(response.checkoutRequestId);
                setActiveStep(1);
                startStatusCheck(response.checkoutRequestId);
            } else {
                setError(response.message || 'Failed to initiate payment');
            }
        } catch (error) {
            setError(error.message || 'Failed to process payment');
        } finally {
            setProcessing(false);
        }
    };

    const startStatusCheck = async (checkoutId) => {
        let attempts = 0;
        const maxAttempts = 20;
        const interval = setInterval(async () => {
            attempts++;
            try {
                const result = await SharesAPI.checkPaymentStatus(checkoutId);
                const resultCode = result.status.ResultCode;
                
                // Store the result
                setStatusResult(result);
                
                if (resultCode === MPESA_CODES.SUCCESS) {
                    clearInterval(interval);
                    setPaymentStatus('completed');
                    setActiveStep(2);
                    onClose(true);
                } else if (resultCode === MPESA_CODES.USER_CANCELLED) {
                    clearInterval(interval);
                    setError(MPESA_MESSAGES[resultCode]);
                    setPaymentStatus('cancelled');
                    setActiveStep(2);
                } else if (
                    resultCode === MPESA_CODES.INSUFFICIENT_FUNDS ||
                    resultCode === MPESA_CODES.WRONG_PIN ||
                    resultCode === MPESA_CODES.INVALID_ACCOUNT
                ) {
                    clearInterval(interval);
                    setError(MPESA_MESSAGES[resultCode]);
                    setPaymentStatus('failed');
                    setActiveStep(2);
                } else if (attempts >= maxAttempts) {
                    clearInterval(interval);
                    setError(MPESA_MESSAGES.TIMEOUT);
                    setPaymentStatus('timeout');
                    setActiveStep(2);
                }
            } catch (error) {
                console.error('Status check error:', error);
            }
        }, 3000);

        return () => clearInterval(interval);
    };

    return (
        <Dialog open={open} onClose={() => !processing && onClose()} maxWidth="sm" fullWidth>
            <DialogTitle>Purchase Shares</DialogTitle>
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
                            onClick={handlePurchase}
                            disabled={processing || !phoneNumber}
                        >
                            Purchase Shares
                        </Button>
                    </>
                )}
            </DialogActions>
        </Dialog>
    );
};

export default SharePurchaseDialog;