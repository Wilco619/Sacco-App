import React, { createContext, useState, useContext, useEffect } from 'react';
import { AuthAPI } from '../api/api';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isOtpSent, setIsOtpSent] = useState(false);
  const [tempCredentials, setTempCredentials] = useState(null);
  const navigate = useNavigate();

  // Check if user is already logged in on mount
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const userData = localStorage.getItem('user_data');
        
        if (token && userData) {
          setCurrentUser(JSON.parse(userData));
        }
      } catch (err) {
        console.error("Auth status check failed:", err);
      } finally {
        setLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const login = async (idNumber, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await AuthAPI.login(idNumber, password);
      
      // Save tokens but don't set user as authenticated yet
      localStorage.setItem('access_token', response.access);
      localStorage.setItem('refresh_token', response.refresh);
      
      // Save temp data for OTP verification
      setTempCredentials({
        tokens: { access: response.access, refresh: response.refresh },
        user: response.user
      });
      
      setIsOtpSent(true);
      return true;
      
    } catch (err) {
      setError(err.error || "Login failed. Please check your credentials.");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const verifyOTP = async (otp) => {
    setLoading(true);
    setError(null);
    try {
      const response = await AuthAPI.verifyOTP(otp);
      
      // Update tokens after OTP verification
      localStorage.setItem('access_token', response.access);
      localStorage.setItem('refresh_token', response.refresh);
      
      // Include is_first_login in the user data
      setCurrentUser({
        ...response.user,
        is_first_login: response.user.is_first_login
      });
      
      setIsOtpSent(false);
      setTempCredentials(null);
      
      return true;
    } catch (err) {
      setError(err.message || "OTP verification failed");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const resendOTP = async () => {
    setLoading(true);
    setError(null);
    try {
      await AuthAPI.requestOTP();
      return true;
    } catch (err) {
      setError(err.error || "Failed to request a new OTP. Please try again.");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_data');
    setCurrentUser(null);
    navigate('/login');
  };

  const updateUserData = (userData) => {
    localStorage.setItem('user_data', JSON.stringify(userData));
    setCurrentUser(userData);
  };

  const isAdmin = () => {
    return currentUser?.user_type === 'ADMIN';
  };

  const value = {
    currentUser,
    login,
    logout,
    verifyOTP,
    resendOTP,
    updateUserData,
    isAdmin,
    isOtpSent,
    loading,
    error,
    setError
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};