import { useAuth } from '../contexts/AuthContext';
import MemberDashboard from './dashboard/MemberDashboard';
import AdminDashboard from './dashboard/AdminDashboard';
import LoadingScreen from '../components/LoadingScreen';

const Dashboard = () => {
  const { currentUser, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  return currentUser?.user_type === 'ADMIN' ? (
    <AdminDashboard />
  ) : (
    <MemberDashboard />
  );
};

export default Dashboard;