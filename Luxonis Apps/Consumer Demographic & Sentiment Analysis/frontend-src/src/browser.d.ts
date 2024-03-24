import type { RobotHubApi } from './hooks/api.types';

type PrivateRobotHubApi = RobotHubApi & {
  readonly webrtcRequest: (streamKey: string) => Promise<MqttReceivePayload<typeof webrtc_request_$id>>;
  readonly webrtcSignal: (sdp: string, uuid: string) => Promise<MqttReceivePayload<typeof webrtc_signal_$id>>;
};

declare global {
  interface Window {
    robothubApi: PrivateRobotHubApi;
  }
}
