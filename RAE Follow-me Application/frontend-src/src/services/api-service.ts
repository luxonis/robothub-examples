/* eslint-disable no-warning-comments */
import type { AppState, App } from './robothubApi.js';
import robothubApi from './robothubApi.js';

export interface InstalledApp extends AppState {
  linkEditor: string | null;
  linkFrontend: string | null;
}

export interface RobotHubApp {
  id: string;
  title: string;
  text: string;
  isVisible: boolean;
  identifier: string;
}

export interface RobotStatus {
  memory: number;
  battery: number;
  wifi: number;
  mappingRunning: boolean;
  mappingPaused: boolean;
}

const waitForStart = (callback: () => void) => {
  const status = window.ROBOT_APP_STATUS;
  return status === 'active' && callback();
};

const loadStatus = async (): Promise<RobotStatus> => {
  return new Promise((resolve, reject) => {
    waitForStart(() => {
      robothubApi
        .request<{
          payload: {
            downloadSpeed: string;
            diskTotal: number;
            diskUsage: number;
            batteryCapacity: number;
            mappingPaused: boolean;
            mappingRunning: boolean;
          };
        }>({}, 'robot_status', 15_000)
        .then(response => {
          if (!response.payload) {
            reject(new Error('Robot is not initialized!')); // TODO (milan.medvec)
          }

          const memory = response.payload.diskTotal - response.payload.diskUsage;
          const battery = response.payload.batteryCapacity;

          // let wifi = Number(response.payload.downloadSpeed);
          // wifi = isNaN(wifi) ? 100 : Math.min(wifi, 100);
          const wifi = (navigator as any).connection.downlink; // TODO

          resolve({
            memory,
            battery,
            wifi,
            mappingPaused: response.payload.mappingPaused,
            mappingRunning: response.payload.mappingRunning,
          });
        })
        .catch(reject);
    });
  });
};

const getInstalledApps = async (): Promise<InstalledApp[]> => {
  return new Promise((resolve, _reject) => {
    waitForStart(() => {
      robothubApi.onRcvStatus(apps => {
        const installedApps = apps.map(item => {
          return {
            ...item,
            linkEditor: item.hasEditor ? `/editor/${item.robotAppId}` : null,
            linkFrontend: item.hasFrontend ? `/app/${item.robotAppId}` : null,
          };
        });

        resolve(installedApps);
      });
    });
  });
};

const getRobothubApps = async (): Promise<RobotHubApp[]> => {
  return new Promise((resolve, reject) => {
    waitForStart(() => {
      robothubApi
        .request<{ payload: App[] }>({}, 'apps_get_list', 15_000)
        .then(response =>
          resolve(
            response.payload.map(item => {
              return {
                id: item.globalIdentifier,
                title: item.name,
                text: item.description,
                isVisible: true,
                identifier: item.globalIdentifier,
              };
            }),
          ),
        )
        .catch(reject);
    });
  });
};

const notify = (key: string, payload: any): Promise<void> => {
  return new Promise((resolve, _reject) => {
    waitForStart(() => {
      robothubApi.notify(key, payload);
      resolve();
    });
  });
};

const request = <T>(payload: any, key?: string, timeout?: number): Promise<T> => {
  return new Promise((resolve, reject) => {
    waitForStart(() => {
      robothubApi
        .request<T>(payload, key, timeout)
        .then(response => resolve(response))
        .catch(reject);
    });
  });
};

export const apiService = {
  loadStatus,
  getInstalledApps,
  getRobothubApps,
  notify,
  request,
};
