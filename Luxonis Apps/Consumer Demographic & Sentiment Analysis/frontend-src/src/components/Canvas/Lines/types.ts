export type LineData = {
  id: string;
  type: 'line';
  trackLabelId: string;
  detectionLabels: string[];
  count: number;
  color: string;
  isDisabled: boolean;
  isDragging?: boolean;
  isHovering?: boolean;
  hoverCornerIndex: number | null;
  lastCrossAt: number | null;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
};

export type LineAgentData = {
  id: string;
  type: 'line';
  trackLabelId: string;
  detectionLabels: string[];
  count: number;
  isDisabled: boolean;
  lastCrossAt: number | null;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
};
