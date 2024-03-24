import type { JsonValue } from 'type-fest';

declare global {
  interface Window {
    ROBOT_APP_ID: string;
    MQTT_USERNAME: string;
    MQTT_PASSWORD: string;
  }
}

/**
 * `notification` / `request` payload - any JSON-serializable object.
 */
export type Payload = JsonValue;

export type VoidCallback = () => void | Promise<void>;

/**
 * A notification received from the application.
 */
export interface Notification {
  key: string;
  payload: unknown;
  broadcast: boolean;
}

export type NotificationCallback = (args: Notification) => void | Promise<void>;

export type RequestCallback = (args: {
  key: string;
  payload: unknown;
  broadcast: boolean;
}) => { response: unknown | Promise<unknown> } | 'ignore';

/**
 * Global object to interact with the RobotHub Agent / App.
 *
 * @example
 * ```js
 * console.log(window.robothubApi.robotAppId);
 * ```
 * @example
 * ```js
 * window.robothubApi.onNotificationWithKey('imu-data', ({ payload }) => {
 *  console.log(`Received IMU data:`, payload);
 * });
 * ```
 */
export type RobotHubApi = {
  /**
   * ID of the application that provided the frontend.
   *
   * @example `4ab416fd-d35c-4221-b96d-2986eaa2c9dc`
   * @deprecated
   */
  readonly robotAppId: string;

  /**
   * Whether or not is the connection with agent established.
   */
  readonly isConnected: boolean;

  readonly onRcvStatus: (cb: (appStates: unknown) => void | Promise<void>) => string;
  readonly offRcvStatus: (id: string) => void;

  /**
   * Registers a callback that will be called when connection with the app is established.
   *
   * @param cb Invoked every time the connection with the app is established.
   * @returns ID to unregister the callback.
   * @see {@link offConnectedWithApp}
   */
  readonly onConnectedWithApp: (cb: VoidCallback) => string;

  /**
   * Unregisters a callback that was previously registered with {@link onConnectedWithApp}.
   *
   * @param id ID of callback to unregister.
   */
  readonly offConnectedWithApp: (id: string) => void;

  /**
   * Registers a callback that will be called when connection with the app is lost.
   *
   * @param cb Invoked every time the connection with the app is lost.
   * @returns ID to unregister the callback.
   * @see {@link offDisconnectedFromApp}
   */
  readonly onDisconnectedFromApp: (cb: VoidCallback) => string;

  /**
   * Unregisters a callback that was previously registered with {@link onDisconnectedFromApp}.
   *
   * @param id ID of callback to unregister.
   */
  readonly offDisconnectedFromApp: (id: string) => void;

  /**
   * Registers a callback that will be called when connection with the agent is established.
   *
   * @param cb Invoked every time the connection with the agent is established.
   * @returns ID to unregister the callback.
   * @see {@link offConnected}
   */
  readonly onConnected: (cb: VoidCallback) => string;

  /**
   * Unregisters a callback that was previously registered with {@link onConnected}.
   *
   * @param id ID of callback to unregister.
   */
  readonly offConnected: (id: string) => void;

  /**
   * Registers a callback that will be called when the connection with the agent is lost.
   *
   * @param cb Invoked every time the connection with the agent is lost.
   * @returns ID to unregister the callback.
   * @see {@link offDisconnected}
   */
  readonly onDisconnected: (cb: VoidCallback) => string;

  /**
   * Unregisters a callback that was previously registered with {@link onDisconnected}.
   *
   * @param id ID of callback to unregister.
   */
  readonly offDisconnected: (id: string) => void;

  /**
   * Registers a callback that will be called when the connection status with the agent changes.
   *
   * @param cb Invoked every time the connection status changes.
   * @returns ID to unregister the callback.
   * @see {@link offConnectionChange}
   */
  readonly onConnectionChange: (cb: (args: { connected: boolean }) => void) => string;

  /**
   * Unregisters a callback that was previously registered with {@link onConnectionChange}.
   *
   * @param id ID to unregister the callback.
   */
  readonly offConnectionChange: (id: string) => void;

  /**
   * Registers a callback that will be called when the application sends a `notification`.
   *
   * @param cb Invoked every time a `notification` is received.
   * @returns ID to unregister the callback.
   * @see {@link offNotification}
   */
  readonly onNotification: (cb: NotificationCallback) => string;

  /**
   * Unregisters a callback that was previously registered with {@link onNotification}.
   *
   * @param id ID to unregister the callback.
   */
  readonly offNotification: (id: string) => void;

  /**
   * Registers a callback that will be called when the application sends a `notification` with the specific key.
   *
   * @param key Key by which to filter notifications.
   * @param cb Invoked every time a `notification` with `key` is received.
   * @returns ID to unregister the callback.
   * @see {@link offNotificationWithKey}
   */
  readonly onNotificationWithKey: (key: string, cb: NotificationCallback) => string;

  /**
   * Unregisters a callback that was previously registered with {@link onNotificationWithKey}.
   *
   * @param id ID to unregister the callback.
   */
  readonly offNotificationWithKey: (id: string) => void;

  /**
   * Registers a callback that will be called when the application sends a `request`.
   * First callback to answer the request wins.
   *
   * @param cb Invoked every time a `request` is received. Must resolve to payload (response).
   * @returns ID to unregister the callback.
   * @see {@link offRequest}
   */
  readonly onRequest: (cb: RequestCallback) => string;

  /**
   * Unregisters a callback that was previously registered with {@link onRequest}.
   *
   * @param id ID to unregister the callback.
   */
  readonly offRequest: (id: string) => void;

  /**
   * TBD
   *
   * @param id
   * @param callback
   */
  readonly whenClicked: (id: string | string[], callback: (event: Event & { target: Element }) => void) => void;

  /**
   * Send a request to the application.
   *
   * @param payload A payload to send. Must be JSON-serializable.
   * @param uniqueKey A unique key to identify the request.
   * @param timeoutMs How long to wait for the response.
   * @returns A promise that resolves to the response.
   * @throws Error if timeout is reached.
   */
  readonly request: (payload: Payload, uniqueKey: string, timeoutMs?: number) => Promise<Payload>;

  /**
   * Send a notification to the application.
   *
   * @param uniqueKey A unique key to identify the notification.
   * @param payload A payload to send. Must be JSON-serializable.
   */
  readonly notify: (uniqueKey: string, payload: Payload) => void;
};
