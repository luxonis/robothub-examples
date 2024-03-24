import { useCallback, useContext } from "react";
import { CanvasContext } from "../providers/CanvasProvider";
import { getRelativeX, getRelativeY } from "src/utils/math";
import { Vector2d } from "konva/lib/types";

export const useCanvas = () => {
  const context = useContext(CanvasContext);
  const {
    setBegPos,
    setEndPos,
    width,
    height,
  } = context;

  const resetPos = useCallback(() => {
    setBegPos(null);
    setEndPos(null);
  }, [setBegPos, setEndPos]);

  const setBegPosAsRel = useCallback(
    (pos: Vector2d) => {
      setBegPos({
        x: getRelativeX(width, pos.x),
        y: getRelativeY(height, pos.y),
      });
    },
    [setBegPos, width, height]
  );

  const setEndPosAsRel = useCallback(
    (pos: Vector2d) => {
      setEndPos({
        x: getRelativeX(width, pos.x),
        y: getRelativeY(height, pos.y),
      });
    },
    [setEndPos, width, height]
  );

  return {
    ...context,
    resetPos,
    setBegPosAsRel,
    setEndPosAsRel,
  };
};
