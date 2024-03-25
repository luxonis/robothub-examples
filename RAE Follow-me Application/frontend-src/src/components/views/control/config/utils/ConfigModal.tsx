import type { SxProps } from '@mui/material';
import { Box, Modal, Typography } from '@mui/material';
import type { ReactNode } from 'react';

type ConfigModalProps = {
  children: ReactNode;
  visible?: boolean;
  title?: string;
  onClose?: () => void;
};

const MODAL_STYLE: SxProps = {
  display: 'block',
  position: 'absolute' as const,
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  bgcolor: 'white',
  boxShadow: 24,
  borderRadius: 5,
  justifyContent: 'center',
  alignItems: 'center',
  flexDirection: 'column',
  p: 5,
  maxHeight: '100%',
  overflowY: 'auto',
};

export const ConfigModal = (props: ConfigModalProps): JSX.Element => {
  const { children, visible, title, onClose } = props;

  return (
    <Modal open={Boolean(visible)} onClose={onClose}>
      <Box sx={MODAL_STYLE}>
        <Box display="flex" flexDirection="column" gap={3} alignItems="center" justifyContent="center">
          <Typography variant="h5" fontWeight={700} color="title" textAlign="center">
            {title}
          </Typography>
          {children}
        </Box>
      </Box>
    </Modal>
  );
};
