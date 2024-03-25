import { useEffect, useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material';
import { blueGrey } from '@mui/material/colors';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { Layout } from './components/common/Layout.js';
import type { RobotStatus } from './services/api-service.js';
import { apiService } from './services/api-service.js';
import ControlView from './views/ControlView.js';
import HomeView from './views/HomeView.js';
import NotFoundView from './views/NotFoundView.js';
import robothubApi from './services/robothubApi.js';

import './App.css';

type AppProps = {
  baseUrl: string;
};

function App({ baseUrl }: AppProps): JSX.Element {
  const [status, setStatus] = useState<RobotStatus>();

  let theme = createTheme();
  theme = createTheme(theme, {
    palette: {
      primary: theme.palette.augmentColor({
        color: { main: '#4e38ed' },
        name: 'primary',
      }),
      secondary: {
        main: '#667085',
      },
      title: {
        main: blueGrey[800],
      }
    },
    components: {
      MuiChip: {
        styleOverrides: {
          colorSuccess: {
            padding: '0 5px',
            backgroundColor: '#ecfdf3',
            color: '#12b76a',
          },
          colorError: {
            padding: '0 5px',
            backgroundColor: '#FFE5E5',
            color: '#d92d20',
          },
          colorInfo: {
            padding: '0 5px',
            backgroundColor: '#ffe0cc',
            color: '#ff8533',
          }
        }
      },
    },
  });

  useEffect(() => {
    let statusInterval: NodeJS.Timeout | null = null;

    const fetchStatus = () => {
      apiService
        .loadStatus()
        .then(s => setStatus(s))
        .catch(console.error);
    };

    const handler = robothubApi.onRcvStatus(apps => {
      const app = apps.find(f => f.robotAppId === window.ROBOT_APP_ID);
      if (app) {
        window.ROBOT_APP_STATUS = app.status;

        if (statusInterval === null && app.status === 'active') {
          setTimeout(() => fetchStatus(), 1000);
          statusInterval = setInterval(fetchStatus, 30_000);
        }
      }
    });

    return () => {
      robothubApi.offRcvStatus(handler);
      statusInterval !== null && clearInterval(statusInterval);
    };
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <BrowserRouter basename={baseUrl}>
        <Routes>
          <Route element={<Layout status={status} />}>
            <Route path="/" element={<HomeView />} />
            <Route path="/control" element={<ControlView />} />
            <Route path="*" element={<NotFoundView />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
