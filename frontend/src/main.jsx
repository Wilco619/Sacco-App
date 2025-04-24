import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { SharesProvider } from './contexts/SharesContext';
import { WelfareProvider } from './contexts/WelfareContext';
import { RegistrationProvider } from './contexts/RegistrationContext';
import { LoanProvider } from './contexts/LoanContext';
import { Toaster } from 'react-hot-toast';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <WelfareProvider>
          <SharesProvider>
            <RegistrationProvider>
              <LoanProvider>
                <Toaster position="top-right" />
                <App />
              </LoanProvider>
            </RegistrationProvider>
          </SharesProvider>
        </WelfareProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);