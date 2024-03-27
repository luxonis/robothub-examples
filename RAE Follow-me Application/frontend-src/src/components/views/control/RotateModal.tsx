import type { SxProps } from '@mui/material';
import { Box, Modal, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { RotatePhoneIcon } from '../../icons/RotatePhone.js';

const isPortrait = (): boolean => {
  const h = window.innerHeight;
  const w = window.innerWidth;
  return h > w;
};

const rotateModalStyle: SxProps = {
  display: 'flex',
  flexDirection: 'column',
  position: 'absolute' as const,
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  bgcolor: 'black',
  boxShadow: 24,
  borderRadius: 10,
  p: 3,
  px: 6,
};

export const RotateModal = (): JSX.Element => {
  const [visible, setVisible] = useState(isPortrait);

  useEffect(() => {
    const handleWindowResize = () => {
      setVisible(isPortrait);
    };

    window.addEventListener('resize', handleWindowResize);
    return () => window.removeEventListener('resize', handleWindowResize);
  }, []);

  return (
    <Modal open={visible} onClose={() => setVisible(false)}>
      <Box sx={rotateModalStyle}>
        <Typography variant="h5" color="white" textAlign="center">
          Rotate your phone
        </Typography>
        <RotatePhoneIcon size={250} style={{ alignSelf: 'center' }} />
        <Typography variant="h5" color="white" textAlign="center">
          for best experience
        </Typography>
      </Box>
    </Modal>
  );
};
