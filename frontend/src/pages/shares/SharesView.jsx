import React, { useState } from 'react';
import {
    Paper,
    Typography,
    Button,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Box,
    CircularProgress,
    Alert,
    Chip
} from '@mui/material';
import { useShares } from '../../contexts/SharesContext';
import SharePurchaseDialog from './SharePurchaseDialog';

const SharesView = () => {
    const [openPurchaseDialog, setOpenPurchaseDialog] = useState(false);
    const { sharesData, loading, refreshShares, error } = useShares();

    const handlePurchaseComplete = async (success) => {
        setOpenPurchaseDialog(false);
        if (success) {
            await refreshShares();
        }
    };

    const formatCurrency = (amount) => {
        return typeof amount === 'number' 
            ? `KSH ${amount.toLocaleString()}`
            : 'KSH 0';
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Alert 
                severity="error" 
                sx={{ mt: 2 }}
                action={
                    <Button color="inherit" size="small" onClick={refreshShares}>
                        Retry
                    </Button>
                }
            >
                {error}
            </Alert>
        );
    }

    const sharesSummary = [
        { label: 'Certificate Number', value: sharesData?.certificate_number || 'N/A' },
        { label: 'Number of Shares', value: sharesData?.number_of_shares || 0 },
        { label: 'Share Value', value: formatCurrency(sharesData?.value_per_share) },
        { label: 'Total Value', value: formatCurrency(sharesData?.total_value) },
        { label: 'Monthly Contribution', value: formatCurrency(sharesData?.monthly_contribution) },
        { 
            label: 'Date Purchased', 
            value: sharesData?.date_purchased 
                ? new Date(sharesData.date_purchased).toLocaleDateString() 
                : 'N/A' 
        },
        { 
            label: 'Last Payment', 
            value: sharesData?.last_payment_date 
                ? new Date(sharesData.last_payment_date).toLocaleDateString() 
                : 'N/A' 
        }
    ];

    return (
        <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h6">My Shares</Typography>
                <Button 
                    variant="contained" 
                    onClick={() => setOpenPurchaseDialog(true)}
                >
                    Purchase Shares
                </Button>
            </Box>

            {sharesData ? (
                <>
                    <Box sx={{ mb: 3 }}>
                        {sharesSummary.map((item, index) => (
                            <Typography 
                                key={index} 
                                variant="subtitle1" 
                                gutterBottom
                                sx={{ 
                                    display: 'flex', 
                                    justifyContent: 'space-between',
                                    borderBottom: index !== sharesSummary.length - 1 ? '1px solid #eee' : 'none',
                                    py: 1
                                }}
                            >
                                <span>{item.label}:</span>
                                <strong>{item.value}</strong>
                            </Typography>
                        ))}
                    </Box>

                    {sharesData.transactions?.length > 0 ? (
                        <TableContainer>
                            <Table>
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Date</TableCell>
                                        <TableCell>Certificate Number</TableCell>
                                        <TableCell align="right">Amount</TableCell>
                                        <TableCell>Status</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {sharesData.transactions.map((transaction, index) => (
                                        <TableRow 
                                            key={`${transaction.transaction_id}-${index}`}
                                            sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                                        >
                                            <TableCell>
                                                {new Date(sharesData?.last_payment_date).toLocaleDateString()}
                                            </TableCell>
                                            <TableCell>{sharesData?.certificate_number}</TableCell>
                                            <TableCell align="right">
                                                {formatCurrency(transaction.amount)}
                                            </TableCell>
                                            <TableCell>
                                                <Chip 
                                                    label={transaction.status}
                                                    color={transaction.status === 'COMPLETED' ? 'success' : 'default'}
                                                    size="small"
                                                />
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    ) : (
                        <Alert severity="info">
                            No share transactions found. Start by purchasing your first shares.
                        </Alert>
                    )}
                </>
            ) : (
                <Alert 
                    severity="info"
                    action={
                        <Button color="inherit" size="small" onClick={refreshShares}>
                            Refresh
                        </Button>
                    }
                >
                    Share information not available. Please try refreshing the page.
                </Alert>
            )}

            <SharePurchaseDialog 
                open={openPurchaseDialog}
                onClose={handlePurchaseComplete}
            />
        </Paper>
    );
};

export default SharesView;