import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Box, Button, Typography } from '@mui/material';
import { SportsEsports } from '@mui/icons-material';
import Rae from '../../../assets/homeView/rae.png';

const tips: string[] = [
  'Switch between cameras by clicking the smaller stream to focus on a different angle.',
  "Customize RAE's LCD display with a unique face and color to add a personal touch.",
  "Control the color and effects of RAE's LEDs for a vibrant and dynamic appearance.",
  'Try arrow controls for a simpler way to navigate RAE.',
];

export const Headline = (): JSX.Element => {
  const [randomTip, setRandomTip] = useState('');

  useEffect(() => {
    const randomIndex = Math.floor(Math.random() * tips.length);
    setRandomTip(tips[randomIndex]);
  }, []);

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      sx={{ marginTop: { sm: '0px', md: '10%', lg: '20%' } }}
    >
      <Typography variant="h3" fontWeight={700} color="title">
        Welcome!
      </Typography>
      <Typography variant="subtitle1" fontWeight={500} color="secondary" textAlign="center">
        Tip: {randomTip}
      </Typography>

      <img src={Rae} alt="Rae robot" width="100%" />

      <Link to="/control">
        <Button variant="contained" endIcon={<SportsEsports />} size="large">
          Take Control of your rae
        </Button>
      </Link>
    </Box>
  );
};
