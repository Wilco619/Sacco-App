import { useState } from 'react';
import {
    Typography,
    Grid,
    Card,
    CardContent,
} from '@mui/material';

const MemberDashboard = () => {
    const [accountInfo, setAccountInfo] = useState({
        balance: 0,
        loanBalance: 0,
        contributions: 0,
    });

    return (
        <>
            <Typography variant="h4" gutterBottom>
                Member Dashboard
            </Typography>
            <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6">Account Balance</Typography>
                            <Typography variant="h3">
                                Ksh. {accountInfo.balance.toLocaleString()}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} md={4}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6">Loan Balance</Typography>
                            <Typography variant="h3">
                                Ksh. {accountInfo.loanBalance.toLocaleString()}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} md={4}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6">Total Contributions</Typography>
                            <Typography variant="h3">
                                Ksh. {accountInfo.contributions.toLocaleString()}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                </Grid>
        </>
    );
};

export default MemberDashboard;