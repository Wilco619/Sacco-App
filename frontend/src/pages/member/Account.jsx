import React from 'react';
import { 
    Box, 
    Paper, 
    Typography, 
    Grid, 
    Button, 
    Card, 
    CardContent,
    CardActions,
    Divider,
    List,
    ListItem,
    ListItemText,
    ListItemIcon
} from '@mui/material';
import { 
    AccountBalance, 
    MonetizationOn, 
    Handshake,
    Favorite, // Changed from Volunteer to Favorite
    ArrowForward
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { formatCurrency } from '../../utils/format';
import { useShares } from '../../contexts/SharesContext';
import { useWelfare } from '../../contexts/WelfareContext';

const Account = () => {
    const navigate = useNavigate();
    const { sharesData } = useShares();
    const { welfareData } = useWelfare();

    const accountSummary = [
        {
            title: 'Shares',
            icon: <MonetizationOn color="primary" />,
            value: sharesData?.total_value || 0,
            action: () => navigate('/shares'),
            description: 'View and manage your shares'
        },
        {
            title: 'Welfare',
            icon: <Handshake color="secondary" />,
            value: 300,
            action: () => navigate('/welfare'),
            description: 'Monthly welfare contribution'
        },
        {
            title: 'Registration',
            icon: <AccountBalance />,
            value: 'Completed',
            description: 'One-time registration fee'
        }
    ];

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" sx={{ mb: 4 }}>
                My Account
            </Typography>

            <Grid container spacing={3}>
                {/* Account Summary Cards */}
                {accountSummary.map((item, index) => (
                    <Grid item xs={12} md={4} key={index}>
                        <Card 
                            sx={{ 
                                height: '100%',
                                display: 'flex',
                                flexDirection: 'column',
                                '&:hover': {
                                    boxShadow: 3,
                                    cursor: item.action ? 'pointer' : 'default'
                                }
                            }}
                            onClick={item.action}
                        >
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                    {item.icon}
                                    <Typography variant="h6" sx={{ ml: 1 }}>
                                        {item.title}
                                    </Typography>
                                </Box>
                                <Typography variant="h5" color="primary">
                                    {typeof item.value === 'number' ? 
                                        formatCurrency(item.value) : item.value}
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                    {item.description}
                                </Typography>
                            </CardContent>
                            {item.action && (
                                <CardActions>
                                    <Button 
                                        size="small" 
                                        endIcon={<ArrowForward />}
                                        onClick={item.action}
                                    >
                                        View Details
                                    </Button>
                                </CardActions>
                            )}
                        </Card>
                    </Grid>
                ))}

                {/* Quick Actions */}
                <Grid item xs={12}>
                    <Paper sx={{ p: 3, mt: 3 }}>
                        <Typography variant="h6" sx={{ mb: 2 }}>
                            Quick Actions
                        </Typography>
                        <Grid container spacing={2}>
                            <Grid item xs={12} md={6}>
                                <Button
                                    variant="contained"
                                    fullWidth
                                    startIcon={<MonetizationOn />}
                                    onClick={() => navigate('/shares')}
                                >
                                    Purchase Shares
                                </Button>
                            </Grid>
                            <Grid item xs={12} md={6}>
                                <Button
                                    variant="contained"
                                    color="secondary"
                                    fullWidth
                                    startIcon={<Favorite />} 
                                    onClick={() => navigate('/welfare')}
                                >
                                    Pay Welfare Contribution
                                </Button>
                            </Grid>
                        </Grid>
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};

export default Account;