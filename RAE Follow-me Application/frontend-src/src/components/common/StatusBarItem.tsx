import type { SxProps } from '@mui/material';
import { Box, Typography } from '@mui/material';

type StatusBarItemProps = {
  text: string;
  sx?: SxProps;
  icon: JSX.Element;
};

export const StatusBarItem = (props: StatusBarItemProps): JSX.Element => {
  const { text, icon, sx } = props;

  return (
    <Box display="flex" alignItems="end" gap="4px" sx={sx}>
      {icon}
      <Typography variant="caption" color="gray">
        {text}
      </Typography>
    </Box>
  );
};
