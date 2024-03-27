export const DragHandleSvg = (props: Omit<JSX.IntrinsicElements['svg'], 'viewBox' | 'fill'>): JSX.Element => (
  <svg data-icon viewBox="0 0 17 4" fill="none" height="12" {...props}>
    <path
      fill="currentColor"
      stroke="currentColor"
      strokeLinecap="round"
      strokeWidth="3"
      d="M2.49 2h.01m6 0h.01m5.99 0h.01"
    />
  </svg>
);
