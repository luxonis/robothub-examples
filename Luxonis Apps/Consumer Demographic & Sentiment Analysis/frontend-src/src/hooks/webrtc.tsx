import React from 'react';

export const useWebRtcStream = (): {
  webrtcRequest: (streamKey: string) => Promise<any>;
  webrtcSignal: (sdp: string, streamId: string) => Promise<any>;
} => {
  const webrtcRequest = React.useCallback(
    async (streamKey: string) => {
      return window.robothubApi.webrtcRequest(streamKey ?? '');
    },
    [],
  );
  const webrtcSignal = React.useCallback(
    async (sdp: string, streamId: string) => {
      window.robothubApi.webrtcSignal(sdp, streamId)
    },
    [],
  );

  return { webrtcRequest, webrtcSignal };
};
