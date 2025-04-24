import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate, useLocation } from 'react-router-dom'
import { Snackbar, Alert } from '@mui/material'
import AdminDashboard from './dashboard/AdminDashboard'
import MemberDashboard from './dashboard/MemberDashboard'

const Home = () => {
    const { user, loading } = useAuth()
    const navigate = useNavigate()
    const location = useLocation()
    const [showSuccess, setShowSuccess] = useState(false)

    useEffect(() => {
        if (!loading && !user) {
            navigate('/login')
        }
        // Check if coming from successful payment
        if (location.state?.paymentSuccess) {
            setShowSuccess(true)
        }
    }, [user, loading, navigate, location])

    const handleCloseSnackbar = () => {
        setShowSuccess(false)
        // Clear the location state
        navigate(location.pathname, { replace: true, state: {} })
    }

    if (loading) {
        return <div>Loading...</div>
    }

    return (
        <>
            {user?.user_type === 'ADMIN' ? (
                <AdminDashboard />
            ) : (
                <MemberDashboard />
            )}
            
            <Snackbar
                open={showSuccess}
                autoHideDuration={6000}
                onClose={handleCloseSnackbar}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert 
                    onClose={handleCloseSnackbar}
                    severity="success"
                    variant="filled"
                    sx={{ width: '100%' }}
                >
                    Registration payment successful! Welcome to the Sacco.
                </Alert>
            </Snackbar>
        </>
    )
}

export default Home