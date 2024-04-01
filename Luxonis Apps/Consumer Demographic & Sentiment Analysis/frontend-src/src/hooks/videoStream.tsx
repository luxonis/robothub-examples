import { useContext, useMemo } from "react";
import { VideoStreamContext } from "../providers/VideoStreamProvider";

export const useVideoStream = () => {
  const context = useContext(VideoStreamContext);
  const { appConfig, status } = context;

  const isAppConfigLoaded = useMemo(() => appConfig !== null, [appConfig]);
  const isVideoReady = useMemo(() => status === 'running', [status])

  return { ...context, isAppConfigLoaded, isVideoReady };
};
