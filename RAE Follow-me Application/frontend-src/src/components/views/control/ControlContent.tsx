import { useEffect, useRef, useState } from 'react';
import type { SxProps } from '@mui/material';
import { Box } from '@mui/material';
import { CampaignOutlined, ImageSearchOutlined } from '@mui/icons-material';
import type { AppMode } from '../../../types.js';
import { apiService } from '../../../services/api-service.js';
import type { StreamKey } from './Stream.js';
import { Stream } from './Stream.js';
import { Controller } from './controllers/Controller.js';
import { ConfigDrawer } from './config/ConfigDrawer.js';
import { RotateModal } from './RotateModal.js';
import { UIElement } from './UIElement.js';
import { VoiceRecord } from './controllers/VoiceRecord.js';

const STYLES: Record<string, SxProps> = {
  PRIMARY_STREAM: { display: 'flex', flexGrow: 1 },
  SECONDARY_STREAM: {
    display: 'flex',
    position: 'absolute',
    zIndex: 999,
    cursor: 'grab',
    top: '6%',
    left: '4%',
    width: '30%',
  },
};

export const ControlContent = (): JSX.Element => {
  const [primaryKey, setPrimaryKey] = useState<StreamKey>('stream_front');
  const [secondaryKey, setSecondaryKey] = useState<StreamKey>('stream_back');
  const [controls, setControls] = useState<'joystick' | 'arrows'>('joystick');
  const [mode, setMode] = useState<AppMode>('manual');
  const videoPlayerRef = useRef(null);

  const toggleStreams = () => {
    setPrimaryKey(secondaryKey);
    setSecondaryKey(secondaryKey === 'stream_front' ? 'stream_back' : 'stream_front');
  };

  const toggleControls = () => {
    setControls(controls === 'joystick' ? 'arrows' : 'joystick');
  };

  const triggerHorn = () => {
    void apiService.notify('rae_control_horn', {});
  };

  const triggerChat = () => {
    void apiService.notify('rae_chat_describe', {});
  };

  const sendAudio = (audioInBase64: string) => {
    void apiService.notify('rae_control_audio', { audio: audioInBase64 });
  };

  useEffect(() => {
    const resizeStream = () => {
      const wrapper = videoPlayerRef.current as HTMLDivElement | null;
      if (!wrapper || !wrapper.parentElement) {
        return;
      }

      const aspectRatio = 16 / 10;
      const parentHeight = wrapper.parentElement.clientHeight;
      const parentWidth = wrapper.parentElement.clientWidth;
      const isWide = parentWidth / parentHeight > aspectRatio;

      wrapper.style.height = `${isWide ? parentHeight : parentWidth / aspectRatio}px`;
      wrapper.style.width = `${isWide ? parentHeight * aspectRatio : parentWidth}px`;
    };

    resizeStream();

    window.addEventListener('resize', resizeStream);
    return () => window.removeEventListener('resize', resizeStream);
  }, []);

  return (
    <Box
      display="flex"
      flexDirection="column"
      flexGrow="1"
      alignItems="center"
      justifyContent="center"
      position="relative"
      height="100vh"
      overflow="hidden"
      sx={{ backgroundColor: '#44444F' }}
    >
      <RotateModal />

      {<ConfigDrawer controls={controls} controlsHandler={toggleControls} mode={mode} setMode={setMode} />}

      <Box display="flex" height="100%" width="100%" alignItems="center" justifyContent="center">
        <Box ref={videoPlayerRef} display="flex" position="relative">
          <UIElement onClick={triggerHorn} left="4%" bottom="8%" border={8}>
            <CampaignOutlined sx={{ color: 'white', fontSize: '100px' }} />
          </UIElement>

          <UIElement onClick={triggerChat} right="4%" top="4%" border={8}>
            <ImageSearchOutlined sx={{ color: 'white', fontSize: '100px' }} />
          </UIElement>

          <VoiceRecord onAudio={sendAudio} />

          <Stream sx={STYLES.PRIMARY_STREAM} streamKey={primaryKey} />

          {mode === 'manual' && (
            <Controller type={controls} front={primaryKey === 'stream_front'} onHornInput={triggerHorn} />
          )}
        </Box>
      </Box>

      <Stream streamKey={secondaryKey} draggable onClick={toggleStreams} sx={STYLES.SECONDARY_STREAM} />
    </Box>
  );
};
