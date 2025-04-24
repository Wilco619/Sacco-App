import React, { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Grid,
    CircularProgress,
    Alert,
    Card,
    CardHeader,
    CardContent,
    CardActions,
    Button,
    Divider,
    List,
    ListItem,
    ListItemText,
    ListItemSecondaryAction,
    IconButton,
    Badge,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Collapse,
    DialogContentText,
    TextField
} from '@mui/material';
import {
    VerifiedUser as VerifiedIcon,
    PendingActions as PendingIcon,
    ExpandMore as ExpandMoreIcon,
    ExpandLess as ExpandLessIcon
} from '@mui/icons-material';
import { AdminAPI } from '../../api/api';
import { useParams } from 'react-router-dom';

const DocumentVerification = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [unverifiedUsers, setUnverifiedUsers] = useState([]);
    const [selectedUser, setSelectedUser] = useState(null);
    const [verifying, setVerifying] = useState(false);
    const [expandedUser, setExpandedUser] = useState(null);
    const [selectedImage, setSelectedImage] = useState(null);
    const [rejectionDialog, setRejectionDialog] = useState(false);
    const [rejectionNotes, setRejectionNotes] = useState('');
    const [documentToReject, setDocumentToReject] = useState(null);
    const [highlightedUser, setHighlightedUser] = useState(null);
    const [verified, setVerified] = useState(false);
    const [successMessage, setSuccessMessage] = useState(null);
    const { userId } = useParams();

    useEffect(() => {
        fetchUnverifiedUsers();
        if (userId) {
            checkAndHighlightUser(userId);
        }
    }, [userId]);

    const fetchUnverifiedUsers = async () => {
        try {
            setLoading(true);
            const users = await AdminAPI.getUnverifiedUsers();
            setUnverifiedUsers(users);
            setError(null);
        } catch (err) {
            setError('Failed to fetch unverified users');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const checkAndHighlightUser = async (idNumber) => {
        try {
            const documents = await AdminAPI.getUserDocuments(idNumber);
            const isVerified = Object.values(documents).every(doc => 
                doc && doc.url && doc.verified
            );
            
            if (isVerified) {
                const userData = await AdminAPI.getUser(idNumber);
                setHighlightedUser(userData);
                setVerified(true);
            } else {
                handleUserClick(idNumber);
                setExpandedUser(idNumber);
                const userIndex = unverifiedUsers.findIndex(u => u.id_number === idNumber);
                if (userIndex !== -1) {
                    document.getElementById(`user-card-${idNumber}`)?.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                }
            }
        } catch (err) {
            console.error('Error checking user documents:', err);
            setError('Failed to check user documents');
        }
    };

    const handleVerify = async (userId, documentType, status, notes = '') => {
        try {
            setVerifying(true);
            setError(null);
            
            await AdminAPI.verifyDocument(userId, documentType, status, notes);
            
            // Show success message
            setSuccessMessage(
                status === 'approve' 
                    ? `Documents ${documentType === 'all' ? 'all' : documentType} verified successfully` 
                    : 'Documents rejected successfully'
            );
            
            // Refresh documents
            await fetchUnverifiedUsers();
            
            // If viewing specific user, refresh their documents
            if (selectedUser?.id === userId) {
                const updatedDocs = await AdminAPI.getUserDocuments(userId);
                setSelectedUser(prev => ({
                    ...prev,
                    documents: updatedDocs
                }));
            }
        } catch (err) {
            console.error('Verification failed:', err);
            setError(`Failed to ${status} documents: ${err.message || 'Unknown error'}`);
        } finally {
            setVerifying(false);
            // Clear success message after 5 seconds
            setTimeout(() => setSuccessMessage(null), 5000);
        }
    };

    const handleVerifyClick = (userId, documentType, status) => {
        if (status === 'reject') {
            setDocumentToReject({ userId, documentType });
            setRejectionDialog(true);
        } else {
            handleVerify(userId, documentType, status);
        }
    };

    const handleReject = async () => {
        if (!documentToReject) return;

        try {
            await handleVerify(
                documentToReject.userId,
                documentToReject.documentType,
                'reject',
                rejectionNotes
            );
            setRejectionDialog(false);
            setRejectionNotes('');
            setDocumentToReject(null);
        } catch (err) {
            console.error('Rejection failed:', err);
            setError('Failed to reject document');
        }
    };

    const handleUserClick = async (idNumber) => {
        if (expandedUser === idNumber) {
            setExpandedUser(null);
            return;
        }

        try {
            const documents = await AdminAPI.getUserDocuments(idNumber);
            setSelectedUser({ id: idNumber, documents });
            setExpandedUser(idNumber);
        } catch (err) {
            console.error('Failed to fetch user documents:', err);
            setError('Failed to fetch user documents');
        }
    };

    const renderDocuments = (documents) => {
        if (!documents) return null;

        return Object.entries(documents)
            .map(([type, doc]) => {
                const hasDocument = doc && doc.url;
                
                return (
                    <Grid item xs={12} sm={6} md={4} key={type}>
                        <Card>
                            {hasDocument ? (
                                <img
                                    src={doc.url}
                                    alt={type.replace(/_/g, ' ')}
                                    style={{
                                        width: '100%',
                                        height: 200,
                                        objectFit: 'contain',
                                        cursor: 'pointer'
                                    }}
                                    onClick={() => setSelectedImage(doc.url)}
                                />
                            ) : (
                                <Box
                                    sx={{
                                        height: 200,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        bgcolor: 'grey.100'
                                    }}
                                >
                                    <Typography color="textSecondary">
                                        No document uploaded
                                    </Typography>
                                </Box>
                            )}
                            <CardContent>
                                <Typography variant="body2">
                                    {type.split('_').map(word => 
                                        word.charAt(0).toUpperCase() + 
                                        word.slice(1)
                                    ).join(' ')}
                                </Typography>
                                <Typography variant="caption" color="textSecondary">
                                    Status: {!hasDocument ? 'Not Uploaded' : (doc.verified ? 'Verified' : 'Pending')}
                                </Typography>
                                <CardActions sx={{ justifyContent: 'space-between', mt: 1 }}>
                                    <Button
                                        size="small"
                                        variant="contained"
                                        color={doc?.verified ? "success" : "primary"}
                                        disabled={verifying || !hasDocument}
                                        onClick={() => handleVerifyClick(
                                            selectedUser.id,
                                            type,
                                            doc?.verified ? 'reject' : 'approve'
                                        )}
                                    >
                                        {doc?.verified ? 'Verified' : 'Verify'}
                                    </Button>
                                    {!doc?.verified && (
                                        <Button
                                            size="small"
                                            variant="outlined"
                                            color="error"
                                            disabled={verifying || !hasDocument}
                                            onClick={() => handleVerifyClick(
                                                selectedUser.id,
                                                type,
                                                'reject'
                                            )}
                                        >
                                            Reject
                                        </Button>
                                    )}
                                </CardActions>
                            </CardContent>
                        </Card>
                    </Grid>
                );
            });
    };

    if (loading) return (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
        </Box>
    );

    return (
        <Box sx={{ p: 3 }}>
            {successMessage && (
                <Alert 
                    severity="success" 
                    sx={{ mb: 3 }}
                    onClose={() => setSuccessMessage(null)}
                >
                    {successMessage}
                </Alert>
            )}

            {highlightedUser && verified && (
                <Alert 
                    severity="success" 
                    sx={{ mb: 3 }}
                >
                    All documents for {highlightedUser.first_name} {highlightedUser.last_name} 
                    (ID: {highlightedUser.id_number}) are verified
                </Alert>
            )}

            <Typography variant="h5" gutterBottom>
                Document Verification
                <Badge 
                    badgeContent={unverifiedUsers.length} 
                    color="warning" 
                    sx={{ ml: 2 }}
                >
                    <PendingIcon />
                </Badge>
            </Typography>

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

            <List>
                {unverifiedUsers.map((user) => (
                    <Card 
                        key={user.id_number} 
                        sx={{ 
                            mb: 2,
                            border: userId === user.id_number ? '2px solid #4caf50' : 'none',
                            boxShadow: userId === user.id_number ? '0 0 10px rgba(76, 175, 80, 0.3)' : undefined
                        }}
                        id={`user-card-${user.id_number}`}
                    >
                        <CardHeader
                            title={`${user.first_name} ${user.last_name}`}
                            subheader={`ID Number: ${user.id_number}`}
                            action={
                                <IconButton
                                    onClick={() => handleUserClick(user.id_number)}
                                >
                                    {expandedUser === user.id_number ? 
                                        <ExpandLessIcon /> : 
                                        <ExpandMoreIcon />
                                    }
                                </IconButton>
                            }
                        />
                        <Collapse in={expandedUser === user.id_number}>
                            <CardContent>
                                <Grid container spacing={2}>
                                    {selectedUser?.documents ? 
                                        renderDocuments(selectedUser.documents) :
                                        <Box sx={{ p: 2, width: '100%', textAlign: 'center' }}>
                                            <Typography color="textSecondary">
                                                No documents available
                                            </Typography>
                                        </Box>
                                    }
                                </Grid>
                            </CardContent>
                            <CardActions sx={{ justifyContent: 'flex-end', p: 2 }}>
                                <Button
                                    variant="contained"
                                    color="success"
                                    startIcon={<VerifiedIcon />}
                                    disabled={
                                        verifying || 
                                        !selectedUser?.documents ||
                                        !Object.values(selectedUser?.documents || {}).some(doc => doc && doc.url)
                                    }
                                    onClick={() => handleVerify(user.id_number, null, 'approve')}
                                >
                                    Verify All Documents
                                </Button>
                                {verifying && <CircularProgress size={24} sx={{ ml: 2 }} />}
                            </CardActions>
                        </Collapse>
                    </Card>
                ))}
            </List>

            <Dialog
                open={!!selectedImage}
                onClose={() => setSelectedImage(null)}
                maxWidth="lg"
                fullWidth
            >
                <DialogTitle>Document Preview</DialogTitle>
                <DialogContent>
                    <img
                        src={selectedImage}
                        alt="Document Preview"
                        style={{ width: '100%', height: 'auto' }}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setSelectedImage(null)}>Close</Button>
                </DialogActions>
            </Dialog>

            <Dialog
                open={rejectionDialog}
                onClose={() => setRejectionDialog(false)}
            >
                <DialogTitle>Reject Document</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        Please provide a reason for rejection. This will be sent to the user.
                    </DialogContentText>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Rejection Notes"
                        fullWidth
                        multiline
                        rows={4}
                        value={rejectionNotes}
                        onChange={(e) => setRejectionNotes(e.target.value)}
                    />
                </DialogContent>
                <DialogActions>
                    <Button 
                        onClick={() => setRejectionDialog(false)}
                        color="inherit"
                    >
                        Cancel
                    </Button>
                    <Button 
                        onClick={handleReject}
                        color="error"
                        disabled={!rejectionNotes.trim()}
                    >
                        Reject
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default DocumentVerification;