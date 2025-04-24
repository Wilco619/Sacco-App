import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  FormControlLabel,
  Checkbox
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import { AuthAPI, AdminAPI } from '../api/api';

const Settings = () => {
  const { currentUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [passwords, setPasswords] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [adminResetDialog, setAdminResetDialog] = useState({
    open: false,
    userId: '',
    generatedPassword: '',
    sendEmail: true
  });

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswords(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (passwords.newPassword !== passwords.confirmPassword) {
        setError("New passwords don't match");
        return;
    }

    try {
        setLoading(true);
        const result = await AuthAPI.changePassword(
            passwords.oldPassword, 
            passwords.newPassword
        );
        
        if (result.success) {
            setSuccess(result.message);
            if (result.warning) {
                setError(result.warning);
            }
            // Clear form after successful password change
            setPasswords({ 
                oldPassword: '', 
                newPassword: '', 
                confirmPassword: '' 
            });
        }
    } catch (err) {
        console.error('Password change error:', err);
        setError(err.message || 'Failed to change password');
    } finally {
        setLoading(false);
    }
  };

  const generatePassword = () => {
    const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    return Array(8).fill(0).map(() => 
      chars.charAt(Math.floor(Math.random() * chars.length))
    ).join('');
  };

  const handleAdminPasswordReset = async () => {
    try {
      setLoading(true);
      await AdminAPI.resetUserPassword(
        adminResetDialog.userId, 
        adminResetDialog.generatedPassword,
        adminResetDialog.sendEmail
      );
      setSuccess(`Password reset successful${
        adminResetDialog.sendEmail ? ' and email sent to user' : ''
      }`);
      setAdminResetDialog({
        open: false,
        userId: '',
        generatedPassword: '',
        sendEmail: true
      });
    } catch (err) {
      setError(err.message || 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>Settings</Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardHeader title="Change Password" />
            <CardContent>
              <form onSubmit={handleSubmit}>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Current Password"
                      type="password"
                      name="oldPassword"
                      value={passwords.oldPassword}
                      onChange={handlePasswordChange}
                      required
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="New Password"
                      type="password"
                      name="newPassword"
                      value={passwords.newPassword}
                      onChange={handlePasswordChange}
                      required
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Confirm New Password"
                      type="password"
                      name="confirmPassword"
                      value={passwords.confirmPassword}
                      onChange={handlePasswordChange}
                      required
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Button
                      type="submit"
                      variant="contained"
                      disabled={loading}
                    >
                      {loading ? <CircularProgress size={24} /> : 'Change Password'}
                    </Button>
                  </Grid>
                </Grid>
              </form>
            </CardContent>
          </Card>
        </Grid>

        {currentUser?.user_type === 'ADMIN' && (
          <Grid item xs={12}>
            <Card>
              <CardHeader title="Admin Password Reset" />
              <CardContent>
                <Button
                  variant="contained"
                  color="secondary"
                  onClick={() => setAdminResetDialog({
                    open: true,
                    userId: '',
                    generatedPassword: generatePassword(),
                    sendEmail: true
                  })}
                >
                  Reset User Password
                </Button>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      <Dialog
        open={adminResetDialog.open}
        onClose={() => setAdminResetDialog({ open: false, userId: '', generatedPassword: '', sendEmail: true })}
      >
        <DialogTitle>Reset User Password</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="User ID Number"
              value={adminResetDialog.userId}
              onChange={(e) => setAdminResetDialog(prev => ({
                ...prev,
                userId: e.target.value
              }))}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Generated Password"
              value={adminResetDialog.generatedPassword}
              InputProps={{ readOnly: true }}
              sx={{ mb: 2 }}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={adminResetDialog.sendEmail}
                  onChange={(e) => setAdminResetDialog(prev => ({
                    ...prev,
                    sendEmail: e.target.checked
                  }))}
                />
              }
              label="Send password to user's email"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setAdminResetDialog({ open: false, userId: '', generatedPassword: '', sendEmail: true })}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleAdminPasswordReset}
            disabled={!adminResetDialog.userId || loading}
          >
            Reset Password
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Settings;