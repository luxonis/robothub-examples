import { Helmet } from 'react-helmet';
import { Box } from '@mui/material';
import { Headline } from '../components/views/home/Headline.js';

export default function HomeView(): JSX.Element {
  return (
    <>
      <Helmet>
        <title>Home</title>
      </Helmet>
      <Box
        marginLeft="auto"
        marginRight="auto"
        display="flex"
        flexDirection="column"
        justifyContent="center"
        gap={1}
        padding={1}
      >
        <Headline />
      </Box>
    </>
  );
}
