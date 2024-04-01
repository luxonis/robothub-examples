import { Box } from '@mui/material';
import { ArrowKeyIcon } from '../../../icons/ArrowKeyIcon.js';

type ArrowKeyProps = {
  name: string;
  keys: Record<string, boolean>;
  handler: (key: string, pressed: boolean) => void;
};

const rotationMap: Record<string, number> = {
  ArrowUp: 0,
  ArrowLeft: 270,
  ArrowDown: 180,
  ArrowRight: 90,
};

export const ArrowKey = (props: ArrowKeyProps): JSX.Element => {
  const { name, keys, handler } = props;

  return (
    <Box sx={{ cursor: 'pointer' }}>
      <ArrowKeyIcon
        color="#FFFFFF"
        size={80}
        rotation={rotationMap[name] || 0}
        opacity={keys[name] ? 0.8 : 0.5}
        onMouseDown={() => handler(name, true)}
        onMouseUp={() => handler(name, false)}
      />
    </Box>
  );
};
