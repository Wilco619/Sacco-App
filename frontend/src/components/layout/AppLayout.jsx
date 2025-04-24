import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'react-hot-toast';
import { useRegistration } from '../../contexts/RegistrationContext';
import RegistrationAlert from '../RegistrationAlert';

// Material UI components
import {
  AppBar,
  Box,
  CssBaseline,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Toolbar,
  Typography,
  Avatar,
  Tooltip,
  Button
} from '@mui/material';

// Icons
import MenuIcon from '@mui/icons-material/Menu';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PersonIcon from '@mui/icons-material/Person';
import GroupIcon from '@mui/icons-material/Group';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import LogoutIcon from '@mui/icons-material/Logout';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import {
  AccountBalance as AccountBalanceIcon,
  AttachMoney as AttachMoneyIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
  AccountBalanceWallet as AccountBalanceWalletIcon,
} from '@mui/icons-material';
import SharesIcon from '@mui/icons-material/ShowChart'; // Add this import at the top with other icons
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';

const drawerWidth = 240;

/**
 * AppLayout provides the main layout structure for authenticated pages
 * including the sidebar navigation, header, and content area
 */
const AppLayout = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const { currentUser, logout } = useAuth();
  const { registrationStatus } = useRegistration();
  const navigate = useNavigate();
  const location = useLocation();
  
  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Logged out successfully');
      navigate('/login');
    } catch (error) {
      toast.error('Failed to log out');
    }
    handleMenuClose();
  };

  const handleProfileClick = () => {
    navigate('/profile');
    handleMenuClose();
  };

  // Navigation items with access control
  const navItems = [
    // Member and Admin shared items
    { 
      title: 'Dashboard', 
      path: '/home', 
      icon: <DashboardIcon />, 
      access: 'all' 
    },
    { 
      title: 'My Profile', 
      path: '/profile', 
      icon: <PersonIcon />, 
      access: 'all' 
    },
    {
      title: 'My Account',
      path: '/account',
      icon: <AccountBalanceIcon />,
      access: 'member'
    },
    {
      title: 'My Loans',
      path: '/loans',  // Updated path
      icon: <AttachMoneyIcon />,
      access: 'member',
      requiresRegistration: true // Only show after registration is complete
    },
    {
      title: 'Shares',
      path: '/shares',
      icon: <SharesIcon />,
      access: 'member',
      requiresRegistration: true // Only show after registration is complete
    },
    // Admin-only items
    { 
      title: 'User Management', 
      path: '/admin/users', 
      icon: <GroupIcon />, 
      access: 'admin' 
    },
    {
      title: 'Loans Management',
      path: '/admin/loans',
      icon: <MonetizationOnIcon />,
      access: 'admin'
    },
    {
      title: 'Document Verification',
      path: '/admin/verify-documents',
      icon: <VerifiedUserIcon />,
      access: 'admin'
    },
    {
      title: 'Reports',
      path: '/admin/reports',
      icon: <AssessmentIcon />,
      access: 'admin'
    },
    {
      title: 'Welfare Management', 
      path: '/admin/welfare', 
      icon: <AccountBalanceWalletIcon />, 
      access: 'admin' 
    },
    {
      title: 'Settings',
      path: '/settings',
      icon: <SettingsIcon />,
      access: 'all'
    }
  ];

  // Filter navigation items based on user role and registration status
  const filteredNavItems = navItems.filter(item => {
    // First check role-based access
    const hasAccess = item.access === 'all' || 
      (item.access === 'admin' && currentUser?.user_type === 'ADMIN') ||
      (item.access === 'member' && currentUser?.user_type !== 'ADMIN');

    // Then check registration requirement
    if (hasAccess && item.requiresRegistration) {
      return registrationStatus?.registration_paid;
    }

    return hasAccess;
  });

  const drawer = (
    <div>
      <Toolbar sx={{ justifyContent: 'center', py: 2 }}>
        <img src="/logo.png" alt="Logo" style={{ height: '40px' }} />
      </Toolbar>
      <Divider />
      <List>
        {filteredNavItems.map((item) => (
          <ListItem key={item.title} disablePadding>
            <ListItemButton 
              selected={location.pathname === item.path}
              onClick={() => {
                navigate(item.path);
                setMobileOpen(false);
              }}
              sx={{
                '&.Mui-selected': {
                  backgroundColor: 'primary.light',
                  '&:hover': {
                    backgroundColor: 'primary.light',
                  }
                }
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.title} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      
      {/* App Bar / Header */}
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {filteredNavItems.find(item => item.path === location.pathname)?.title || 'Dashboard'}
          </Typography>
          
          {/* User menu */}
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography variant="body2" sx={{ mr: 2, display: { xs: 'none', sm: 'block' } }}>
            {(currentUser?.first_name || currentUser?.last_name)
              ? `${currentUser?.first_name ?? ''} ${currentUser?.last_name ?? ''}`.trim()
              : 'User'}
            </Typography>
            
            <Tooltip title="Account settings">
              <IconButton
                onClick={handleMenuOpen}
                size="small"
                aria-controls={Boolean(anchorEl) ? 'account-menu' : undefined}
                aria-haspopup="true"
                aria-expanded={Boolean(anchorEl) ? 'true' : undefined}
                color="inherit"
              >
                <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>
                 {(currentUser?.first_name?.[0] || 'U').toUpperCase()}

                </Avatar>
              </IconButton>
            </Tooltip>
          </Box>
          
          <Menu
            id="account-menu"
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <MenuItem onClick={handleProfileClick}>
              <ListItemIcon>
                <AccountCircleIcon fontSize="small" />
              </ListItemIcon>
              Profile
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout}>
              <ListItemIcon>
                <LogoutIcon fontSize="small" />
              </ListItemIcon>
              Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>
      
      {/* Sidebar Drawer - responsive */}
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
        aria-label="navigation"
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        
        {/* Desktop drawer - permanent */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      
      {/* Main content area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          backgroundColor: (theme) => theme.palette.grey[50]
        }}
      >
        <Toolbar /> {/* Spacing to push content below AppBar */}
        <RegistrationAlert />
        <Outlet />
      </Box>
    </Box>
  );
};

export default AppLayout;