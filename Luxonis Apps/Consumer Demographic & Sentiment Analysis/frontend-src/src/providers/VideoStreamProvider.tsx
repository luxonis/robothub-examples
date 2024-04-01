import React, {
  ReactNode,
  createContext,
  useCallback,
  useEffect,
  useState,
} from "react";
import { useRobotHubApi } from "../hooks/robotHubApi";

const DEFAULT_CONFIG: AppConfig = {
  robotId: '',
  robotAppId: ''
}

type VideoStreamProps = {
  children: ReactNode;
};

type VideoStreamData = {
  isDev: boolean;
  appConfig: AppConfig | null;
  status: VideoStatus;
  setStatus: (status: VideoStatus) => void;
};

export const VideoStreamContext = createContext<VideoStreamData>({
  isDev: false,
  appConfig: null,
  status: "connecting",
  setStatus: () => {},
});

export type VideoStatus = "connecting" | "running" | "stopped";
type AppConfig = {
  robotId: string;
  robotAppId: string;
};

export const VideoStreamProvider: React.FC<VideoStreamProps> = ({
  children,
}) => {
  const { request } = useRobotHubApi();
  const [appConfig, setAppConfig] = useState<AppConfig | null>(null);
  const [isDev] = useState<boolean>(process.env.NODE_ENV === "development");
  const [status, setStatus] = useState<VideoStatus>("connecting");

  const fetchConfig = useCallback(async () => {
    try {
      const response = await request<AppConfig>("get_config", {});
      if (!response) {
        throw new Error(
          `Unknown resposne from app config - ${JSON.stringify(response)}`
        );
      }

      const appConfig = response?.payload.result;
      setAppConfig(appConfig);
    } catch (e) {
      console.info("Problem fetching app config, setting default config...", e);
      setAppConfig({ ...DEFAULT_CONFIG });
    }
  }, [request]);

  useEffect(() => {
    status === "running" && fetchConfig();
  }, [status, isDev, fetchConfig]);

  // Development - Mark VideoStream even if its not
  useEffect(() => {
    isDev && setStatus("running");
  }, [isDev]);

  return (
    <VideoStreamContext.Provider value={{ isDev, appConfig, status, setStatus }}>
      {children}
    </VideoStreamContext.Provider>
  );
};
