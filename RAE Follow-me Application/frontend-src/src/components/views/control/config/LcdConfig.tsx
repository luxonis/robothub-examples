import { useEffect, useState } from 'react';
import { Tab, Tabs, Typography } from '@mui/material';
import { SentimentSatisfiedAltOutlined } from '@mui/icons-material';
import { apiService } from '../../../../services/api-service.js';
import { ColorPicker } from './utils/ColorPicker.js';
import { ConfigButton } from './utils/ConfigButton.js';
import { ConfigModal } from './utils/ConfigModal.js';

type Face = {
  value: string;
  label: string;
};

const FACES: Face[] = [
  { value: 'happy', label: 'Happy' },
  { value: 'sad', label: 'Sad' },
  { value: 'angry', label: 'Angry' },
  { value: 'suspicious', label: 'Suspicious' },
];

const COLOR_LIST: string[] = [
  '#f2167c',
  '#f216d9',
  '#c016f2',
  '#5216f2',
  '#1682f2',
  '#16f2ef',
  '#16f261',
  '#9ef216',
  '#ebf216',
  '#f2b116',
  '#f26516',
  '#ffffff',
];

export const LcdConfig = (): JSX.Element => {
  const [visible, setVisible] = useState<boolean>(false);
  const [face, setFace] = useState<string | null>(null);
  const [faceColor, setFaceColor] = useState<string>('#FFFFFF');

  const openModal = () => {
    setVisible(true);
  };

  const handleFaceChange = (_event: React.SyntheticEvent, newFace: string) => setFace(newFace);

  useEffect(() => {
    if (face) {
      const payload = [
        {
          cmd: 'fill',
          color: faceColor,
        },
        {
          cmd: 'img',
          name: `face_${face}`,
          x: 0,
          y: 0,
        },
      ];
      void apiService.request(payload, 'rae_control_lcd', 15_000);
    }
  }, [face, faceColor]);

  return (
    <>
      <ConfigButton onClick={openModal} label="Face" icon={<SentimentSatisfiedAltOutlined />} />
      <ConfigModal title="Edit Face" visible={visible} onClose={() => setVisible(false)}>
        <Tabs value={face || FACES[0].value} onChange={handleFaceChange}>
          {FACES.map(item => (
            <Tab key={item.value} {...item} />
          ))}
        </Tabs>

        <Typography variant="subtitle1" fontWeight={700} color="secondary">
          Pick a color
        </Typography>

        <ColorPicker color={faceColor} colors={COLOR_LIST} onChange={setFaceColor} />
      </ConfigModal>
    </>
  );
};
