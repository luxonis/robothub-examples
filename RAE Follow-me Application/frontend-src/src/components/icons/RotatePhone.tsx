import type { CSSProperties } from 'react';

type RotatePhoneIconProps = {
  size: number;
  style?: CSSProperties;
  onClick?: () => void;
};

export const RotatePhoneIcon = (props: RotatePhoneIconProps): JSX.Element => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={props.size}
      height={props.size}
      viewBox="0 0 24 24"
      style={props.style}
    >
      <path
        fill="white"
        d="M9 1H3a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V3a2 2 0 0 0-2-2m0 14H3V3h6v12m12-2h-8v2h8v6H9v-1H6v1a2 2 0 0 0 2 2h13a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2m2-3l-4-2l1.91-.91A7.516 7.516 0 0 0 14 2.5V1a9 9 0 0 1 9 9Z"
      />
    </svg>
  );
};
