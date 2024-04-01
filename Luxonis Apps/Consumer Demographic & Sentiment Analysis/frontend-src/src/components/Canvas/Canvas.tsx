import { Stage } from "react-konva";
import { useCanvas } from "../../hooks/canvas";
import { useVideoStream } from "../../hooks/videoStream";
import { useMemo } from "react";
import { useToolbar } from "../../hooks/toolbar";
import { KonvaEventObject } from "konva/lib/Node";
import { getRelativeX, getRelativeY } from "../../utils/math";
import { CanvasScope } from "./CanvasScope";
import { Lines } from "./Lines/Lines";

export const Canvas = () => {
  const canvas = useCanvas();
  const { isVideoReady } = useVideoStream();
  const { isCanvasVisible } = useToolbar();
  const { triggerEvent, width, height } = canvas;

  const style = useMemo(() => {
    return {
      position: "absolute",
      top: canvas.offset.y,
      left: canvas.offset.x,
      zIndex: 50,
      backgroundColor: "transparent",
    } as const;
  }, [canvas]);

  const handleMouseDown = (e: KonvaEventObject<MouseEvent>) => {
    const evt = e.evt;
    const offsetX = getRelativeX(width, evt.offsetX);
    const offsetY = getRelativeY(height, evt.offsetY);
    canvas.setBegPos({ x: offsetX, y: offsetY });

    triggerEvent("mouseDown", e);
  };

  const handleMouseMove = (e: KonvaEventObject<MouseEvent>) => {
    const evt = e.evt;
    const offsetX = getRelativeX(width, evt.offsetX);
    const offsetY = getRelativeY(height, evt.offsetY);
    canvas.setEndPos({ x: offsetX, y: offsetY });

    triggerEvent("mouseMove", e);
  };

  const handleMouseUp = async (e: KonvaEventObject<MouseEvent>) => {
    triggerEvent("mouseUp", e);
  };

  return (
    <>
      <Stage
        style={style}
        width={canvas.width}
        height={canvas.height}
        visible={isVideoReady && isCanvasVisible}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
      >
        <CanvasScope scopeKey="lines">
          <Lines />
        </CanvasScope>
      </Stage>
    </>
  );
};
