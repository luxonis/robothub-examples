import { Link, Outlet, useLocation } from 'react-router-dom';
import { useState, type ReactNode, useMemo, useEffect } from 'react';
import { SportsEsports, Home, Menu } from '@mui/icons-material';
import {
  AppBar,
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import type { RobotStatus } from '../../services/api-service.js';
import Logo from '../../../luxonis_logo.svg';
import { StatusBar } from './StatusBar.js';

const DRAWER_WIDTH = 60;

const MENU_ITEMS: MenuItem[] = [
  { to: '/', icon: <Home />, name: 'Home' },
  { to: '/control', icon: <SportsEsports />, name: 'Control' },
];

type MenuItem = {
  to: string;
  icon: ReactNode;
  name: string;
};

type LayoutProps = {
  status?: RobotStatus;
};

export const Layout = (props: LayoutProps): JSX.Element => {
  const { status } = props;
  const { pathname } = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [open, setOpen] = useState(!isMobile);
  const [appStatus, setAppStatus] = useState<string | undefined>(window.ROBOT_APP_STATUS);

  const pageTitle = useMemo(() => {
    const route = MENU_ITEMS.find(item => item.to === pathname);
    return route ? route.name : '';
  }, [pathname]);

  useEffect(() => {
    const interval = setInterval(() => {
      setAppStatus(window.ROBOT_APP_STATUS);
    }, 1_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Box display="flex" height="100%" sx={{ flexDirection: { xs: 'column', md: 'row' } }}>
      <Drawer
        className="drawer"
        sx={{
          'width': DRAWER_WIDTH,
          'flexShrink': 0,
          '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box', overflow: 'hidden', border: 0 },
          '& .MuiButtonBase-root:hover': { '& .MuiListItemIcon-root': 'white' },
          '& .MuiList-padding': { padding: 0 },
        }}
        open={open}
        variant={isMobile ? 'temporary' : 'permanent'}
        onClose={() => setOpen(false)}
      >
        <Link to="/">
          <IconButton onClick={() => setOpen(true)}>
            <img src={Logo} width="42" height="42" />
          </IconButton>
        </Link>

        <Divider />

        <List>
          {MENU_ITEMS.map(item => (
            <ListItem key={item.name} disablePadding sx={{ display: 'block' }} color="red">
              <Link to={item.to} onClick={() => setOpen(false)}>
                <ListItemButton
                  selected={item.to === pathname}
                  sx={{
                    'minHeight': 48,
                    'justifyContent': 'center',
                    '&.Mui-selected': {
                      'backgroundColor': theme.palette.primary.main,
                      '&:hover': {
                        backgroundColor: theme.palette.primary.main,
                      },
                    },
                  }}
                >
                  <ListItemIcon sx={{ justifyContent: 'center' }} className="drawer-icon">
                    {item.icon}
                  </ListItemIcon>
                </ListItemButton>
              </Link>
            </ListItem>
          ))}
        </List>
      </Drawer>

      <AppBar position="static" color="primary" sx={{ display: { md: 'none' } }}>
        <Toolbar variant="dense">
          <IconButton edge="start" color="inherit" aria-label="menu" sx={{ mr: 2 }} onClick={() => setOpen(true)}>
            <Menu />
          </IconButton>
          <Typography variant="h5" component="div">
            {pageTitle}
          </Typography>
        </Toolbar>
      </AppBar>

      <Outlet />

      <StatusBar
        isMapping={status?.mappingRunning}
        isConnecting={typeof appStatus === 'undefined'}
        isOnline={appStatus === 'active'}
        battery={status?.battery}
        wifi={status?.wifi}
        wifiUnit="Mbps"
      />
    </Box>
  );
};
