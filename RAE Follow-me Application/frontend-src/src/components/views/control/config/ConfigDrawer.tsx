import { useState } from 'react';
import { Box } from '@mui/material';
import { DragHandleSvg } from '../../../icons/DragHandleSvg.js';
import type { AppMode } from '../../../../types.js';
import { LcdConfig } from './LcdConfig.js';
import { LedConfig } from './LedConfig.js';
import { ModeConfig } from './ModeConfig.js';

type ConfigDrawerProps = {
  controls: 'joystick' | 'arrows';
  controlsHandler: () => void;
  mode: AppMode;
  setMode: (mode: AppMode) => void;
};

export const ConfigDrawer = (props: ConfigDrawerProps): JSX.Element => {
  const { controls, controlsHandler, mode, setMode } = props;
  const [hidden, setHidden] = useState<boolean>(true);

  const toggleHidden = () => {
    setHidden(prevHiddnen => !prevHiddnen);
  };

  return (
    <Box
      display="flex"
      flexDirection="column"
      position="absolute"
      top="0"
      alignItems="center"
      justifyContent="center"
      borderRadius="0 0 12px 12px"
      bottom="auto"
      left="auto"
      zIndex="1001"
      minWidth="80px"
      sx={{ backgroundColor: 'white' }}
    >
      {!hidden && (
        <Box display="flex" flexDirection="row" gap="10px" padding="20px" paddingBottom="0px">
          <ModeConfig controls={controls} controlsHandler={controlsHandler} mode={mode} setMode={setMode} />
          <LcdConfig />
          <LedConfig />
        </Box>
      )}

      <Box
        onClick={toggleHidden}
        display="flex"
        alignItems="center"
        justifyContent="center"
        sx={{ cursor: 'pointer' }}
        width="100%"
        paddingY={2}
      >
        <DragHandleSvg color="#5a5a5a" />
      </Box>
    </Box>
  );
};
