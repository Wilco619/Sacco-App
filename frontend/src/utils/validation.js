/**
 * Format phone number to international format (254...)
 * @param {string} phoneNumber - The phone number to format
 * @returns {string} Formatted phone number
 */
export const formatPhoneNumber = (phoneNumber) => {
    // Remove any non-digit characters
    const numbers = phoneNumber.replace(/\D/g, '');
    
    // Convert to international format
    if (numbers.startsWith('0')) {
        return `254${numbers.slice(1)}`;
    }
    if (!numbers.startsWith('254')) {
        return `254${numbers}`;
    }
    return numbers;
};

/**
 * Validate Safaricom phone number format
 * @param {string} phoneNumber - The phone number to validate
 * @returns {boolean} True if valid, false otherwise
 */
export const validatePhoneNumber = (phoneNumber) => {
    const formatted = formatPhoneNumber(phoneNumber);
    // Validate Safaricom format (254 + 7xx or 1xx)
    return /^254[17]\d{8}$/.test(formatted);
};