import type { SxProps } from '@mui/material';
import { Box, IconButton } from '@mui/material';
import { useState, type ReactNode, useMemo } from 'react';

type UIElementProps = {
  top?: string;
  left?: string;
  bottom?: string;
  right?: string;
  opacity?: number;
  border?: number;
  sx?: SxProps;
  onClick?: () => void;
  onDown?: () => void;
  onUp?: () => void;
  children: ReactNode;
};

export const UIElement = (props: UIElementProps): JSX.Element => {
  const { top, left, bottom, right, opacity, sx } = props;
  const [active, setActive] = useState(false);

  const handleDown = () => {
    props.onClick && props.onClick();
    props.onDown && props.onDown();
    setActive(true);
  };

  const handleUp = () => {
    props.onUp && props.onUp();
    setActive(false);
  };

  const elementOpacity = useMemo(() => (active ? 0.8 : opacity || 0.5), [active, opacity]);

  return (
    <Box
      position="absolute"
      zIndex="999"
      top={top}
      left={left}
      bottom={bottom}
      right={right}
      border={`${props.border || 4}px solid white`}
      borderRadius="99999%"
      sx={{ opacity: elementOpacity, ...sx }}
    >
      <IconButton
        disableRipple
        onContextMenu={e => e.preventDefault()}
        onMouseDown={handleDown}
        onMouseUp={handleUp}
        onMouseLeave={handleUp}
        onTouchStart={handleDown}
        onTouchEnd={handleUp}
        onTouchCancel={handleUp}
      >
        {props.children}
      </IconButton>
    </Box>
  );
};
