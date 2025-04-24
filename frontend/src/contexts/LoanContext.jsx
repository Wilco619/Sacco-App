import React, { createContext, useContext, useState, useCallback } from 'react';
import { LoansAPI } from '../api/api';
import { toast } from 'react-hot-toast';
import { useAuth } from './AuthContext';

const LoanContext = createContext(null);

export const LoanProvider = ({ children }) => {
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { currentUser } = useAuth();

  const fetchLoans = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = currentUser?.user_type === 'ADMIN' 
        ? await LoansAPI.getAllLoans()
        : await LoansAPI.getMyLoans();
      setLoans(data);
    } catch (err) {
      setError(err.message);
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  }, [currentUser]);

  const applyForLoan = useCallback(async (loanData) => {
    try {
      const response = await LoansAPI.applyForLoan(loanData);
      toast.success('Loan application submitted successfully');
      fetchLoans();
      return response;
    } catch (err) {
      toast.error(err.message);
      throw err;
    }
  }, [fetchLoans]);

  const approveLoan = useCallback(async (loanId) => {
    try {
      await LoansAPI.approveLoan(loanId);
      toast.success('Loan approved successfully');
      fetchLoans();
    } catch (err) {
      toast.error(err.message);
      throw err;
    }
  }, [fetchLoans]);

  return (
    <LoanContext.Provider value={{
      loans,
      loading,
      error,
      fetchLoans,
      applyForLoan,
      approveLoan
    }}>
      {children}
    </LoanContext.Provider>
  );
};

export const useLoan = () => {
  const context = useContext(LoanContext);
  if (!context) {
    throw new Error('useLoan must be used within a LoanProvider');
  }
  return context;
};