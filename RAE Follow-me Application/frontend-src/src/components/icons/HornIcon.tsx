import { useState } from 'react';

interface HornIconProps {
  color: string;
  size: number;
  opacity?: number;
  className?: string;
  onClick?: () => void;
}

export const HornIcon = (props: HornIconProps): JSX.Element => {
  const { color, size, opacity, className, onClick } = props;
  const [isButtonHeld, setIsButtonHeld] = useState(false);

  const handleMouseDown = () => {
    setIsButtonHeld(true);
  };

  const handleMouseUp = () => {
    setIsButtonHeld(false);
  };

  const handleMouseLeave = () => {
    setIsButtonHeld(false);
  };

  return (
    <span
      className={className}
      onClick={onClick}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseLeave}
      onTouchStart={handleMouseDown}
      onTouchEnd={handleMouseUp}
      onTouchCancel={handleMouseLeave}
    >
      <svg
        fill={color}
        width={size}
        height={size}
        version="1.0"
        viewBox="0 0 512 512"
        xmlns="http://www.w3.org/2000/svg"
        opacity={isButtonHeld ? 0.5 : opacity || 0.2}
      >
        <g>
          <path
            d="M479.486,163.011c-3.128,1.925-9.888,5.27-19.633,8.735c-16.572,5.892-34.944,9.434-54.52,9.434H249.323
			c-14.516,0-30.635-2.093-51.087-6.296c-7.64-1.57-14.78-3.176-27.088-6.044c-20.417-4.757-27.478-6.354-36.69-8.143l-90.028-40.31
			c-15.358-7.358-30.022,0.077-37.747,13.471C2.343,141.381,0,151.054,0,159.846v170.667c0,8.782,2.344,18.453,6.68,25.976
			c7.723,13.399,22.384,20.845,38.241,13.256l75.796-33.927c8.826-3.954,17.863-6.926,27.001-8.862
			c3.59-0.76,7.332-1.567,12.246-2.639c6.202-1.355,9.793-2.141,12.454-2.719c8.349-1.816,14.889-3.202,20.997-4.432
			c-0.92,4.308-1.415,8.771-1.415,13.347c0,35.249,28.751,64,64,64h106.667c35.249,0,64-28.751,64-64
			c0-7.104-1.185-13.936-3.339-20.331c12.896,1.442,25.136,4.382,36.525,8.431c9.745,3.465,16.505,6.81,19.633,8.735
			C493.7,336.095,512,325.869,512,309.179v-128C512,164.49,493.7,154.264,479.486,163.011z M362.667,351.846H256
			c-11.685,0-21.333-9.649-21.333-21.333c0-11.685,9.649-21.333,21.333-21.333h106.667c11.685,0,21.333,9.649,21.333,21.333
			C384,342.197,374.351,351.846,362.667,351.846z M469.333,276.766c-19.642-6.448-41.125-10.254-64-10.254h-42.667H256
			c-18.796,0-39.728,2.689-66.218,7.874c-7.831,1.533-15.71,3.187-26.431,5.519c-2.69,0.585-6.31,1.377-12.479,2.725
			c-4.836,1.055-8.499,1.845-11.993,2.585c-12.14,2.572-24.056,6.492-35.601,11.663l-60.612,27.136V166.339l76.615,34.311
			c1.513,0.678,3.101,1.177,4.73,1.487c9.748,1.855,15.902,3.235,37.455,8.257c12.65,2.947,20.076,4.618,28.18,6.283
			c23.036,4.734,41.792,7.17,59.676,7.17h156.011c22.875,0,44.358-3.806,64-10.254V276.766z"
          />
        </g>
      </svg>
    </span>
  );
};
