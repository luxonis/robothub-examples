import { v4 as uuidv4 } from 'uuid';

export interface App {
  globalIdentifier: string;
  name: string;
  description: string;
}

export interface AppState {
  appId: string;
  appIdentifier: string;
  appSourceUpToDate: boolean;
  configUpToDate: boolean;
  expectedStatus: string;
  hasEditor: boolean;
  hasFrontend: boolean;
  name: string;
  robotAppId: string;
  status: string;
  studioRunning: boolean;
}

export interface MappingMap {
  mapId: string;
  mapFile: any | null;
  name: string;
  description: string;
}

export enum MapStatusFE {
  Default = 'default',
  Pause = 'pause',
  Active = 'active',
}

interface RobotHubAppWindow extends Window {
  robothubApi: {
    onRcvStatus: (cb: (appStates: AppState[]) => void | Promise<void>) => string;
    offRcvStatus: (id: string) => void;
    onNotification: (callback: (notification: any) => void) => string;
    offNotification: (callbackId: string) => void;
    request: <T>(payload: any, key?: string, timeout?: number) => Promise<T>;
    notify: (key: string, payload: any) => void;
    webrtcRequest: (streamKey: string) => Promise<any>;
    webrtcSignal: (sdp: string, uuid: string) => Promise<any>;
  };
}

if (process.env.NODE_ENV === 'development') {
  const socket = new WebSocket('ws://localhost:8765');
  socket.onopen = _e => {
    //console.debug('[WS] Connection established');
  };

  socket.onmessage = event => {
    //console.debug(`[WS] Data received from server: ${event.data}`);

    try {
      const data = JSON.parse(event.data);

      if (data['type'] === 'notification') {
        for (const cb of notificationsCallbacks) {
          cb.callback({
            key: data['key'],
            payload: data['payload'],
            broadcast: false,
          });
        }
      } else if (data['type'] === 'response') {
        const requestId = data['requestId'];
        const requestCallback = requestsCallback.find(item => item.requestId === requestId);

        requestsCallback = requestsCallback.filter(item => item.requestId !== requestId);

        requestCallback?.resolve({
          key: data['key'],
          payload: data['payload'],
        });
      }
    } catch (error) {
      //console.debug(`[WS] Cannot parse incoming message`);
    }
  };

  socket.onerror = _error => {
    //console.debug(`[WS] Error ${error}`);
  };

  let notificationsCallbacks: {
    callbackId: string;
    callback: any;
  }[] = [];

  let requestsCallback: {
    requestId: string;
    resolve: any;
    reject: any;
    timer: any;
  }[] = [];

  const robothubApi = {
    onRcvStatus: (cb: (appStates: any[]) => void | Promise<void>): string => {
      //console.debug('robothubApi > onRcvStatus');
      robothubApi
        .request({}, 'rcv_status')
        .then(response => {
          void cb(response.payload);
        })
        .catch(console.debug);
      return '00000000-0000-0000-0000-000000000000';
    },
    offRcvStatus: (_id: string): void => {
      //console.debug({ id }, 'robothubApi > offRcvStatus');
    },
    onNotification: (callback: (notification: any) => void): string => {
      //console.debug('robothubApi > onNotification');
      const callbackId = uuidv4();
      notificationsCallbacks.push({
        callbackId,
        callback,
      });
      return callbackId;
    },
    offNotification: (callbackId: string): void => {
      //console.debug('robothubApi > offNotification');
      notificationsCallbacks = notificationsCallbacks.filter(callback => callback.callbackId !== callbackId);
    },
    request: (payload: any, key?: string, _timeout?: number): Promise<any> => {
      //console.debug({ payload, key }, 'robothubApi > request');

      return new Promise((resolve, reject) => {
        const requestId = uuidv4();

        const timer = setTimeout(() => {
          requestsCallback = requestsCallback.filter(item => item.requestId !== requestId);
          reject(new Error('Timeout!'));
        }, 15_000);

        requestsCallback.push({
          requestId,
          resolve,
          reject,
          timer,
        });

        socket.send(
          JSON.stringify({
            type: 'request',
            requestId,
            key,
            payload,
          }),
        );
      });
    },
    notify: (key: string, payload: any): void => {
      //console.debug({ payload, key }, 'robothubApi > notify');

      socket.send(
        JSON.stringify({
          type: 'notification',
          key,
          payload,
        }),
      );
    },
    webrtcRequest: (_streamKey: string): Promise<any> => {
      //console.debug(`webrtcRequest ${streamKey} test01`);
      return new Promise((resolve, _reject) =>
        resolve({
          success: true,
        }),
      );
    },
    webrtcSignal: (_sdp: string, _uuid: string): Promise<any> => {
      //console.debug(`webrtcSignal ${sdp} ${uuid} test02`);
      return new Promise((resolve, _reject) =>
        resolve({
          success: true,
        }),
      );
    },
  };

  (window as unknown as RobotHubAppWindow).robothubApi = robothubApi;
}

const robothubApi = (window as unknown as RobotHubAppWindow).robothubApi;

export type RobotHubApiResponse<T> = {
  status: number;
  payload: T;
};

export default robothubApi;
