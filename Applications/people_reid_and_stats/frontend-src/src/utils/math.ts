export const getLineDistance = (x1: number, y1: number, x2: number, y2: number): number => {
  const dx = x2 - x1;
  const dy = y2 - y1;
  return Math.sqrt(dx * dx + dy * dy);
};

export const isInBounds = (x1: number, y1: number, x2: number, y2: number) => {
  return x1 >= 0 && x1 <= 1 && y1 >= 0 && y1 <= 1 && x2 >= 0 && x2 <= 1 && y2 >= 0 && y2 <= 1;
};

export const getAbsoluteX = (width: number, posX: number) => {
  return posX * width;
}

export const getAbsoluteY = (height: number, posY: number) => {
  return posY * height;
}

export const getRelativeX = (width: number, posX: number) => {
  return posX / width;
}

export const getRelativeY = (height: number, posY: number) => {
  return posY / height;
}

export const getAbsolutePoints = (width: number, height: number, points: number[]) => {
  return points.map((point, index) => {
    if (index % 2 === 0) {
      return getAbsoluteX(width, point);
    } else {
      return getAbsoluteY(height, point);
    }
  });
}