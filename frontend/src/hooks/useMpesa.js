import { useState, useEffect } from 'react';
import { axiosInstance } from '../api/api';
import { MPESA_CODES, MPESA_MESSAGES } from '../constants/mpesaCodes';

export const useMpesa = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [checkoutId, setCheckoutId] = useState(null);
  const [transactionDetails, setTransactionDetails] = useState(null);

  const initiateMpesaPayment = async (phoneNumber, amount, paymentType = 'REGISTRATION') => {
    setLoading(true);
    setError(null);
    try {
      const response = await axiosInstance.post('/mpesa/initiate_payment/', {
        phone_number: phoneNumber,
        amount: Number(amount),
        payment_type: paymentType
      });

      if (response.data.success) {
        const details = {
          checkoutRequestId: response.data.checkout_request_id,
          merchantRequestId: response.data.merchant_request_id,
          transactionId: response.data.transaction_id
        };
        
        setCheckoutId(details.checkoutRequestId);
        setTransactionDetails(details);
        setPaymentStatus('processing');
        
        return {
          success: true,
          ...details,
          message: response.data.message
        };
      } else {
        throw new Error(response.data.message || 'Failed to initiate payment');
      }
    } catch (error) {
      setError(error.response?.data?.message || error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const checkPaymentStatus = async (checkoutRequestId) => {
    try {
      const response = await axiosInstance.post('/mpesa/query_status/', {
        checkout_request_id: checkoutRequestId
      });

      if (response.data.success) {
        const status = response.data.status;
        const resultCode = status.ResultCode;
        
        // Enhanced status handling
        switch(resultCode) {
          case MPESA_CODES.SUCCESS:
            setPaymentStatus('completed');
            return { status: 'completed', message: MPESA_MESSAGES[resultCode] };
            
          case MPESA_CODES.USER_CANCELLED:
            setPaymentStatus('cancelled');
            return { status: 'cancelled', message: MPESA_MESSAGES[resultCode] };
            
          case MPESA_CODES.TIMEOUT:
            setPaymentStatus('timeout');
            return { status: 'timeout', message: MPESA_MESSAGES[resultCode] };
            
          case MPESA_CODES.INSUFFICIENT_FUNDS:
          case MPESA_CODES.WRONG_PIN:
            setPaymentStatus('failed');
            return { 
              status: 'failed', 
              message: MPESA_MESSAGES[resultCode],
              canRetry: true 
            };

          case MPESA_CODES.INVALID_AMOUNT:
          case MPESA_CODES.INVALID_NUMBER:
            setPaymentStatus('failed');
            return { 
              status: 'failed', 
              message: MPESA_MESSAGES[resultCode],
              canRetry: false 
            };

          case 'None':
          case null:
          case undefined:
            setPaymentStatus('pending');
            return { status: 'pending', message: 'Payment is being processed' };
            
          default:
            setPaymentStatus('failed');
            return { 
              status: 'failed', 
              message: MPESA_MESSAGES.default,
              canRetry: true 
            };
        }
      }
      return { status: 'pending', message: 'Checking payment status...' };
    } catch (error) {
      console.error('Status check error:', error);
      setError(error.response?.data?.message || 'Failed to check payment status');
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Failed to check payment status',
        canRetry: true 
      };
    }
  };

  const resetPaymentStatus = () => {
    setPaymentStatus(null);
    setCheckoutId(null);
    setTransactionDetails(null);
    setError(null);
  };

  return {
    loading,
    error,
    paymentStatus,
    checkoutId,
    transactionDetails,
    initiateMpesaPayment,
    checkPaymentStatus,
    resetPaymentStatus,
    setError,
    setPaymentStatus
  };
};