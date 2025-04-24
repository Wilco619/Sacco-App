import React, { useState, useEffect } from 'react';
import {
  Box,
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
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Chip,
  Tooltip,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { WelfareAPI } from '../../api/api';
import { toast } from 'react-hot-toast';

const WelfareManagement = () => {
  const [funds, setFunds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedFund, setSelectedFund] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    minimum_contribution: '',
    contribution_frequency: 'MONTHLY',
    status: 'ACTIVE',
    date_established: new Date().toISOString().split('T')[0]  // Add today's date by default
  });

  const fetchWelfareFunds = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await WelfareAPI.getWelfareFunds();
      setFunds(Array.isArray(response) ? response : []);
    } catch (error) {
      setError(error.message || 'Failed to fetch welfare funds');
      toast.error('Failed to fetch welfare funds');
      setFunds([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWelfareFunds();
  }, []);

  const handleDialogOpen = (fund = null) => {
    if (fund) {
      setSelectedFund(fund);
      setFormData({
        name: fund.name,
        description: fund.description,
        minimum_contribution: fund.minimum_contribution,
        contribution_frequency: fund.contribution_frequency,
        status: fund.status
      });
    } else {
      setSelectedFund(null);
      setFormData({
        name: '',
        description: '',
        minimum_contribution: '',
        contribution_frequency: 'MONTHLY',
        status: 'ACTIVE'
      });
    }
    setOpenDialog(true);
  };

  const handleDialogClose = () => {
    setOpenDialog(false);
    setSelectedFund(null);
    setFormData({
      name: '',
      description: '',
      minimum_contribution: '',
      contribution_frequency: 'MONTHLY',
      status: 'ACTIVE'
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (selectedFund) {
        await WelfareAPI.updateWelfareFund(selectedFund.id, formData);
        toast.success('Welfare fund updated successfully');
      } else {
        await WelfareAPI.createWelfareFund(formData);
        toast.success('Welfare fund created successfully');
      }
      handleDialogClose();
      fetchWelfareFunds();
    } catch (error) {
      toast.error(error.message || 'Failed to save welfare fund');
    }
  };

  const handleDelete = async (fundId) => {
    if (window.confirm('Are you sure you want to delete this fund?')) {
      try {
        await WelfareAPI.deleteWelfareFund(fundId);
        toast.success('Welfare fund deleted successfully');
        fetchWelfareFunds();
      } catch (error) {
        toast.error('Failed to delete welfare fund');
      }
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5" component="h1">
          Welfare Fund Management
        </Typography>
        <Box>
          <Button
            startIcon={<RefreshIcon />}
            onClick={fetchWelfareFunds}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleDialogOpen()}
          >
            New Fund
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Minimum Contribution</TableCell>
              <TableCell>Frequency</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Total Amount</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : funds.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  No welfare funds found
                </TableCell>
              </TableRow>
            ) : (
              funds.map((fund) => (
                <TableRow key={fund.id}>
                  <TableCell>{fund.name}</TableCell>
                  <TableCell>{fund.description}</TableCell>
                  <TableCell>{fund.minimum_contribution}</TableCell>
                  <TableCell>{fund.contribution_frequency}</TableCell>
                  <TableCell>
                    <Chip
                      label={fund.status}
                      color={fund.status === 'ACTIVE' ? 'success' : 'default'}
                    />
                  </TableCell>
                  <TableCell>{fund.total_amount}</TableCell>
                  <TableCell>
                    <Tooltip title="Edit">
                      <IconButton onClick={() => handleDialogOpen(fund)}>
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton onClick={() => handleDelete(fund.id)}>
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={handleDialogClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedFund ? 'Edit Welfare Fund' : 'Create New Welfare Fund'}
        </DialogTitle>
        <DialogContent>
          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Fund Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              margin="normal"
              multiline
              rows={3}
              required
            />
            <TextField
              fullWidth
              label="Minimum Contribution"
              type="number"
              value={formData.minimum_contribution}
              onChange={(e) => setFormData({ ...formData, minimum_contribution: e.target.value })}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              select
              label="Contribution Frequency"
              value={formData.contribution_frequency}
              onChange={(e) => setFormData({ ...formData, contribution_frequency: e.target.value })}
              margin="normal"
              required
              SelectProps={{
                native: true,
              }}
            >
              <option value="MONTHLY">Monthly</option>
              <option value="QUARTERLY">Quarterly</option>
              <option value="ANNUALLY">Annually</option>
              <option value="ONETIME">One Time</option>
            </TextField>
            <TextField
              fullWidth
              select
              label="Status"
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              margin="normal"
              required
              SelectProps={{
                native: true,
              }}
            >
              <option value="ACTIVE">Active</option>
              <option value="INACTIVE">Inactive</option>
            </TextField>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose}>Cancel</Button>
          <Button variant="contained" onClick={handleSubmit}>
            {selectedFund ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default WelfareManagement;