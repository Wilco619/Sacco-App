export const formatCurrency = (amount) => {
    if (!amount && amount !== 0) return 'KSH 0.00';
    
    return new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: 'KES',
        minimumFractionDigits: 2
    }).format(amount).replace('KES', 'KSH');
};

export const formatDate = (date) => {
    if (!date) return 'N/A';
    return new Date(date).toLocaleDateString('en-KE', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
};