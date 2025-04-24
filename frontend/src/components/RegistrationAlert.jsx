import React, { useState } from 'react';
import {
  Alert,
  AlertTitle,
  Button,
  Box
} from '@mui/material';
import { useRegistration } from '../contexts/RegistrationContext';
import RegistrationPaymentDialog from './RegistrationPaymentDialog';
import { toast } from 'react-toastify';

const RegistrationAlert = () => {
  const { registrationStatus, loading, refreshStatus } = useRegistration();
  const [dialogOpen, setDialogOpen] = useState(false);

  const handlePaymentComplete = async (success) => {
    setDialogOpen(false);
    if (success) {
      toast.success('Registration payment successful!');
      await refreshStatus();
    }
  };

  if (loading || registrationStatus?.registration_paid) return null;

  return (
    <>
      <Box sx={{ mb: 3 }}>
        <Alert
          severity="warning"
          action={
            <Button
              color="inherit"
              size="small"
              onClick={() => setDialogOpen(true)}
            >
              Pay Now
            </Button>
          }
        >
          <AlertTitle>Registration Payment Required</AlertTitle>
          Please pay the registration fee of KSH 1,000 to activate your membership
          and access all services.
        </Alert>
      </Box>

      <RegistrationPaymentDialog 
        open={dialogOpen}
        onClose={handlePaymentComplete}
      />
    </>
  );
};

export default RegistrationAlert;