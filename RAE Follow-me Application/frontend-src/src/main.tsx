import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.js';

import './index.css';

const robotAppId = window.ROBOT_APP_ID ?? '00000000-0000-0000-0000-000000000000';
const baseUrl = process.env.NODE_ENV === 'development' ? '/' : `/app/${robotAppId}`;

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App baseUrl={baseUrl} />
  </React.StrictMode>,
);
