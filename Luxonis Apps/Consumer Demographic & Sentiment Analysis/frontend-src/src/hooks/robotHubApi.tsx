import { useCallback } from "react";
import { useVideoStream } from './videoStream';

export const useRobotHubApi = () => {
  const { isDev } = useVideoStream();

  const notify = useCallback(
    (uniqueKey: string, payload: any) => {
      if (isDev) return;
      window.robothubApi.notify(uniqueKey, payload);
    },
    [isDev]
  );

  const request = useCallback(
    <T,>(uniqueKey: string, payload: any) => {
      if (isDev) return;
      return window.robothubApi.request(payload, uniqueKey) as Promise<{
        payload: { result: T };
      }>;
    },
    [isDev]
  );

  return { notify, request };
};
