import { useEffect, useState } from 'react';
import { LightModeOutlined } from '@mui/icons-material';
import { Box, Slider, Tab, Tabs, Typography } from '@mui/material';
import { apiService } from '../../../../services/api-service.js';
import { ColorPicker } from './utils/ColorPicker.js';
import { ConfigButton } from './utils/ConfigButton.js';
import { ConfigModal } from './utils/ConfigModal.js';

type Effect = { value: string; label: string };

const EFFECTS: Effect[] = [
  { value: 'car', label: 'Car' },
  { value: 'solid', label: 'Solid' },
  { value: 'spinner', label: 'Spinner' },
  { value: 'fan', label: 'Fan' },
  { value: 'pulse', label: 'Pulse' },
  { value: 'blink', label: 'Blink' },
];

const COLOR_LIST: string[] = [
  '#0000FF',
  '#800080',
  '#C71585',
  '#8A2BE2',
  '#008000',
  '#008B8B',
  '#FF0000',
  '#FF4500',
  '#FFA500',
  '#FFD700',
  '#ADFF2F',
  '#FFFFFF',
];

type NamedSliderProps = {
  text: string;
  min: number;
  max: number;
  value: number;
  setter: (state: number) => void;
};

const NamedSlider = (props: NamedSliderProps): JSX.Element => {
  const { text, min, max, value, setter } = props;

  const handleChange = (_event: Event, newValue: number | number[]) => {
    setter(Array.isArray(newValue) ? newValue[0] : newValue);
  };

  return (
    <Box display="flex" flexDirection="column" gap={1} alignItems="center" justifyContent="center" width="100%">
      <Typography variant="subtitle1" fontWeight={700} color="secondary">
        {text}
      </Typography>
      <Slider
        sx={{ mt: 2 }}
        step={1}
        min={min}
        max={max}
        value={value}
        onChange={handleChange}
        valueLabelDisplay="on"
      />
    </Box>
  );
};

export const LedConfig = (): JSX.Element => {
  const [visible, setVisible] = useState<boolean>(false);
  const [color, setColor] = useState<string>('#FFFFFF');
  const [effect, setEffect] = useState<string>('none');
  const [brightness, setBrightness] = useState<number>(50);
  const [spinnerBlades, setSpinnerBlades] = useState<number>(5);
  const [fanBlades, setFanBlades] = useState<number>(2);
  const [size, setSize] = useState<number>(3);
  const [interval, setInterval] = useState<number>(5);
  const [low, setLow] = useState<number>(25);
  const [high, setHigh] = useState<number>(75);

  const openModal = () => {
    setVisible(true);
  };

  const handleEffectChange = (_event: React.SyntheticEvent, newEffect: string) => setEffect(newEffect);

  useEffect(() => {
    const payload: any = {
      color,
      effect,
      brightness,
    };

    switch (effect) {
      case 'spinner':
        payload['size'] = size;
        payload['blades'] = spinnerBlades;
        break;
      case 'fan':
        payload['blades'] = fanBlades;
        payload['opening'] = 1;
        break;
      case 'pulse':
        payload['interval'] = interval;
        break;
      case 'blink':
        payload['high'] = high;
        payload['low'] = low;
        break;
    }
    if (effect !== 'none') {
      void apiService.request(payload, 'rae_control_leds', 15_000);
    }
  }, [color, effect, brightness, spinnerBlades, fanBlades, size, interval, low, high]);

  useEffect(() => setEffect(EFFECTS[0].value), []);

  return (
    <>
      <ConfigButton onClick={openModal} label="Lights" icon={<LightModeOutlined />} />
      <ConfigModal visible={visible} title="Edit Lights" onClose={() => setVisible(false)}>
        <Tabs
          value={effect}
          onChange={handleEffectChange}
          scrollButtons="auto"
          variant="scrollable"
          sx={{ maxWidth: { xs: 320, lg: 600, xl: 720 } }}
        >
          {EFFECTS.map(item => (
            <Tab key={item.value} {...item} />
          ))}
        </Tabs>
        <ColorPicker color={color} colors={COLOR_LIST} onChange={setColor} />
        <NamedSlider text="Brightness" min={0} max={100} value={brightness} setter={setBrightness} />

        {effect === 'spinner' && (
          <>
            <NamedSlider text="Number of blades" min={1} max={10} value={spinnerBlades} setter={setSpinnerBlades} />
            <NamedSlider text="Size of each blade" min={1} max={5} value={size} setter={setSize} />
          </>
        )}
        {effect === 'fan' && (
          <NamedSlider text="Number of blades" min={1} max={4} value={fanBlades} setter={setFanBlades} />
        )}
        {effect === 'pulse' && <NamedSlider text="Interval" min={1} max={10} value={interval} setter={setInterval} />}
        {effect === 'blink' && (
          <>
            <NamedSlider text="Off timer" min={0} max={100} value={low} setter={setLow} />
            <NamedSlider text="On timer" min={0} max={100} value={high} setter={setHigh} />
          </>
        )}
      </ConfigModal>
    </>
  );
};
