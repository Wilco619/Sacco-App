import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { axiosInstance } from '../api/api';

const RegistrationContext = createContext(null);

export const RegistrationProvider = ({ children }) => {
    const [registrationStatus, setRegistrationStatus] = useState({
        registration_paid: false,
        needs_payment: true,
        registration_fee: 1000,
        status: 'pending',
        has_profile: false,
        id_number: null
    });
    const [loading, setLoading] = useState(true);
    const { currentUser } = useAuth();

    const checkRegistrationStatus = async () => {
        if (!currentUser) return;
        
        try {
            const response = await axiosInstance.get('/accounts/members/registration-status/');
            console.log('Registration status response:', response.data);
            setRegistrationStatus(response.data);
        } catch (error) {
            console.error('Failed to fetch registration status:', error);
            setRegistrationStatus({
                registration_paid: false,
                needs_payment: true,
                registration_fee: 1000,
                status: 'error',
                has_profile: false,
                id_number: currentUser?.id_number
            });
        } finally {
            setLoading(false);
        }
    };

    const processRegistrationPayment = async (receiptNumber) => {
        try {
            const response = await axiosInstance.post('/accounts/members/registration_payment/', {
                receipt_number: receiptNumber
            });
            await checkRegistrationStatus();
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Payment processing failed'
            };
        }
    };

    useEffect(() => {
        checkRegistrationStatus();
    }, [currentUser]);

    return (
        <RegistrationContext.Provider value={{
            registrationStatus,
            loading,
            processRegistrationPayment,
            refreshStatus: checkRegistrationStatus
        }}>
            {children}
        </RegistrationContext.Provider>
    );
};

export const useRegistration = () => useContext(RegistrationContext);