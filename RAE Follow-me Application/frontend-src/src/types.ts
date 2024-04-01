export type RobotHubNotification = {
  key: string;
  payload: AppData;
  broadcast: boolean;
};

export type AppData = {
  instances: Robot[];
  extra_topics: string[];
};

export type Payload = {
  returns: Payload;
};

export type Robot = {
  app_id: string;
  hostname: string;
  ip: string;
  internet: boolean;
  mtime: string;
  load: Load;
  cameras: Camera[];
  bags: Bag[];
};

export interface Request {
  payload: any;
  uniqueKey: string;
  timeoutMs: number;
  returns: Promise<Payload>;
}

export interface Bag {
  name: string;
  alive: boolean;
  topics: string[];
  files: File[];
}

export interface File {
  name: string;
  size: number;
  mtime: string;
  ctime: string;
}

export interface Camera {
  mxid: string;
  protocol: string;
  platform: string;
  product_name: string;
  board_name: string;
  board_rev: string;
  bootloader_version: string;
  state: string;
  sensors: Sensor[];
}

export interface Sensor {
  name: string;
  fps: number;
  resolution: string;
  available_resolutions: string[];
  stream_id: string;
  stream_url: string;
  stream_preview_id: string;
  stream_preview_url: string;
  logging_enabled: boolean;
  topics: string[];
}

export interface Load {
  cpu: number;
  cpu_max: number;
  ram: number;
  ram_max: number;
  disk: number;
  disk_max: number;
}

export type AppMode = 'manual' | 'follow_me';
