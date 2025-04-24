import React, { createContext, useContext, useState, useCallback } from 'react';
import { axiosInstance } from '../api/api';
import { useAuth } from './AuthContext';
import { toast } from 'react-hot-toast';

// Create context
const SharesContext = createContext(null);

export const SharesProvider = ({ children }) => {
    const [sharesData, setSharesData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { currentUser } = useAuth();

    const fetchSharesData = useCallback(async () => {
        if (!currentUser) return;

        try {
            setLoading(true);
            setError(null);
            
            // Updated API endpoint to match backend
            const response = await axiosInstance.get('/accounts/my_shares/');
            
            if (response.data) {
                const transformedData = {
                    number_of_shares: response.data.number_of_shares || 0,
                    value_per_share: response.data.value_per_share || 1000,
                    total_value: response.data.total_value || 0,
                    monthly_contribution: response.data.monthly_contribution || 0,
                    last_payment_date: response.data.last_payment_date,
                    transactions: response.data.transactions?.map(transaction => ({
                        ...transaction,
                        date: transaction.payment_date || transaction.created_at,
                        transaction_id: transaction.mpesa_receipt || transaction.id
                    })) || []
                };
                
                setSharesData(transformedData);
            }
        } catch (err) {
            const errorMessage = err.response?.data?.message || 'Failed to fetch shares data';
            setError(errorMessage);
            toast.error(errorMessage);
        } finally {
            setLoading(false);
        }
    }, [currentUser]);

    const refreshShares = useCallback(async () => {
        try {
            await fetchSharesData();
            toast.success('Shares data refreshed');
        } catch (error) {
            toast.error('Failed to refresh shares data');
        }
    }, [fetchSharesData]);

    // Initial fetch
    React.useEffect(() => {
        if (currentUser) {
            fetchSharesData();
        }
    }, [currentUser, fetchSharesData]);

    // Create the context value object
    const contextValue = {
        sharesData,
        loading,
        error,
        refreshShares
    };

    return (
        <SharesContext.Provider value={contextValue}>
            {children}
        </SharesContext.Provider>
    );
};

// Export the useShares hook
export const useShares = () => {
    const context = useContext(SharesContext);
    if (!context) {
        throw new Error('useShares must be used within SharesProvider');
    }
    return context;
};

// Export the SharesContext for direct access if needed
export default SharesContext;