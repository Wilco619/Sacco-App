import React, { Suspense, lazy, useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import { AuthProvider } from './contexts/AuthContext';

// Main layout components
import AppLayout from './components/layout/AppLayout';
import AuthLayout from './components/layout/AuthLayout';
import LoadingScreen from './components/LoadingScreen';

// Auth pages - direct imports for critical paths
import Login from './pages/Login';
import OTPVerification from './pages/OTPVerification';

// Lazy-loaded page components
const MemberDashboard = lazy(() => import('./pages/dashboard/MemberDashboard'));
const AdminDashboard = lazy(() => import('./pages/dashboard/AdminDashboard'));
const Profile = lazy(() => import('./pages/member/Profile'));
const NotFound = lazy(() => import('./pages/NotFound'));
const Settings = lazy(() => import('./pages/Settings'));
const SharesView = lazy(() => import('./pages/shares/SharesView')); // Import SharesView component
const WelfareView = lazy(() => import('./pages/welfare/WelfareView')); // Import WelfareView component
const Account = lazy(() => import('./pages/member/Account'));
const MyLoans = lazy(() => import('./pages/loans/MyLoans'));
const LoanManagement = lazy(() => import('./pages/admin/LoanManagement'));

// Admin pages
const UserManagement = lazy(() => import('./pages/admin/UserManagement'));
const CreateUser = lazy(() => import('./pages/admin/CreateUser'));
const EditUser = lazy(() => import('./pages/admin/EditUser'));
const DocumentVerification = lazy(() => import('./pages/admin/DocumentVerification'));
const WelfareManagement = lazy(() => import('./pages/admin/WelfareManagement')); // Add this to your imports

// Dialog components
import ChangePasswordDialog from './components/ChangePasswordDialog';

// Protected route wrapper
const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const { currentUser, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && currentUser.user_type !== 'ADMIN') {
    return <Navigate to="/home" replace />;
  }

  return children;
};

const DashboardRouter = () => {
  const { currentUser } = useAuth();
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);

  useEffect(() => {
    // Check explicitly for is_first_login being true
    console.log('Current user:', currentUser); // For debugging
    if (currentUser && currentUser.is_first_login === true) {
      setShowPasswordDialog(true);
    }
  }, [currentUser]);

  return (
    <>
      {currentUser?.user_type === 'ADMIN' ? <AdminDashboard /> : <MemberDashboard />}
      {showPasswordDialog && (
        <ChangePasswordDialog
          open={showPasswordDialog}
          onClose={async (success) => {
            if (success) {
              // Update the user's first login status in the backend
              try {
                await AuthAPI.updateFirstLoginStatus();
                window.location.reload();
              } catch (error) {
                console.error('Failed to update first login status:', error);
              }
            }
            setShowPasswordDialog(false);
          }}
        />
      )}
    </>
  );
};

const App = () => {
  const { currentUser, isOtpSent } = useAuth();

  return (
    <div>
      <Suspense fallback={<LoadingScreen />}>
        <Routes>
          {/* Auth routes */}
          <Route element={<AuthLayout />}>
            <Route index element={<Navigate to={currentUser ? "/home" : "/login"} replace />} />
            <Route 
              path="login" 
              element={
                currentUser ? (
                  <Navigate to="/home" replace />
                ) : isOtpSent ? (
                  <Navigate to="/verify-otp" replace />
                ) : (
                  <Login />
                )
              } 
            />
            <Route 
              path="verify-otp" 
              element={
                currentUser ? (
                  <Navigate to="/home" replace />
                ) : !isOtpSent ? (
                  <Navigate to="/login" replace />
                ) : (
                  <OTPVerification />
                )
              } 
            />
          </Route>

          {/* Protected routes with AppLayout */}
          <Route element={<AppLayout />}>
            <Route path="/" element={<Navigate to="/home" replace />} />
            <Route 
              path="/home" 
              element={
                <ProtectedRoute>
                  <Suspense fallback={<LoadingScreen />}>
                    <DashboardRouter />
                  </Suspense>
                </ProtectedRoute>
              } 
            />
            {/* Member routes */}
            <Route 
              path="profile" 
              element={
                <ProtectedRoute>
                  <Suspense fallback={<LoadingScreen />}>
                    <Profile />
                  </Suspense>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="shares" 
              element={
                <ProtectedRoute>
                  <Suspense fallback={<LoadingScreen />}>
                    <SharesView />
                  </Suspense>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="welfare" 
              element={
                <ProtectedRoute>
                  <Suspense fallback={<LoadingScreen />}>
                    <WelfareView />
                  </Suspense>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="account" 
              element={
                <ProtectedRoute>
                  <Suspense fallback={<LoadingScreen />}>
                    <Account />
                  </Suspense>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="loans" 
              element={
                <ProtectedRoute>
                  <Suspense fallback={<LoadingScreen />}>
                    <MyLoans />
                  </Suspense>
                </ProtectedRoute>
              } 
            />

            {/* Admin routes */}
            <Route path="admin">
              <Route 
                path="users" 
                element={
                  <ProtectedRoute requireAdmin>
                    <Suspense fallback={<LoadingScreen />}>
                      <UserManagement />
                    </Suspense>
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="users/create" 
                element={
                  <ProtectedRoute requireAdmin>
                    <Suspense fallback={<LoadingScreen />}>
                      <CreateUser />
                    </Suspense>
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="users/edit/:userId" 
                element={
                  <ProtectedRoute requireAdmin>
                    <Suspense fallback={<LoadingScreen />}>
                      <EditUser />
                    </Suspense>
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="verify-documents" 
                element={
                  <ProtectedRoute requireAdmin>
                    <Suspense fallback={<LoadingScreen />}>
                      <DocumentVerification />
                    </Suspense>
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="users/:userId/profile" 
                element={
                  <ProtectedRoute requireAdmin>
                    <Suspense fallback={<LoadingScreen />}>
                      <Profile adminView />
                    </Suspense>
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="users/:userId/verify-documents" 
                element={
                  <ProtectedRoute requireAdmin>
                    <Suspense fallback={<LoadingScreen />}>
                      <DocumentVerification />
                    </Suspense>
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="document-verification" 
                element={
                  <ProtectedRoute requireAdmin>
                    <Suspense fallback={<LoadingScreen />}>
                      <DocumentVerification />
                    </Suspense>
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="document-verification/:userId" 
                element={
                  <ProtectedRoute requireAdmin>
                    <Suspense fallback={<LoadingScreen />}>
                      <DocumentVerification />
                    </Suspense>
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="welfare" 
                element={
                  <ProtectedRoute requireAdmin>
                    <Suspense fallback={<LoadingScreen />}>
                      <WelfareManagement />
                    </Suspense>
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="loans" 
                element={
                  <ProtectedRoute requireAdmin>
                    <Suspense fallback={<LoadingScreen />}>
                      <LoanManagement />
                    </Suspense>
                  </ProtectedRoute>
                } 
              />
            </Route>

            {/* Settings route */}
            <Route 
              path="settings" 
              element={
                <ProtectedRoute>
                  <Suspense fallback={<LoadingScreen />}>
                    <Settings />
                  </Suspense>
                </ProtectedRoute>
              } 
            />
          </Route>

          {/* 404 route */}
          <Route 
            path="*" 
            element={
              <Suspense fallback={<LoadingScreen />}>
                <NotFound />
              </Suspense>
            } 
          />
        </Routes>
      </Suspense>
    </div>
  );
};

export default App;