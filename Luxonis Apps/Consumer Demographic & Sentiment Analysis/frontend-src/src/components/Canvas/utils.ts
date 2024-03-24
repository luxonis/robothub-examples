import { CanvasTag, TrackLabel } from './types';

export const TRACK_LABELS: TrackLabel[] = [
  { id: "all", name: "Everything", color: "purple", type: 'line',labels: []},
  { id: "vehicles", name: "Vehicles", color: "orange", type: 'line', labels: ["car", "motorbike", "bus", "truck"] },
  { id: "people", name: "People", color: "blue", type: 'line', labels: ["person"] },
  { id: "bicycle", name: "Bicycles", color: "teal", type: 'line', labels: ["bicycle"] },
];

export const tagName = (name: string, tags: CanvasTag[]) => {
  return name + '__' + tags.join(';')
}

export const hasTag = (name: string, tag: CanvasTag | string) => {
  return name.indexOf(tag) !== -1;
}