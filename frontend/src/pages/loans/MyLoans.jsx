import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  CircularProgress,
  AlertTitle,
  Alert,
  Chip
} from '@mui/material';
import { LoansAPI } from '../../api/api';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

const MyLoans = () => {
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openApplyDialog, setOpenApplyDialog] = useState(false);
  const [formData, setFormData] = useState({
    principal_amount: '',
    purpose: '',
    repayment_period: 'MONTHLY',
    term_months: 12,
    loan_type: 'PERSONAL',
    interest_rate: 12.0
  });
  const [availableAmount, setAvailableAmount] = useState(null);
  const [eligibility, setEligibility] = useState(null);
  const navigate = useNavigate();

  const fetchLoans = async () => {
    try {
      setLoading(true);
      const data = await LoansAPI.getMyLoans();
      setLoans(data);
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableAmount = async () => {
    try {
      const response = await LoansAPI.getAvailableAmount();
      if (response.success) {
        setAvailableAmount(response.data);
      }
    } catch (error) {
      toast.error('Failed to fetch available loan amount');
    }
  };

  const fetchEligibility = async () => {
    try {
      const response = await LoansAPI.getLoanEligibility();
      if (response.success) {
        setEligibility(response.data);
      }
    } catch (error) {
      toast.error('Failed to fetch loan eligibility status');
    }
  };

  useEffect(() => {
    fetchLoans();
    fetchAvailableAmount();
    fetchEligibility();
  }, []);

  const handleApplyLoan = async () => {
    try {
      // Validate required fields
      if (!formData.principal_amount || !formData.purpose) {
        toast.error('Please fill in all required fields');
        return;
      }

      // Format data for API
      const loanData = {
        ...formData,
        principal_amount: parseFloat(formData.principal_amount),
        interest_rate: parseFloat(formData.interest_rate)
      };

      await LoansAPI.applyForLoan(loanData);
      toast.success('Loan application submitted successfully');
      setOpenApplyDialog(false);
      // Reset form
      setFormData({
        principal_amount: '',
        purpose: '',
        repayment_period: 'MONTHLY',
        term_months: 12,
        loan_type: 'PERSONAL',
        interest_rate: 12.0
      });
      fetchLoans();
    } catch (error) {
      toast.error(error.message || 'Failed to submit loan application');
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5">My Loans</Typography>
        <Button
          variant="contained"
          onClick={() => setOpenApplyDialog(true)}
        >
          Apply for Loan
        </Button>
      </Box>

      {loading ? (
        <CircularProgress />
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Amount</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Repayment Period</TableCell>
                <TableCell>Due Date</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loans.map((loan) => (
                <TableRow key={loan.id}>
                  <TableCell>{loan.principal_amount}</TableCell>
                  <TableCell>{loan.status}</TableCell>
                  <TableCell>{loan.repayment_period}</TableCell>
                  <TableCell>{loan.due_date}</TableCell>
                  <TableCell>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => {/* View details */}}
                    >
                      View Details
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Loan Application Dialog */}
      <Dialog open={openApplyDialog} onClose={() => setOpenApplyDialog(false)}>
        <DialogTitle>Apply for Loan</DialogTitle>
        <DialogContent>
          {eligibility && (
            <Box sx={{ mb: 3 }}>
              <Alert 
                severity={eligibility.can_apply ? "info" : "warning"}
                sx={{ mb: 2 }}
              >
                <AlertTitle>Loan Eligibility Status</AlertTitle>
                <Typography variant="body2">
                  Welfare Status: {eligibility.welfare_paid ? (
                    <Chip 
                      size="small" 
                      color="success" 
                      label="Paid for current month" 
                    />
                  ) : (
                    <Chip 
                      size="small" 
                      color="error" 
                      label="Not paid for current month" 
                    />
                  )}
                </Typography>
                <Typography variant="body2">
                  Available Amount: KES {eligibility.available_amount.toLocaleString()}
                </Typography>
                {eligibility.has_active_loan && (
                  <Typography variant="body2" color="error">
                    You have an active loan. New applications are not allowed.
                  </Typography>
                )}
                {!eligibility.welfare_paid && (
                  <Button 
                    variant="contained" 
                    size="small"
                    sx={{ mt: 1 }}
                    onClick={() => {
                      setOpenApplyDialog(false);
                      navigate('/welfare');
                    }}
                  >
                    Pay Welfare Contribution
                  </Button>
                )}
              </Alert>
            </Box>
          )}
          {availableAmount && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Available loan amount: KES {availableAmount.available_amount.toLocaleString()}
              <br />
              Based on shares value: KES {availableAmount.shares_value.toLocaleString()}
            </Alert>
          )}
          <Box component="form" sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Amount"
              type="number"
              value={formData.principal_amount}
              onChange={(e) => setFormData({
                ...formData,
                principal_amount: e.target.value
              })}
              margin="normal"
            />
            <TextField
              fullWidth
              select
              label="Repayment Period"
              value={formData.repayment_period}
              onChange={(e) => setFormData({
                ...formData,
                repayment_period: e.target.value
              })}
              margin="normal"
            >
              <MenuItem value="MONTHLY">Monthly</MenuItem>
              <MenuItem value="TWO_MONTHS">Two Months</MenuItem>
              <MenuItem value="THREE_MONTHS">Three Months</MenuItem>
              <MenuItem value="FOUR_MONTHS">Four Months</MenuItem>
            </TextField>
            <TextField
              fullWidth
              label="Purpose"
              multiline
              rows={3}
              value={formData.purpose}
              onChange={(e) => setFormData({
                ...formData,
                purpose: e.target.value
              })}
              margin="normal"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenApplyDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleApplyLoan} 
            variant="contained"
            disabled={!eligibility?.can_apply}
          >
            Apply
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MyLoans;