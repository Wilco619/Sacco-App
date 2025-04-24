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
  Alert,
  Switch,
  FormControlLabel,
  Tabs,
  Tab
} from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import { AdminAPI } from '../../api/api';
import { Person as PersonIcon, Badge as BadgeIcon } from '@mui/icons-material';

const EditUser = () => {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [userData, setUserData] = useState({
    id_number: '',
    email: '',
    first_name: '',
    last_name: '',
    phone_number: '',
    address: '',
    user_type: '',
    is_active: true
  });
  const [profileData, setProfileData] = useState({
    date_of_birth: '',
    gender: '',
    occupation: '',
    next_of_kin: '',
    next_of_kin_contact: '',
    profile_picture: null
  });

  useEffect(() => {
    fetchUserData();
  }, [userId]);

  const fetchUserData = async () => {
    try {
      setLoading(true);
      const [user, profile] = await Promise.all([
        AdminAPI.getUser(userId),
        AdminAPI.getUserProfile(userId)
      ]);
      setUserData(user);
      setProfileData(profile);
      setError(null);
    } catch (err) {
      setError('Failed to fetch user data');
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUserChange = (e) => {
    const { name, value, checked } = e.target;
    setUserData(prev => ({
      ...prev,
      [name]: name === 'is_active' ? checked : value
    }));
  };

  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfileData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      await Promise.all([
        AdminAPI.updateUser(userId, userData),
        AdminAPI.updateUserProfile(userId, profileData)
      ]);
      navigate('/admin/users');
    } catch (err) {
      setError(err.message || 'Failed to update user');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <CircularProgress />;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" sx={{ mb: 3 }}>Edit User</Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab icon={<PersonIcon />} label="Basic Info" />
          <Tab icon={<BadgeIcon />} label="Profile Details" />
        </Tabs>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <form onSubmit={handleSubmit}>
          {activeTab === 0 && (
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="ID Number"
                  name="id_number"
                  value={userData.id_number}
                  disabled
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Email"
                  name="email"
                  type="email"
                  value={userData.email}
                  onChange={handleUserChange}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="First Name"
                  name="first_name"
                  value={userData.first_name}
                  onChange={handleUserChange}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Last Name"
                  name="last_name"
                  value={userData.last_name}
                  onChange={handleUserChange}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Phone Number"
                  name="phone_number"
                  value={userData.phone_number}
                  onChange={handleUserChange}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  select
                  label="User Type"
                  name="user_type"
                  value={userData.user_type}
                  onChange={handleUserChange}
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
                  value={userData.address}
                  onChange={handleUserChange}
                  multiline
                  rows={3}
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={userData.is_active}
                      onChange={handleUserChange}
                      name="is_active"
                    />
                  }
                  label="Active Account"
                />
              </Grid>
            </Grid>
          )}

          {activeTab === 1 && (
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Date of Birth"
                  type="date"
                  name="date_of_birth"
                  value={profileData.date_of_birth || ''}
                  onChange={handleProfileChange}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  select
                  label="Gender"
                  name="gender"
                  value={profileData.gender || ''}
                  onChange={handleProfileChange}
                >
                  <MenuItem value="">Select Gender</MenuItem>
                  <MenuItem value="Male">Male</MenuItem>
                  <MenuItem value="Female">Female</MenuItem>
                  <MenuItem value="Other">Other</MenuItem>
                </TextField>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Occupation"
                  name="occupation"
                  value={profileData.occupation || ''}
                  onChange={handleProfileChange}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Next of Kin"
                  name="next_of_kin"
                  value={profileData.next_of_kin || ''}
                  onChange={handleProfileChange}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Next of Kin Contact"
                  name="next_of_kin_contact"
                  value={profileData.next_of_kin_contact || ''}
                  onChange={handleProfileChange}
                />
              </Grid>
            </Grid>
          )}

          <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              onClick={() => navigate('/admin/users')}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button
              variant="outlined"
              onClick={() => navigate(`/admin/users/${userId}/profile`)}
            >
              View Full Profile
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={saving}
            >
              {saving ? <CircularProgress size={24} /> : 'Save Changes'}
            </Button>
          </Box>
        </form>
      </Paper>
    </Box>
  );
};

export default EditUser;