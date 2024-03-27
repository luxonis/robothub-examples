import { Joystick as ReactJoystick } from 'react-joystick-component';

type JoystickProps = {
  x: number;
  y: number;
  handleMove: (event: any) => void;
  handleStop: () => void;
};

export const Joystick = (props: JoystickProps): JSX.Element => {
  const { x, y, handleMove, handleStop } = props;

  return (
    <ReactJoystick
      size={150}
      stickSize={100}
      baseColor="rgba(200, 200, 200, 0.3)"
      stickColor="rgba(200, 200, 200, 0.4)"
      move={handleMove}
      stop={handleStop}
      pos={{ x, y }}
    />
  );
};
