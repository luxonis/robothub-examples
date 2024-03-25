type ArrowKeyIconProps = {
  color: string;
  size: number;
  rotation: number;
  opacity: any;
  onMouseDown?: () => void;
  onMouseUp?: () => void;
};

export const ArrowKeyIcon = (props: ArrowKeyIconProps): JSX.Element => {
  const { color, rotation, size, opacity, onMouseDown, onMouseUp } = props;

  return (
    <span onTouchStart={onMouseDown} onTouchEnd={onMouseUp} onMouseDown={onMouseDown} onMouseUp={onMouseUp}>
      <svg
        version="1.0"
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        viewBox="0 0 680 680"
        fill={color}
        opacity={opacity}
        style={{ transform: `rotate(${rotation}deg)` }}
      >
        <path d="M97 21.7c-7.9 1.3-18.5 5-26.4 9-7.5 3.9-10.9 6.4-19.2 14.7-8.2 8.3-10.8 11.7-14.6 19.1-2.6 5-5.7 12.4-7 16.5l-2.3 7.5-.3 244.5c-.2 170.7.1 246.5.8 251 5.5 33.5 30.4 60 63.5 67.7 7.7 1.7 18.2 1.8 252.5 1.8h244.5l8.5-2.2c33-8.7 57.2-35.6 62-68.8 1.4-10 1.4-479.7-.1-490.2-4.4-32.7-27.4-58.9-60.4-68.9-5.7-1.8-17.2-1.9-252.5-2-135.6-.1-247.6.1-249 .3zm488 41.2c16.5 5.6 29.1 19 33.5 35.8 2.2 8.4 2.3 468.9 0 477.2-4.9 18.5-20.1 33.2-38.3 37-3.8.8-71.7 1.1-237 1.1-255 0-238.1.4-250.3-6.1C82 602.1 71.4 588.5 68 576c-1-3.5-1.3-55.9-1.3-238.5 0-219.9.1-234.4 1.7-240 2.2-7.5 3.8-10.7 8.8-17.3 7.7-10.4 20.8-17.7 33.8-19 3.6-.4 110.2-.6 237-.6l230.5.1 6.5 2.2z" />
        <path d="M338.3 218.9c-1.7.5-4.9 1.9-7 3.2-2.1 1.3-47.7 46.5-101.4 100.4C150.6 402 132 421.2 131 424.4c-.7 2.1-1 6.4-.8 9.6 1.1 15.5 16 25.3 30.9 20.5 5.1-1.6 9.6-6 93.9-90.1l88.5-88.4 87.5 87.6c49.6 49.6 89.1 88.4 91.2 89.5 9.6 5 19.5 3.3 27.4-4.5 7.8-7.9 9.5-17.8 4.5-27.4-2.9-5.4-196.7-198.7-201.1-200.6-4.8-1.9-10.8-2.6-14.7-1.7z" />
      </svg>
    </span>
  );
};
