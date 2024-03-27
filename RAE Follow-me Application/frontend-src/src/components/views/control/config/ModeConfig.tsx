import { useEffect, useState } from 'react';
import { Button, Tab, Tabs, Typography } from '@mui/material';
import { Autorenew, ControlCameraOutlined } from '@mui/icons-material';
import type { AppMode } from '../../../../types.js';
import { apiService } from '../../../../services/api-service.js';
import { ConfigButton } from './utils/ConfigButton.js';
import { ConfigModal } from './utils/ConfigModal.js';

type Mode = {
  value: string;
  label: string;
};

const MODES: Mode[] = [
  { value: 'manual', label: 'Manual' },
  { value: 'follow_me', label: 'Follow me' },
];

type ModeConfigProps = {
  controls: 'joystick' | 'arrows';
  controlsHandler: () => void;
  mode: AppMode;
  setMode: (mode: AppMode) => void;
};

export const ModeConfig = (props: ModeConfigProps): JSX.Element => {
  const { controls, controlsHandler, mode, setMode } = props;
  const [visible, setVisible] = useState<boolean>(false);

  const openModal = () => {
    setVisible(true);
  };

  const handleModeChange = (_event: React.SyntheticEvent, newMode: AppMode) => setMode(newMode);

  useEffect(() => {
    const payload = {
      mode,
    };
    void apiService.request(payload, 'change_mode', 15_000);
  }, [mode]);

  return (
    <>
      <ConfigButton onClick={openModal} label="Mode" icon={<ControlCameraOutlined />} />
      <ConfigModal visible={visible} title="Edit Mode" onClose={() => setVisible(false)}>
        <Tabs value={mode || MODES[0].value} onChange={handleModeChange} aria-label="basic tabs example">
          {MODES.map(item => (
            <Tab key={item.value} {...item} />
          ))}
        </Tabs>
        {mode === 'manual' && (
          <>
            <Typography variant="subtitle1" fontWeight={700} color="secondary">
              Set a controller
            </Typography>
            <Button variant="contained" onClick={controlsHandler} endIcon={<Autorenew />} fullWidth>
              {controls}
            </Button>
          </>
        )}
      </ConfigModal>
    </>
  );
};
