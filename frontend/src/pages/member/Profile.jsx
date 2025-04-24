import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Avatar, 
  Grid, 
  Paper, 
  TextField, 
  Button, 
  MenuItem, 
  CircularProgress, 
  Snackbar, 
  Alert, 
  Divider, 
  Card, 
  CardContent,
  CardHeader,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  ImageList,
  ImageListItem,
  ImageListItemBar,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { UsersAPI, AdminAPI, API_URL } from '../../api/api';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import SaveIcon from '@mui/icons-material/Save';
import PersonIcon from '@mui/icons-material/Person';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { useParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

// Styled components
const ProfilePicture = styled(Avatar)(({ theme }) => ({
  width: theme.spacing(12),
  height: theme.spacing(12),
  margin: 'auto',
  marginBottom: theme.spacing(2),
  border: `2px solid ${theme.palette.primary.main}`
}));

const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1,
});

// Add these styles in the component
const documentPreviewStyles = {
  cursor: 'pointer',
  transition: 'transform 0.2s',
  '&:hover': {
    transform: 'scale(1.02)',
  }
};

const Profile = ({ adminView }) => {
  const { userId } = useParams(); // Will be available in admin view
  const { currentUser } = useAuth();

  const [profile, setProfile] = useState({
    profile_picture: null,
    date_of_birth: '',
    gender: '',
    occupation: '',
    next_of_kin: '',
    next_of_kin_contact: '',
    id_front_image: null,
    id_back_image: null,
    passport_photo: null,
    signature: null,
  });
  
  const [user, setUser] = useState({
    id_number: '',
    email: '',
    first_name: '',
    last_name: '',
    phone_number: '',
    address: '',
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [alert, setAlert] = useState({ open: false, message: '', severity: 'info' });
  const [previewUrls, setPreviewUrls] = useState({
    profile_picture: null,
    id_front_image: null,
    id_back_image: null,
    passport_photo: null,
    signature: null,
  });

  const [documentsDialogOpen, setDocumentsDialogOpen] = useState(false);
  const [uploadedDocuments, setUploadedDocuments] = useState([]);

  // Modify field permissions based on user type
  const isFieldEditable = (fieldName) => {
    // Admin can edit all fields
    if (currentUser?.user_type === 'ADMIN') {
      return true;
    }
    
    // Regular members cannot edit these fields
    const restrictedFields = ['id_number', 'phone_number', 'email'];
    return !restrictedFields.includes(fieldName);
  };
  
  // Fetch user profile data
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        setLoading(true);
        if (adminView) {
          const [user, profile] = await Promise.all([
            AdminAPI.getUser(userId),
            AdminAPI.getUserProfile(userId)
          ]);
          setUser(user);
          setProfile(profile);
        } else {
          const userData = await UsersAPI.getCurrentUser();
          const { profile: profileData, ...userData2 } = userData;
          setUser(userData2);
          setProfile(profileData);
        }
      } catch (error) {
        console.error('Error fetching profile:', error);
        setAlert({
          open: true,
          message: 'Failed to load profile data',
          severity: 'error'
        });
      } finally {
        setLoading(false);
      }
    };
    
    fetchUserData();
  }, [adminView, userId]);
  
  // Handle form input changes for user fields
  const handleUserChange = (e) => {
    const { name, value } = e.target;
    setUser(prev => ({ ...prev, [name]: value }));
  };
  
  // Handle form input changes for profile fields
  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfile(prev => ({ ...prev, [name]: value }));
  };
  
  // Handle file uploads
  const handleFileChange = async (e) => {
    const { name, files } = e.target;
    if (files && files[0]) {
      try {
        setSaving(true);
        // Upload document
        const response = await UsersAPI.uploadDocument(name, files[0]);
        
        // Use the returned URL from the response
        setPreviewUrls(prev => ({ 
          ...prev, 
          [name]: response[`${name}_url`] 
        }));
        
        setAlert({
          open: true,
          message: `${name.replace('_', ' ')} uploaded successfully`,
          severity: 'success'
        });
      } catch (error) {
        console.error(`Error uploading ${name}:`, error);
        setAlert({
          open: true,
          message: `Failed to upload ${name.replace('_', ' ')}`,
          severity: 'error'
        });
      } finally {
        setSaving(false);
      }
    }
  };

  // Add a function to get the full URL for images
  const getFullImageUrl = (relativeUrl) => {
    if (!relativeUrl) return '';
    if (relativeUrl.startsWith('http')) return relativeUrl;
    return `${API_URL}${relativeUrl}`;
  };

  // Add a function to prepare documents for display
  const prepareDocuments = () => {
    return [
      { title: 'ID Front', url: profile.id_front_image, verified: profile.id_front_verified },
      { title: 'ID Back', url: profile.id_back_image, verified: profile.id_back_verified },
      { title: 'Passport Photo', url: profile.passport_photo, verified: profile.passport_photo_verified },
      { title: 'Signature', url: profile.signature, verified: profile.signature_verified }
    ].filter(doc => doc.url);
  };
  
  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setSaving(true);
      
      // Update profile data (excluding files which are uploaded separately)
      const profileData = {
        date_of_birth: profile.date_of_birth,
        gender: profile.gender,
        occupation: profile.occupation,
        next_of_kin: profile.next_of_kin,
        next_of_kin_contact: profile.next_of_kin_contact
      };
      
      if (adminView) {
        await AdminAPI.updateUserProfile(userId, profileData);
      } else {
        await UsersAPI.updateProfile(profileData);
      }
      
      setAlert({
        open: true,
        message: 'Profile updated successfully',
        severity: 'success'
      });
    } catch (error) {
      console.error('Error updating profile:', error);
      setAlert({
        open: true,
        message: 'Failed to update profile',
        severity: 'error'
      });
    } finally {
      setSaving(false);
    }
  };
  
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
      </Box>
    );
  }
  
  return (
    <Box sx={{ py: 4, px: 2, maxWidth: 1200, mx: 'auto' }}>
      <Typography variant="h4" sx={{ mb: 4 }}>My Profile</Typography>
      
      <Grid container spacing={3}>
        {/* Personal Information */}
        <Grid item xs={12} md={4}>
          <Card elevation={3}>
            <CardHeader title="Personal Information" />
            <CardContent>
              <Box sx={{ textAlign: 'center', mb: 3 }}>
                {previewUrls.profile_picture ? (
                  <ProfilePicture src={previewUrls.profile_picture} alt="Profile" />
                ) : (
                  <ProfilePicture>
                    <PersonIcon sx={{ fontSize: 50 }} />
                  </ProfilePicture>
                )}
                
                <Button
                  component="label"
                  variant="outlined"
                  startIcon={<CloudUploadIcon />}
                  sx={{ mt: 2 }}
                >
                  Upload Photo
                  <VisuallyHiddenInput 
                    type="file" 
                    name="profile_picture"
                    accept="image/*"
                    onChange={handleFileChange}
                  />
                </Button>
              </Box>
              
              <TextField
                fullWidth
                label="ID Number"
                value={user.id_number}
                margin="normal"
                InputProps={{ 
                  readOnly: !isFieldEditable('id_number')
                }}
              />
              
              <TextField
                fullWidth
                label="Email"
                name="email"
                value={user.email}
                onChange={handleUserChange}
                margin="normal"
                disabled={!isFieldEditable('email')}
              />
              
              <TextField
                fullWidth
                label="Phone Number"
                name="phone_number"
                value={user.phone_number}
                onChange={handleUserChange}
                margin="normal"
                disabled={!isFieldEditable('phone_number')}
              />
            </CardContent>
          </Card>
        </Grid>
        
        {/* Profile Information */}
        <Grid item xs={12} md={8}>
          <form onSubmit={handleSubmit}>
            <Card elevation={3}>
              <CardHeader title="Profile Details" />
              <CardContent>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="First Name"
                      name="first_name"
                      value={user.first_name}
                      onChange={handleUserChange}
                      margin="normal"
                      disabled={!isFieldEditable('first_name')}
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Last Name"
                      name="last_name"
                      value={user.last_name}
                      onChange={handleUserChange}
                      margin="normal"
                      disabled={!isFieldEditable('last_name')}
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Date of Birth"
                      type="date"
                      name="date_of_birth"
                      value={profile.date_of_birth || ''}
                      onChange={handleProfileChange}
                      margin="normal"
                      InputLabelProps={{ shrink: true }}
                      disabled={!isFieldEditable('date_of_birth')}
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      select
                      label="Gender"
                      name="gender"
                      value={profile.gender || ''}
                      onChange={handleProfileChange}
                      margin="normal"
                      disabled={!isFieldEditable('gender')}
                    >
                      <MenuItem value="">Select Gender</MenuItem>
                      <MenuItem value="Male">Male</MenuItem>
                      <MenuItem value="Female">Female</MenuItem>
                      <MenuItem value="Other">Other</MenuItem>
                    </TextField>
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Occupation"
                      name="occupation"
                      value={profile.occupation || ''}
                      onChange={handleProfileChange}
                      margin="normal"
                      disabled={!isFieldEditable('occupation')}
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Address"
                      name="address"
                      value={user.address || ''}
                      onChange={handleUserChange}
                      margin="normal"
                      multiline
                      rows={2}
                      disabled={!isFieldEditable('address')}
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Next of Kin"
                      name="next_of_kin"
                      value={profile.next_of_kin || ''}
                      onChange={handleProfileChange}
                      margin="normal"
                      disabled={!isFieldEditable('next_of_kin')}
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Next of Kin Contact"
                      name="next_of_kin_contact"
                      value={profile.next_of_kin_contact || ''}
                      onChange={handleProfileChange}
                      margin="normal"
                      disabled={!isFieldEditable('next_of_kin_contact')}
                    />
                  </Grid>
                </Grid>
                
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
                  <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    startIcon={<SaveIcon />}
                    disabled={saving}
                  >
                    {saving ? 'Saving...' : 'Save Changes'}
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </form>
          
          {/* Document Uploads */}
          <Card elevation={3} sx={{ mt: 3 }}>
            <CardHeader 
              title="Documents" 
              action={
                <Button
                  variant="outlined"
                  startIcon={<VisibilityIcon />}
                  onClick={() => {
                    setUploadedDocuments(prepareDocuments());
                    setDocumentsDialogOpen(true);
                  }}
                >
                  View Documents
                </Button>
              }
            />
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="subtitle1">ID Front</Typography>
                    <Box 
                      sx={{ 
                        height: 120, 
                        border: '1px dashed grey', 
                        borderRadius: 1, 
                        display: 'flex', 
                        justifyContent: 'center',
                        alignItems: 'center',
                        mb: 1,
                        overflow: 'hidden',
                        backgroundSize: 'cover',
                        backgroundPosition: 'center',
                        backgroundImage: previewUrls.id_front_image ? `url(${previewUrls.id_front_image})` : 'none',
                        ...documentPreviewStyles
                      }}
                    >
                      {!previewUrls.id_front_image && <CloudUploadIcon color="action" />}
                    </Box>
                    <Button
                      component="label"
                      variant="outlined"
                      size="small"
                      fullWidth
                    >
                      Upload
                      <VisuallyHiddenInput 
                        type="file" 
                        name="id_front_image"
                        accept="image/*"
                        onChange={handleFileChange}
                      />
                    </Button>
                  </Box>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="subtitle1">ID Back</Typography>
                    <Box 
                      sx={{ 
                        height: 120, 
                        border: '1px dashed grey', 
                        borderRadius: 1, 
                        display: 'flex', 
                        justifyContent: 'center',
                        alignItems: 'center',
                        mb: 1,
                        overflow: 'hidden',
                        backgroundSize: 'cover',
                        backgroundPosition: 'center',
                        backgroundImage: previewUrls.id_back_image ? `url(${previewUrls.id_back_image})` : 'none',
                        ...documentPreviewStyles
                      }}
                    >
                      {!previewUrls.id_back_image && <CloudUploadIcon color="action" />}
                    </Box>
                    <Button
                      component="label"
                      variant="outlined"
                      size="small"
                      fullWidth
                    >
                      Upload
                      <VisuallyHiddenInput 
                        type="file" 
                        name="id_back_image"
                        accept="image/*"
                        onChange={handleFileChange}
                      />
                    </Button>
                  </Box>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="subtitle1">Passport Photo</Typography>
                    <Box 
                      sx={{ 
                        height: 120, 
                        border: '1px dashed grey', 
                        borderRadius: 1, 
                        display: 'flex', 
                        justifyContent: 'center',
                        alignItems: 'center',
                        mb: 1,
                        overflow: 'hidden',
                        backgroundSize: 'cover',
                        backgroundPosition: 'center',
                        backgroundImage: previewUrls.passport_photo ? `url(${previewUrls.passport_photo})` : 'none',
                        ...documentPreviewStyles
                      }}
                    >
                      {!previewUrls.passport_photo && <CloudUploadIcon color="action" />}
                    </Box>
                    <Button
                      component="label"
                      variant="outlined"
                      size="small"
                      fullWidth
                    >
                      Upload
                      <VisuallyHiddenInput 
                        type="file" 
                        name="passport_photo"
                        accept="image/*"
                        onChange={handleFileChange}
                      />
                    </Button>
                  </Box>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="subtitle1">Signature</Typography>
                    <Box 
                      sx={{ 
                        height: 120, 
                        border: '1px dashed grey', 
                        borderRadius: 1, 
                        display: 'flex', 
                        justifyContent: 'center',
                        alignItems: 'center',
                        mb: 1,
                        overflow: 'hidden',
                        backgroundSize: 'cover',
                        backgroundPosition: 'center',
                        backgroundImage: previewUrls.signature ? `url(${previewUrls.signature})` : 'none',
                        ...documentPreviewStyles
                      }}
                    >
                      {!previewUrls.signature && <CloudUploadIcon color="action" />}
                    </Box>
                    <Button
                      component="label"
                      variant="outlined"
                      size="small"
                      fullWidth
                    >
                      Upload
                      <VisuallyHiddenInput 
                        type="file" 
                        name="signature"
                        accept="image/*"
                        onChange={handleFileChange}
                      />
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Alert/Notification */}
      <Snackbar 
        open={alert.open} 
        autoHideDuration={6000} 
        onClose={() => setAlert({ ...alert, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setAlert({ ...alert, open: false })} 
          severity={alert.severity}
          variant="filled"
        >
          {alert.message}
        </Alert>
      </Snackbar>

      {/* Documents Dialog */}
      <Dialog
        open={documentsDialogOpen}
        onClose={() => setDocumentsDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Uploaded Documents
          <Typography variant="subtitle2" color="text.secondary">
            {user.first_name} {user.last_name}
          </Typography>
        </DialogTitle>
        <DialogContent>
          {uploadedDocuments.length === 0 ? (
            <Box sx={{ py: 4, textAlign: 'center' }}>
              <Typography color="text.secondary">
                No documents uploaded yet
              </Typography>
            </Box>
          ) : (
            <ImageList cols={2} gap={16}>
              {uploadedDocuments.map((doc, index) => (
                <ImageListItem key={index}>
                  <img
                    src={getFullImageUrl(doc.url)}
                    alt={doc.title}
                    loading="lazy"
                    style={{ 
                      height: 200, 
                      objectFit: 'contain',
                      backgroundColor: 'rgba(0, 0, 0, 0.03)'
                    }}
                  />
                  <ImageListItemBar
                    title={doc.title}
                    subtitle={doc.verified ? 'Verified' : 'Pending Verification'}
                    sx={{
                      '& .MuiImageListItemBar-title': { color: 'white' },
                      '& .MuiImageListItemBar-subtitle': { 
                        color: doc.verified ? '#4caf50' : '#ff9800'
                      }
                    }}
                  />
                </ImageListItem>
              ))}
            </ImageList>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDocumentsDialogOpen(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Profile;