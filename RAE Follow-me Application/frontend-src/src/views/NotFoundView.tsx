import { Box, Button, Typography } from '@mui/material';
import { Link } from 'react-router-dom';

export default function NotFoundView(): JSX.Element {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        width: '100%',
      }}
    >
      <Typography variant="h2">
        <b>404</b> Not found
      </Typography>
      <Link to="/" style={{ marginTop: '12px' }}>
        <Button sx={{ px: 5 }} size="large" variant="contained">
          Home
        </Button>
      </Link>
    </Box>
  );
}
