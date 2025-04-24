import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  MenuItem,
  CircularProgress,
  Alert
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { AdminAPI } from '../../api/api';

const CreateUser = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [alert, setAlert] = useState({ open: false, message: '', severity: '' });
  const [formData, setFormData] = useState({
    id_number: '',
    email: '',
    password: '', // Add password field
    first_name: '',
    last_name: '',
    phone_number: '',
    address: '',
    user_type: 'MEMBER'
  });

  const generatePassword = () => {
    // Generate a random 8-character password
    const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    const password = Array(8).fill(0).map(() =>
      chars.charAt(Math.floor(Math.random() * chars.length))
    ).join('');
    setFormData(prev => ({ ...prev, password }));
  };

  useEffect(() => {
    generatePassword(); // Generate password when component mounts
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await AdminAPI.createUser(formData);
      // Show success message with password
      setAlert({
        open: true,
        message: `User created successfully. Initial password: ${formData.password}`,
        severity: 'success'
      });
      navigate('/admin/users');
    } catch (err) {
      setError(err.message || 'Failed to create user');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" sx={{ mb: 3 }}>Create New User</Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {alert.open && <Alert severity={alert.severity} sx={{ mb: 2 }}>{alert.message}</Alert>}

      <Paper sx={{ p: 3 }}>
        <form onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="ID Number"
                name="id_number"
                value={formData.id_number}
                onChange={handleChange}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="First Name"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Last Name"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Phone Number"
                name="phone_number"
                value={formData.phone_number}
                onChange={handleChange}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                select
                label="User Type"
                name="user_type"
                value={formData.user_type}
                onChange={handleChange}
                required
              >
                <MenuItem value="MEMBER">Member</MenuItem>
                <MenuItem value="ADMIN">Admin</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Address"
                name="address"
                value={formData.address}
                onChange={handleChange}
                multiline
                rows={3}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Generated Password"
                value={formData.password}
                InputProps={{
                  readOnly: true,
                }}
                helperText="This password will be sent to the user"
              />
              <Button
                variant="text"
                onClick={generatePassword}
                sx={{ mt: 1 }}
              >
                Generate New Password
              </Button>
            </Grid>
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/admin/users')}
                  disabled={loading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={loading}
                >
                  {loading ? <CircularProgress size={24} /> : 'Create User'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Box>
  );
};

export default CreateUser;