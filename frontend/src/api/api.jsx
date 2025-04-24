import axios from 'axios';

// Create axios instance with default config
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const axiosInstance = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding token
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If error is 401 and we haven't tried refreshing token yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          // No refresh token, logout user
          return Promise.reject(error);
        }
        
        const response = await axios.post(`${API_URL}/api/token/refresh/`, {
          refresh: refreshToken
        });
        
        if (response.data.access) {
          localStorage.setItem('access_token', response.data.access);
          // Retry the original request with new token
          originalRequest.headers['Authorization'] = `Bearer ${response.data.access}`;
          return axiosInstance(originalRequest);
        }
      } catch (refreshError) {
        // If refresh token is invalid, clear storage and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
        window.location = '/login';
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

// Auth API calls
const AuthAPI = {
  login: async (idNumber, password) => {
    try {
      const response = await axiosInstance.post('/token/', {
        id_number: idNumber,
        password: password
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: "Login failed" };
    }
  },
  
  verifyOTP: async (otp) => {
    try {
      const response = await axiosInstance.post('/users/verify-login/', {
        otp: otp
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: "OTP verification failed" };
    }
  },
  
  requestOTP: async () => {
    try {
      const response = await axiosInstance.post('/users/request-otp/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: "Failed to request OTP" };
    }
  },
  
  changePassword: async (oldPassword, newPassword) => {
    try {
      const response = await axiosInstance.post('/users/change-password/', {
        old_password: oldPassword,
        new_password: newPassword
      });
      
      if (response.data.status === 'success') {
        return {
          success: true,
          message: response.data.message,
          warning: !response.data.email_sent ? 
              'Password changed but notification email failed to send' : null
        };
      } else {
        throw new Error(response.data.error || 'Password change failed');
      }
    } catch (error) {
      if (error.response?.data?.error) {
        throw new Error(error.response.data.error);
      }
      throw new Error('Failed to change password. Please try again.');
    }
  },

  updateFirstLoginStatus: async () => {
    try {
      const response = await axiosInstance.patch('/users/me/', {
        is_first_login: false
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: "Failed to update login status" };
    }
  }
};

// Users API calls
const UsersAPI = {
  getCurrentUser: async () => {
    try {
      const response = await axiosInstance.get('/users/me/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: "Failed to fetch user data" };
    }
  },
  
  updateProfile: async (profileData) => {
    try {
      const response = await axiosInstance.patch('/users/profiles/me/', profileData);
      return response.data;
    } catch (error) {
      if (error.response?.status === 404) {
        // If profile doesn't exist, try to get the user data which will create the profile
        await UsersAPI.getCurrentUser();
        // Retry the update
        const retryResponse = await axiosInstance.patch('/users/profiles/me/', profileData);
        return retryResponse.data;
      }
      throw error.response?.data || { error: "Failed to update profile" };
    }
  },
  
  uploadDocument: async (documentType, file) => {
    try {
      const formData = new FormData();
      formData.append(documentType, file);
      
      const response = await axiosInstance.patch('/users/profiles/me/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: "Failed to upload document" };
    }
  }
};

// Admin API calls
const AdminAPI = {
  getAllUsers: async () => {
    try {
      const response = await axiosInstance.get('/users/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: "Failed to fetch users" };
    }
  },
  
  createUser: async (userData) => {
    try {
      const response = await axiosInstance.post('/users/', {
        ...userData,
        password: userData.password // Make sure password is included
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: "Failed to create user" };
    }
  },
  
  updateUser: async (idNumber, userData) => {
    try {
      const response = await axiosInstance.patch(
        `/users/by-id-number/${idNumber}/`,
        userData
      );
      return response.data;
    } catch (error) {
      console.error('User update error:', error.response || error);
      throw error.response?.data || { error: "Failed to update user" };
    }
  },
  
  verifyDocuments: async (profileId, isVerified) => {
    try {
      const response = await axiosInstance.patch(`/users/profiles/${profileId}/verify_documents/`, {
        documents_verified: isVerified
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: "Failed to verify documents" };
    }
  },
  
  resetUserPassword: async (userId, newPassword, sendEmail = true) => {
    try {
      const response = await axiosInstance.post('/users/admin-reset-password/', {
        user_id: userId,
        new_password: newPassword,
        send_email: sendEmail
      });
      return response.data;
    } catch (error) {
      if (error.response?.status === 403) {
        throw new Error('You do not have permission to reset passwords');
      }
      if (error.response?.status === 404) {
        throw new Error('User not found');
      }
      throw error.response?.data || { error: "Failed to reset password" };
    }
  },

  getUser: async (idNumber) => {
    try {
      const response = await axiosInstance.get(`/users/by-id-number/${idNumber}/`);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: "Failed to fetch user" };
    }
  },

  getUserProfile: async (idNumber) => {
    try {
      const response = await axiosInstance.get(`/users/by-id-number/${idNumber}/profile/`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch user profile:', error.response || error);
      throw error.response?.data || { error: "Failed to fetch user profile" };
    }
  },

  updateUserProfile: async (idNumber, profileData) => {
    try {
      const formData = new FormData();
      
      // Convert profileData to FormData if it contains files
      Object.keys(profileData).forEach(key => {
        if (profileData[key] instanceof File) {
          formData.append(key, profileData[key]);
        } else if (profileData[key] !== null && profileData[key] !== undefined) {
          formData.append(key, profileData[key]);
        }
      });

      const response = await axiosInstance.patch(
        `/users/by-id-number/${idNumber}/profile/`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Profile update error:', error.response || error);
      throw error.response?.data || { error: "Failed to update profile" };
    }
  },

  getUserDocuments: async (idNumber) => {
    try {
      // First get the user profile
      const profile = await AdminAPI.getUserProfile(idNumber);
      
      // Transform the data
      return {
        id_front: {
          url: profile.id_front_image,
          verified: profile.id_front_verified
        },
        id_back: {
          url: profile.id_back_image,
          verified: profile.id_back_verified
        },
        passport_photo: {
          url: profile.passport_photo,
          verified: profile.passport_photo_verified
        },
        signature: {
          url: profile.signature,
          verified: profile.signature_verified
        },
        verification_status: profile.verification_status,
        verification_notes: profile.verification_notes
      };
    } catch (error) {
      console.error('Failed to fetch user documents:', error);
      throw error.response?.data || { error: "Failed to fetch documents" };
    }
  },

  verifyDocument: async (idNumber, documentType, status, notes = '') => {
    try {
      console.log('Verifying document:', { idNumber, documentType, status });
      const response = await axiosInstance.patch(
        `/users/by-id-number/${idNumber}/verify-documents/`,
        {
          document_type: documentType || 'all',
          status: status,
          notes: notes
        }
      );
      return response.data;
    } catch (error) {
      console.error('Document verification error:', error.response || error);
      throw error.response?.data || { error: "Failed to verify document" };
    }
  },

  getUnverifiedUsers: async () => {
    try {
      const response = await axiosInstance.get('/users/unverified-documents/');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch unverified users:', error);
      throw error.response?.data || { error: "Failed to fetch unverified users" };
    }
  },

  getDashboardStats: async () => {
    try {
      console.log('Fetching dashboard stats...');
      const response = await axiosInstance.get('/users/dashboard-stats/');
      console.log('Dashboard stats response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error.response || error);
      throw error.response?.data || { error: "Failed to fetch dashboard stats" };
    }
  }
};

// Shares API calls
const SharesAPI = {
  getSharesStatement: async () => {
    try {
      const response = await axiosInstance.get('/accounts/shares/share_statement/');
      return response.data;
    } catch (error) {
      console.error('Error fetching shares statement:', error);
      throw error.response?.data || { error: "Failed to fetch shares statement" };
    }
  },

  purchaseShares: async (amount, phoneNumber) => {
    try {
      const response = await axiosInstance.post('/mpesa/initiate_payment/', {
        amount: amount,
        phone_number: phoneNumber,
        payment_type: 'SHARES'
      });

      if (response.data.success) {
        return {
          success: true,
          checkoutRequestId: response.data.checkout_request_id,
          message: response.data.message
        };
      }
      throw new Error(response.data.message || 'Failed to initiate payment');
    } catch (error) {
      console.error('Share purchase error:', error);
      throw error.response?.data || { error: "Failed to initiate share purchase" };
    }
  },

  checkPaymentStatus: async (checkoutRequestId) => {
    try {
      const response = await axiosInstance.post('/mpesa/query_status/', {
        checkout_request_id: checkoutRequestId,
        payment_type: 'SHARES'  // Add payment type explicitly
      });
      return response.data;
    } catch (error) {
      console.error('Payment status check error:', error);
      throw error.response?.data || { message: 'Failed to check payment status' };
    }
  },

  getNextPurchaseDate: async () => {
    try {
      const response = await axiosInstance.get('/accounts/shares/next-purchase-date/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: "Failed to get next purchase date" };
    }
  }
};

// Welfare API calls
const WelfareAPI = {
  getMyContributions: async () => {
    try {
      const response = await axiosInstance.get('/welfare/contributions/my_contributions/');
      return {
        ...response.data,
        payment_type: 'WELFARE'
      };
    } catch (error) {
      throw error.response?.data || { message: 'Failed to fetch welfare data' };
    }
  },

  initiatePayment: async (paymentData) => {
    try {
      const response = await axiosInstance.post('/welfare/contributions/initiate_payment/', {
        phone_number: paymentData.phone_number,
        amount: paymentData.amount || 300, // Default welfare amount
        payment_type: 'WELFARE'
      });

      if (!response.data.success) {
        throw new Error(response.data.message || 'Failed to initiate payment');
      }

      return response.data;
    } catch (error) {
      console.error('Welfare payment error:', error);
      throw error.response?.data || { 
        success: false, 
        message: 'Failed to initiate payment' 
      };
    }
  },

  checkPaymentStatus: async (checkoutRequestId) => {
    try {
      const response = await axiosInstance.post('/mpesa/query_status/', {
        checkout_request_id: checkoutRequestId,
        payment_type: 'WELFARE'
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Failed to check payment status' };
    }
  },

  // Admin methods
  getWelfareFunds: async () => {
    try {
      const response = await axiosInstance.get('/welfare/welfare-funds/');
      // Ensure we return an array
      return Array.isArray(response.data) ? response.data : response.data?.results || [];
    } catch (error) {
      console.error('Failed to fetch welfare funds:', error);
      throw error.response?.data || { message: 'Failed to fetch welfare funds' };
    }
  },

  createWelfareFund: async (fundData) => {
    try {
        // Format the date if not provided
        const data = {
            ...fundData,
            date_established: fundData.date_established || new Date().toISOString().split('T')[0]
        };
        
        const response = await axiosInstance.post('/welfare/welfare-funds/', data);
        return response.data;
    } catch (error) {
        console.error('Create welfare fund error:', error);
        throw error.response?.data || { message: 'Failed to create welfare fund' };
    }
  },

  updateWelfareFund: async (fundId, fundData) => {
    try {
      const response = await axiosInstance.patch(`/welfare/welfare-funds/${fundId}/`, fundData);
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Failed to update welfare fund' };
    }
  },

  deleteWelfareFund: async (fundId) => {
    try {
      await axiosInstance.delete(`/welfare/welfare-funds/${fundId}/`);
      return true;
    } catch (error) {
      throw error.response?.data || { message: 'Failed to delete welfare fund' };
    }
  }
};

// Loans API calls
const LoansAPI = {
  // Member endpoints
  getMyLoans: async () => {
    try {
      const response = await axiosInstance.get('/loans/loans/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Failed to fetch loans' };
    }
  },

  applyForLoan: async (loanData) => {
    try {
      const response = await axiosInstance.post('/loans/loans/', loanData);
      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to apply for loan');
      }
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Failed to apply for loan' };
    }
  },

  requestGuarantor: async (requestData) => {
    try {
      const response = await axiosInstance.post('/loans/guarantors/', requestData);
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Failed to request guarantor' };
    }
  },

  getAvailableAmount: async () => {
    try {
      const response = await axiosInstance.get('/loans/loans/available_amount/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Failed to fetch available amount' };
    }
  },

  getLoanEligibility: async () => {
    try {
      const response = await axiosInstance.get('/loans/loans/loan_eligibility/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Failed to fetch loan eligibility' };
    }
  },

  // Admin endpoints
  getAllLoans: async () => {
    try {
      const response = await axiosInstance.get('/loans/loans/all/');
      if (!response.data.success) {
        throw new Error(response.data.error);
      }
      return response.data.data;
    } catch (error) {
      throw error.response?.data || { message: 'Failed to fetch all loans' };
    }
  },

  approveLoan: async (loanId) => {
    try {
      const response = await axiosInstance.post(`/loans/loans/${loanId}/approve/`);
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Failed to approve loan' };
    }
  },

  rejectLoan: async (loanId, reason) => {
    try {
      const response = await axiosInstance.post(`/loans/loans/${loanId}/reject/`, { reason });
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Failed to reject loan' };
    }
  }
};

export { axiosInstance, AuthAPI, UsersAPI, AdminAPI, SharesAPI, WelfareAPI, LoansAPI };