import { AppBar, Box, Chip } from '@mui/material';
import {
  Sensors,
  SensorsOff,
  ExploreOutlined,
  WifiOff,
  Wifi,
  Wifi2Bar,
  Wifi1Bar,
  Battery0Bar,
  Battery20,
  BatteryUnknown,
  Battery30,
  Battery50,
  Battery60,
  Battery80,
  Battery90,
  BatteryFull,
  Refresh,
} from '@mui/icons-material';
import { StatusBarItem } from './StatusBarItem.js';

type Icons = JSX.Element[];

const WIFI_ICONS: Icons = [
  <WifiOff key="wifi-icon-0" htmlColor="gray" />,
  <WifiOff key="wifi-icon-1" htmlColor="gray" />,
  <Wifi1Bar key="wifi-icon-2" htmlColor="gray" />,
  <Wifi2Bar key="wifi-icon-3" htmlColor="gray" />,
  <Wifi key="wifi-icon-4" htmlColor="gray" />,
];

const BATTERY_ICONS: Icons = [
  <BatteryUnknown key="batter-icon-0" htmlColor="gray" />,
  <Battery0Bar key="battery-icon-1" htmlColor="red" />,
  <Battery20 key="battery-icon-2" htmlColor="red" />,
  <Battery30 key="battery-icon-3" htmlColor="gray" />,
  <Battery50 key="battery-icon-4" htmlColor="gray" />,
  <Battery60 key="battery-icon-5" htmlColor="gray" />,
  <Battery80 key="battery-icon-6" htmlColor="gray" />,
  <Battery90 key="battery-icon-7" htmlColor="gray" />,
  <BatteryFull key="battery-icon-8" htmlColor="gray" />,
];

const getIcon = (value: number | undefined, max: number, icons: Icons): JSX.Element => {
  if (typeof value !== 'number' || value <= 0) {
    return icons[0];
  }

  if (value >= max) {
    return icons[icons.length - 1];
  }

  const iconLength = icons.length;
  const index = Math.floor((value / max) * (iconLength - 2)) + 1;

  return icons[index];
};

type StatusBarProps = {
  wifi?: number;
  wifiUnit?: string;
  battery?: number;
  isOnline?: boolean;
  isMapping?: boolean;
  isConnecting?: boolean;
};

export const StatusBar = (props: StatusBarProps): JSX.Element => {
  const { wifi, wifiUnit, battery, isOnline, isMapping, isConnecting } = props;

  return (
    <AppBar position="fixed" sx={{ top: 'auto', bottom: 0, bgcolor: 'white', color: 'black' }}>
      <Box display="flex" alignItems="center" justifyContent="end" padding="5px" gap="12px" marginLeft="80px">
        <StatusBarItem
          icon={getIcon(wifi, 20, WIFI_ICONS)}
          text={`${typeof wifi === 'number' ? wifi : '?'} ${wifiUnit}`}
        />
        <StatusBarItem
          icon={getIcon(battery, 100, BATTERY_ICONS)}
          text={typeof battery === 'number' ? `${battery} %` : '?'}
          sx={{ ml: 4 }}
        />

        <Box flexGrow="1"></Box>

        {isMapping && <Chip size="small" color="info" icon={<ExploreOutlined />} label="Mapping" />}
        {isConnecting ? (
          <Chip color="info" label="Trying to connect..." icon={<Refresh />} size="small" />
        ) : isOnline ? (
          <Chip color="success" label="Connected" icon={<Sensors />} size="small" />
        ) : (
          <Chip color="error" label="Disconnected" icon={<SensorsOff />} size="small" />
        )}
      </Box>
    </AppBar>
  );
};
