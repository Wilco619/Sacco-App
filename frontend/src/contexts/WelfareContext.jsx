import React, { createContext, useContext, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { toast } from 'react-hot-toast';
import { WelfareAPI } from '../api/api';
import { WELFARE_CONSTANTS } from '../constants/mpesaCodes';

const WelfareContext = createContext(null);

export const useWelfare = () => {
    const context = useContext(WelfareContext);
    if (!context) {
        throw new Error('useWelfare must be used within WelfareProvider');
    }
    return context;
};

export const WelfareProvider = ({ children }) => {
    const { currentUser } = useAuth();
    const [welfareData, setWelfareData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchWelfareData = useCallback(async () => {
        if (!currentUser) return;

        try {
            setLoading(true);
            setError(null);
            
            const data = await WelfareAPI.getMyContributions();
            
            const transformedData = {
                contributions: data.contributions || [],
                can_contribute: data.can_contribute ?? true,
                next_contribution_date: data.next_contribution_date,
                monthly_amount: data.monthly_amount || WELFARE_CONSTANTS.AMOUNT,
                last_contribution_date: data.last_contribution_date,
                payment_type: 'WELFARE'  // Add payment type
            };

            setWelfareData(transformedData);
        } catch (err) {
            const errorMessage = err.message || 'Failed to fetch welfare data';
            setError(errorMessage);
            toast.error(errorMessage);
        } finally {
            setLoading(false);
        }
    }, [currentUser]);

    const refreshWelfare = useCallback(async () => {
        try {
            await fetchWelfareData();
            toast.success('Welfare data refreshed');
        } catch (error) {
            toast.error('Failed to refresh welfare data');
        }
    }, [fetchWelfareData]);

    const initiatePayment = useCallback(async (phoneNumber) => {
        try {
            const response = await WelfareAPI.initiatePayment({
                phone_number: phoneNumber,
                amount: WELFARE_CONSTANTS.AMOUNT,
                payment_type: 'WELFARE'
            });
            
            if (response.success) {
                toast.success('Payment initiated successfully');
            }
            return response;
        } catch (error) {
            toast.error(error.message || 'Failed to initiate payment');
            throw error;
        }
    }, []);

    React.useEffect(() => {
        if (currentUser) {
            fetchWelfareData();
        }
    }, [currentUser, fetchWelfareData]);

    const value = {
        welfareData,
        loading,
        error,
        refreshWelfare,
        initiatePayment  // Add this to the context value
    };

    return (
        <WelfareContext.Provider value={value}>
            {children}
        </WelfareContext.Provider>
    );
};

export default WelfareContext;