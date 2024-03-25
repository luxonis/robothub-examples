import { useState } from 'react';
import Draggable from 'react-draggable';
import type { SxProps } from '@mui/material';
import { Box } from '@mui/material';

export type StreamKey = 'stream_front' | 'stream_back';

interface CommonProps {
  streamKey: StreamKey;
  sx?: SxProps;
}

interface DraggableProps extends CommonProps {
  draggable: true;
  onClick: () => void;
}

interface NonDraggableProps extends CommonProps {
  draggable?: false;
  onClick?: () => void;
}

type Props = DraggableProps | NonDraggableProps;

export const Stream = (props: Props): JSX.Element => {
  const { streamKey, draggable, onClick, sx } = props;
  const [mouseDownStart, setMouseDownStart] = useState<number>(0);

  const handleMouseDown = () => {
    setMouseDownStart(Date.now());
  };

  const handleMouseUp = () => {
    const mouseDownFor = Date.now() - mouseDownStart;

    if (mouseDownFor < 100) {
      onClick && onClick();
    }
  };

  const content = (
    <Box sx={{ backgroundColor: 'black', ...sx }}>
      <rh-video stream-key={streamKey}></rh-video>
    </Box>
  );

  return draggable ? (
    <Draggable onStart={handleMouseDown} onStop={handleMouseUp} bounds="parent">
      {content}
    </Draggable>
  ) : (
    content
  );
};
