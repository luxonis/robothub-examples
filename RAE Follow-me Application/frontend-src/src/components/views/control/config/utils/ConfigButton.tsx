import { Button } from '@mui/material';
import type { ReactNode } from 'react';

type ConfigButtonProps = {
  onClick: () => void;
  icon: ReactNode;
  label: string;
};

export const ConfigButton = (props: ConfigButtonProps): JSX.Element => {
  const { onClick, label, icon } = props;
  return (
    <Button
      variant="text"
      onClick={onClick}
      color="secondary"
      endIcon={icon}
      sx={{ border: '1px solid #eaecf0', fontSize: '14px', textTransform: 'none', px: 3 }}
    >
      {label}
    </Button>
  );
};
