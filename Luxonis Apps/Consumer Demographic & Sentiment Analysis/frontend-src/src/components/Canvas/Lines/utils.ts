import { getLineDistance } from 'src/utils/math';
import { getAbsoluteX, getAbsoluteY, isInBounds } from '../../../utils/math';
import { LineAgentData, LineData } from './types';

export const isValidLine = (width: number, height: number, minLength: number, x1: number, y1: number, x2: number, y2: number) => {
  return (
    isInBounds(x1, y1, x2, y2) &&
    getLineDistance(
      getAbsoluteX(width, x1),
      getAbsoluteY(height, y1),
      getAbsoluteX(width, x2),
      getAbsoluteY(height, y2)
    ) >= minLength
  );
};

export const prepareAgentLine = (line: LineData) => {
  const fields: Array<keyof LineData> = [
    "id",
    "trackLabelId",
    "detectionLabels",
    "isDisabled",
    "x1",
    "y1",
    "x2",
    "y1",
    "y2",
  ];

  // Filter out fields
  const agentLineData: any = {};
  for (const field of fields) {
    if (line[field] !== undefined) {
      agentLineData[field] = line[field];
    }
  }

  return agentLineData as LineAgentData;
};

export const getLinePointX = (line: LineData, pointIndex: number) => {
  return line[pointIndex === 0 ? "x1" : "x2"]
}

export const getLinePointY = (line: LineData, pointIndex: number) => {
  return line[pointIndex === 0 ? "y1" : "y2"]
}
