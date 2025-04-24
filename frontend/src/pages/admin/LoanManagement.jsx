import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Chip,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Check as CheckIcon,
  Close as CloseIcon,
  Visibility as VisibilityIcon
} from '@mui/icons-material';
import { LoansAPI } from '../../api/api';
import { toast } from 'react-hot-toast';

const LoanManagement = () => {
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLoan, setSelectedLoan] = useState(null);
  const [rejectReason, setRejectReason] = useState('');
  const [openRejectDialog, setOpenRejectDialog] = useState(false);
  const [openDetailsDialog, setOpenDetailsDialog] = useState(false);

  const fetchLoans = async () => {
    try {
      setLoading(true);
      const data = await LoansAPI.getAllLoans();
      setLoans(data);
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLoans();
  }, []);

  const handleApproveLoan = async (loanId) => {
    try {
      await LoansAPI.approveLoan(loanId);
      toast.success('Loan approved successfully');
      fetchLoans();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleRejectLoan = async () => {
    try {
      await LoansAPI.rejectLoan(selectedLoan.id, rejectReason);
      toast.success('Loan rejected successfully');
      setOpenRejectDialog(false);
      fetchLoans();
    } catch (error) {
      toast.error(error.message);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" sx={{ mb: 3 }}>Loan Management</Typography>

      {loading ? (
        <CircularProgress />
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Member</TableCell>
                <TableCell>Amount</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Repayment Period</TableCell>
                <TableCell>Applied Date</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loans.map((loan) => (
                <TableRow key={loan.id}>
                  <TableCell>{loan.member_name}</TableCell>
                  <TableCell>{loan.principal_amount}</TableCell>
                  <TableCell>
                    <Chip
                      label={loan.status}
                      color={
                        loan.status === 'APPROVED' ? 'success' :
                        loan.status === 'REJECTED' ? 'error' :
                        'default'
                      }
                    />
                  </TableCell>
                  <TableCell>{loan.repayment_period}</TableCell>
                  <TableCell>{new Date(loan.created_at).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <Tooltip title="View Details">
                      <IconButton
                        onClick={() => {
                          setSelectedLoan(loan);
                          setOpenDetailsDialog(true);
                        }}
                      >
                        <VisibilityIcon />
                      </IconButton>
                    </Tooltip>
                    {loan.status === 'PENDING' && (
                      <>
                        <Tooltip title="Approve">
                          <IconButton
                            color="success"
                            onClick={() => handleApproveLoan(loan.id)}
                          >
                            <CheckIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Reject">
                          <IconButton
                            color="error"
                            onClick={() => {
                              setSelectedLoan(loan);
                              setOpenRejectDialog(true);
                            }}
                          >
                            <CloseIcon />
                          </IconButton>
                        </Tooltip>
                      </>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Reject Dialog */}
      <Dialog open={openRejectDialog} onClose={() => setOpenRejectDialog(false)}>
        <DialogTitle>Reject Loan Application</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Reason for Rejection"
            multiline
            rows={4}
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenRejectDialog(false)}>Cancel</Button>
          <Button onClick={handleRejectLoan} color="error" variant="contained">
            Reject
          </Button>
        </DialogActions>
      </Dialog>

      {/* Details Dialog */}
      <Dialog
        open={openDetailsDialog}
        onClose={() => setOpenDetailsDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Loan Details</DialogTitle>
        <DialogContent>
          {selectedLoan && (
            <Box sx={{ mt: 2 }}>
              <Typography><strong>Member:</strong> {selectedLoan.member_name}</Typography>
              <Typography><strong>Amount:</strong> {selectedLoan.principal_amount}</Typography>
              <Typography><strong>Purpose:</strong> {selectedLoan.purpose}</Typography>
              <Typography><strong>Repayment Period:</strong> {selectedLoan.repayment_period}</Typography>
              <Typography><strong>Status:</strong> {selectedLoan.status}</Typography>
              <Typography><strong>Applied Date:</strong> {new Date(selectedLoan.created_at).toLocaleDateString()}</Typography>
              {selectedLoan.due_date && (
                <Typography><strong>Due Date:</strong> {new Date(selectedLoan.due_date).toLocaleDateString()}</Typography>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDetailsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LoanManagement;