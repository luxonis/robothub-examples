import { useEffect, useState } from 'react';
import { Box } from '@mui/material';
import { apiService } from '../../../../services/api-service.js';
import { Joystick } from './Joystick.js';
import { Arrows } from './Arrows.js';

type ArrowKeyMap = { x: number; y: number };

const ARROW_KEY_MAP: Record<string, ArrowKeyMap> = {
  ArrowUp: { x: 0, y: 1 },
  ArrowDown: { x: 0, y: -1 },
  ArrowLeft: { x: -1, y: 0 },
  ArrowRight: { x: 1, y: 0 },
};

type ControllerProps = {
  front: boolean;
  type: 'arrows' | 'joystick';
  onHornInput: () => void;
};

export const Controller = (props: ControllerProps): JSX.Element => {
  const { front, type, onHornInput } = props;
  const [x, setX] = useState<number>(0);
  const [y, setY] = useState<number>(0);
  const [pressedKeys, setPressedKeys] = useState<Record<string, boolean>>({
    ArrowUp: false,
    ArrowLeft: false,
    ArrowDown: false,
    ArrowRight: false,
  });

  const handleMove = (event: any) => {
    setX(event.x);
    setY(event.y);
  };

  const handleStop = () => {
    setX(0);
    setY(0);
  };

  const handleKey = (key: string, pressed: boolean) => {
    if (key in ARROW_KEY_MAP && pressed !== pressedKeys[key]) {
      setPressedKeys(prevKeys => ({
        ...prevKeys,
        [key]: pressed,
      }));
    }
  };

  useEffect(() => {
    let checkGamepadLoop: number;

    const checkGamepad = () => {
      checkGamepadLoop = window.requestAnimationFrame(checkGamepad);

      const gamepad = navigator.getGamepads()[0];
      if (!gamepad) {
        return;
      }

      for (let i = 0; i < gamepad.buttons.length; i++) {
        const button = gamepad.buttons[i];
        if (i === 0) {
          button.value > 0 && onHornInput();
        }
      }

      let axisX = 0;
      let axisY = 0;

      for (let k = 0; k < gamepad.axes.length; k++) {
        const axes = gamepad.axes[k];
        if (k === 1) {
          axisX = axes;
        } else if (k === 0) {
          axisY = axes;
        }
      }

      setX(axisY);
      setY(-axisX);
    };

    checkGamepadLoop = window.requestAnimationFrame(checkGamepad);
    return () => {
      window.cancelAnimationFrame(checkGamepadLoop);
    };
  }, [onHornInput]);

  useEffect(() => {
    const handleDown = (event: KeyboardEvent) => handleKey(event.key, true);
    const handleUp = (event: KeyboardEvent) => handleKey(event.key, false);
    window.addEventListener('keydown', handleDown);
    window.addEventListener('keyup', handleUp);

    return () => {
      window.removeEventListener('keydown', handleDown);
      window.removeEventListener('keyup', handleUp);
    };
  });

  useEffect(() => {
    let newX = 0;
    let newY = 0;
    for (const key in ARROW_KEY_MAP) {
      if (pressedKeys[key]) {
        newX += ARROW_KEY_MAP[key].x;
        newY += ARROW_KEY_MAP[key].y;
      }
    }
    setX(newX);
    setY(newY);
  }, [pressedKeys]);

  useEffect(() => {
    const direction = front ? 1 : -1;
    const linear = y * 2 * direction;
    const angular = -x * 5;

    const sendRequest = () => {
      if (Math.abs(linear) > 0.1 || Math.abs(angular) > 0.1) {
        void apiService.notify('cmd_vel', { linear, angular });
      }
    };

    if (x === 0 && y === 0) {
      void apiService.notify('cmd_vel', { linear: 0, angular: 0 });

      setTimeout(() => {
        void apiService.notify('cmd_vel', { linear: 0, angular: 0 });
      }, 100);
    } else {
      sendRequest();
      const intervalId = setInterval(sendRequest, 30);

      return () => {
        clearInterval(intervalId);
      };
    }
  }, [x, y, front]);

  return (
    <Box position="absolute" zIndex="999" bottom="8%" right="4%">
      {type === 'joystick' ? (
        <Joystick x={x} y={y} handleMove={handleMove} handleStop={handleStop} />
      ) : (
        <Arrows keys={pressedKeys} handler={handleKey} />
      )}
    </Box>
  );
};
