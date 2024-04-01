import { Box } from '@mui/material';
import type { ReactNode } from 'react';

type ConfigContentProps = {
  children: ReactNode;
};

export const ConfigContent = (props: ConfigContentProps): JSX.Element => {
  const { children } = props;

  return (
    <Box display="flex" flexDirection="column" padding={4} gap={3} alignItems="center" justifyContent="center">
      {children}
    </Box>
  );
};
