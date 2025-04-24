import React, { useState, useEffect } from 'react';
import {
    Box,
    Paper,
    Typography,
    Button,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Alert,
    CircularProgress,
    Chip
} from '@mui/material';
import { useWelfare } from '../../contexts/WelfareContext';
import WelfarePaymentDialog from './WelfarePaymentDialog';
import { formatCurrency } from '../../utils/format';

const WelfareView = () => {
    const [openPaymentDialog, setOpenPaymentDialog] = useState(false);
    const { welfareData, loading, error, refreshWelfare } = useWelfare();

    const handlePaymentComplete = async (success) => {
        setOpenPaymentDialog(false);
        if (success) {
            await refreshWelfare();
        }
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h6">Welfare Contributions</Typography>
                <Button 
                    variant="contained" 
                    onClick={() => setOpenPaymentDialog(true)}
                    disabled={!welfareData?.can_contribute}
                >
                    Make Contribution
                </Button>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}

            {welfareData?.contributions?.length > 0 ? (
                <TableContainer>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Month</TableCell>
                                <TableCell>Payment Date</TableCell>
                                <TableCell align="right">Amount</TableCell>
                                <TableCell>Status</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {welfareData.contributions.map((contribution) => (
                                <TableRow key={contribution.id}>
                                    <TableCell>{contribution.month}</TableCell>
                                    <TableCell>
                                        {new Date(contribution.payment_date).toLocaleDateString()}
                                    </TableCell>
                                    <TableCell align="right">
                                        {formatCurrency(contribution.amount)}
                                    </TableCell>
                                    <TableCell>
                                        <Chip 
                                            label={contribution.status}
                                            color={contribution.status === 'COMPLETED' ? 'success' : 'default'}
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
                    No welfare contributions found. Start by making your first contribution.
                </Alert>
            )}

            <WelfarePaymentDialog 
                open={openPaymentDialog}
                onClose={handlePaymentComplete}
            />
        </Paper>
    );
};

export default WelfareView;