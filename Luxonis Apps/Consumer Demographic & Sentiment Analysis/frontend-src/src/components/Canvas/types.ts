import { ThemeColor } from '@luxonis/theme/dist/types';

export type TrackLabel = {
  id: string;
  labels: string[],
  name: string;
  color: ThemeColor;
  type: string;
}

export type CanvasTag = 'IGNORE_MOUSE_DOWN' | "LINE"