import { Box } from '@mui/material';
import { ArrowKey } from './ArrowKey.js';

type ArrowsProps = {
  handler: (key: string, pressed: boolean) => void;
  keys: Record<string, boolean>;
};

export const Arrows = (props: ArrowsProps): JSX.Element => {
  const { keys, handler } = props;

  return (
    <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center">
      <ArrowKey name="ArrowUp" keys={keys} handler={handler} />
      <Box display="flex" flexDirection="row">
        <ArrowKey name="ArrowLeft" keys={keys} handler={handler} />
        <ArrowKey name="ArrowDown" keys={keys} handler={handler} />
        <ArrowKey name="ArrowRight" keys={keys} handler={handler} />
      </Box>
    </Box>
  );
};
