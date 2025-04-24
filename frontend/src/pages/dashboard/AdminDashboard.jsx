import React, { useState, useEffect } from 'react';
import {
    Typography,
    Grid,
    Card,
    CardContent,
    Box,
    CircularProgress,
    Alert,
    List,
    ListItem,
    ListItemText,
    ListItemAvatar,
    Avatar,
    Divider,
    Paper
} from '@mui/material';
import {
    People as PeopleIcon,
    VerifiedUser as VerifiedIcon,
    AccountBalance as AccountIcon,
    Warning as WarningIcon
} from '@mui/icons-material';
import { AdminAPI } from '../../api/api';

const AdminDashboard = () => {
    const [stats, setStats] = useState({
        totalMembers: 0,
        pendingVerifications: 0,
        activeLoans: 0,
        recentMembers: [],
        verificationStats: {
            pending: 0,
            verified: 0,
            rejected: 0
        }
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchDashboardStats();
    }, []);

    const fetchDashboardStats = async () => {
        try {
            setLoading(true);
            const data = await AdminAPI.getDashboardStats();
            setStats({
                totalMembers: data.total_members,
                pendingVerifications: data.pending_verifications,
                activeLoans: data.active_loans,
                recentMembers: data.recent_members,
                verificationStats: data.verification_stats
            });
            setError(null);
        } catch (err) {
            console.error('Failed to fetch dashboard stats:', err);
            setError('Failed to load dashboard statistics');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
            )}

            <Typography variant="h4" gutterBottom>
                Admin Dashboard
            </Typography>

            <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <PeopleIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                                <Box>
                                    <Typography variant="h6">Total Members</Typography>
                                    <Typography variant="h3">{stats.totalMembers}</Typography>
                                </Box>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <WarningIcon sx={{ fontSize: 40, color: 'warning.main', mr: 2 }} />
                                <Box>
                                    <Typography variant="h6">Pending Verifications</Typography>
                                    <Typography variant="h3">{stats.pendingVerifications}</Typography>
                                </Box>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <AccountIcon sx={{ fontSize: 40, color: 'success.main', mr: 2 }} />
                                <Box>
                                    <Typography variant="h6">Active Loans</Typography>
                                    <Typography variant="h3">{stats.activeLoans}</Typography>
                                </Box>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Recent Members
                            </Typography>
                            <List>
                                {stats.recentMembers.map((member, index) => (
                                    <React.Fragment key={member.id_number}>
                                        <ListItem>
                                            <ListItemAvatar>
                                                <Avatar>{member.first_name[0]}</Avatar>
                                            </ListItemAvatar>
                                            <ListItemText
                                                primary={`${member.first_name} ${member.last_name}`}
                                                secondary={`ID: ${member.id_number} • Joined: ${new Date(member.date_joined).toLocaleDateString()}`}
                                            />
                                        </ListItem>
                                        {index < stats.recentMembers.length - 1 && <Divider />}
                                    </React.Fragment>
                                ))}
                            </List>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Document Verification Status
                            </Typography>
                            <Box sx={{ mt: 2 }}>
                                <Grid container spacing={2}>
                                    <Grid item xs={4}>
                                        <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light' }}>
                                            <Typography variant="h4">{stats.verificationStats.pending}</Typography>
                                            <Typography>Pending</Typography>
                                        </Paper>
                                    </Grid>
                                    <Grid item xs={4}>
                                        <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light' }}>
                                            <Typography variant="h4">{stats.verificationStats.verified}</Typography>
                                            <Typography>Verified</Typography>
                                        </Paper>
                                    </Grid>
                                    <Grid item xs={4}>
                                        <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'error.light' }}>
                                            <Typography variant="h4">{stats.verificationStats.rejected}</Typography>
                                            <Typography>Rejected</Typography>
                                        </Paper>
                                    </Grid>
                                </Grid>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
};

export default AdminDashboard;