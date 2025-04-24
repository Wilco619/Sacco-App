export const MPESA_CODES = {
  SUCCESS: '0',
  INSUFFICIENT_FUNDS: '2001',
  WRONG_PIN: '2002',
  USER_CANCELLED: '1032',
  TIMEOUT: '1037',
  INVALID_NUMBER: '2041',
  DUPLICATE_REQUEST: '2042',
  INVALID_ACCOUNT: '2043',
  LIMIT_EXCEEDED: '2044',
  TRANSACTION_FAILED: '2045'
};

export const MPESA_MESSAGES = {
  '0': 'Payment completed successfully',
  '2001': 'Insufficient funds in your M-Pesa account. Please top up and try again.',
  '2002': 'Wrong M-Pesa PIN entered. Please try again with the correct PIN.',
  '1032': 'Payment was cancelled. Click "Try Again" when ready.',
  '1037': 'Payment request timed out. Please try again.',
  '2041': 'Invalid phone number format. Please enter a valid M-Pesa number.',
  '2042': 'A similar payment request is in progress. Please wait a moment.',
  '2043': 'Invalid M-Pesa account. Please check your number and try again.',
  '2044': 'Transaction limit exceeded. Try a lower amount or contact M-Pesa.',
  '2045': 'Transaction failed. Please try again or use a different number.',
  'NOT_FOUND': 'Transaction not found or was cancelled. Please try again.',
  'WELFARE_SUCCESS': 'Welfare contribution completed successfully',
  'WELFARE_PENDING': 'Your welfare payment is being processed...',
  'WELFARE_DUPLICATE': 'You have already contributed for this month',
  'default': 'Payment processing failed. Please try again.',
  'TIMEOUT': 'Payment request timed out. Please try again.'
};

export const MPESA_RETRY_ALLOWED = {
  '2001': true,  // Insufficient funds
  '2002': true,  // Wrong PIN
  '1032': true,  // User cancelled
  '1037': true,  // Timeout
  '2041': true,  // Invalid number
  '2042': false, // Duplicate request
  '2043': true,  // Invalid account
  '2044': false, // Limit exceeded
  '2045': true   // Transaction failed
};

export const SHARE_CONSTANTS = {
    VALUE: 1,  // 1 share = 1000 KSH
    MIN_SHARES: 1,
    MAX_SHARES: 50,
    CURRENCY: 'KSH'
};

export const SHARE_OPTIONS = Array.from(
    { length: 10 },  // Show first 10 options
    (_, i) => ({
        value: i + 1,
        label: `${i + 1} ${i + 1 === 1 ? 'Share' : 'Shares'}`,
        amount: (i + 1) * SHARE_CONSTANTS.VALUE
    })
);

export const WELFARE_CONSTANTS = {
    AMOUNT: 300,  // Fixed welfare amount
    CURRENCY: 'KSH',
    PAYMENT_TYPE: 'WELFARE',
    DESCRIPTION: 'Monthly Welfare Contribution'
};

export const MPESA_STATUS = {
    PENDING: 'PENDING',
    COMPLETED: 'COMPLETED',
    FAILED: 'FAILED',
    CANCELLED: 'CANCELLED',
    NOT_FOUND: 'NOT_FOUND',
    TIMEOUT: 'TIMEOUT'
};

export const WELFARE_PAYMENT_MESSAGES = {
    [MPESA_STATUS.PENDING]: 'Processing your welfare contribution...',
    [MPESA_STATUS.COMPLETED]: 'Welfare contribution received successfully',
    [MPESA_STATUS.FAILED]: 'Welfare payment failed. Please try again.',
    [MPESA_STATUS.CANCELLED]: 'Welfare payment was cancelled',
    [MPESA_STATUS.NOT_FOUND]: 'Transaction not found or was cancelled',
    'ALREADY_PAID': 'You have already made your welfare contribution for this month',
    'INVALID_AMOUNT': 'Invalid amount. Welfare contribution is fixed at KSH 300',
    [MPESA_STATUS.TIMEOUT]: 'Payment request timed out',
    'CANCELLED': 'Payment was cancelled by user'
};