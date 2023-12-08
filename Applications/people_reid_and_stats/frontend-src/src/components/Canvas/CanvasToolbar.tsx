import { useVideoStream } from "src/hooks/videoStream";
import { useCanvas } from "../../hooks/canvas";
import { Spinner } from "./Toolbar/Spinner";
import { useToolbar } from "src/hooks/toolbar";
import { LabelSelector } from "./Toolbar/LabelSelector";
import { CSSProperties, useMemo } from "react";
import { LineOptions } from "./Toolbar/LineOptions";
import { LineDetail } from "./Toolbar/LineDetail";
import { HideCanvasButton } from './Toolbar/HideCanvasButtons';

export const CanvasToolbar = () => {
  const { isVideoReady } = useVideoStream();
  const { offset } = useCanvas();
  const { isLoading, isCanvasVisible } = useToolbar();

  const style = useMemo(() => {
    return {
      position: "absolute",
      top: offset.y,
      left: offset.x,
      zIndex: 100,
      backgroundColor: "transparent",
    } as CSSProperties;
  }, [offset]);

  const visibleStyle = useMemo(() => {
    return {
      visibility: isCanvasVisible ? "visible" : "hidden",
    } as CSSProperties;
  }, [isCanvasVisible]);

  return isVideoReady ? (
    <div style={style}>
      {isLoading ? (
        <Spinner />
      ) : (
        <>
          <div style={visibleStyle}>
            <LabelSelector />
            <LineOptions />
            <LineDetail />
          </div>

          <HideCanvasButton />
        </>
      )}
    </div>
  ) : (
    <></>
  );
};
