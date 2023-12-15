import { VideoPlayer } from "@luxonis/theme/components/general/VideoPlayer/VideoPlayer";
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { defaultVideoStreamRendererFactory } from "@luxonis/common-fe/video-renderer";
import { useWebRtcStream } from "../hooks/webrtc";
import { Canvas } from "./Canvas/Canvas";
import { CanvasProvider } from "../providers/CanvasProvider";
import { Vector2d } from "konva/lib/types";
import { CanvasToolbar } from "./Canvas/CanvasToolbar";
import { ToolbarProvider } from "../providers/ToolbarProvider";
import { useVideoStream } from "../hooks/videoStream";
import { AspectRatio } from "react-aspect-ratio";

type VideoStreamProps = {
  uniqueKey: string;
};

export const VideoStream = React.forwardRef<HTMLDivElement, VideoStreamProps>(
  (props, _ref) => {
    const { uniqueKey } = props;
    const { webrtcRequest, webrtcSignal } = useWebRtcStream();
    const { setStatus } = useVideoStream();
    const [dimensions, setDimensions] = useState({ height: 0, width: 0 });
    const [offset, setOffset] = useState<Vector2d>({ x: 0, y: 0 });
    const videoRef = useRef<HTMLDivElement | null>(null);

    const requestSdp = React.useCallback(async () => {
      const response = await webrtcRequest(uniqueKey);
      if (response.result === "not-found") {
        setStatus("stopped");
        return null;
      }
      return response.data;
    }, [uniqueKey, webrtcRequest, setStatus]);

    const submitSdp = React.useCallback(
      async (sdp: string, streamId: string) => {
        return webrtcSignal(sdp, streamId);
      },
      [webrtcSignal]
    );

    const handleResize = useCallback(() => {
      if (videoRef.current) {
        const { width, height, x, y } =
          videoRef.current.getBoundingClientRect();

        setDimensions({ width, height });
        setOffset({
          x: window.scrollX + x,
          y: window.scrollY + y,
        });
      }
    }, []);

    useEffect(() => {
      if (!videoRef.current) return;
      const resizeObserver = new ResizeObserver(() => {
        handleResize();
      });
      resizeObserver.observe(videoRef.current);
      return () => resizeObserver.disconnect();
    }, [handleResize]);

    return (
      <div data-is="aspect-ratio-wrapper">
        {/* Make this better, value 90 is kinda hardcoded, may not work in other ratios */}
        {/* 1.778 -> 16 / 9 */}
        <AspectRatio style={{ maxWidth: `${1.778 * 90}vh` }}>
          <div ref={videoRef}>
            <VideoPlayer
              streamKey={uniqueKey}
              requestSdp={requestSdp}
              submitSdp={submitSdp}
              videoStreamRendererFactory={defaultVideoStreamRendererFactory}
              onLoadedData={() => setStatus("running")}
              onEnded={() => setStatus("stopped")}
            />
            <CanvasProvider
              width={dimensions.width}
              height={dimensions.height}
              offset={offset}
            >
              <ToolbarProvider>
                <CanvasToolbar />
                <Canvas />
              </ToolbarProvider>
            </CanvasProvider>
          </div>
        </AspectRatio>
      </div>
    );
  }
);
