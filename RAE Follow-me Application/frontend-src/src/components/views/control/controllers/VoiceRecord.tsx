import { useEffect, useRef, useState } from 'react';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import { Mic } from '@mui/icons-material';
import { UIElement } from '../UIElement.js';

const MAX_VOICE_DURATION = 10; // Seconds

type VoiceRecordProps = {
  onAudio: (audioInBase64: string) => void;
};

export const VoiceRecord = (props: VoiceRecordProps): JSX.Element => {
  const { onAudio } = props;
  const [recording, setRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  useEffect(() => {
    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then(stream => {
        const recorder = new MediaRecorder(stream);
        mediaRecorderRef.current = recorder;

        const chunks: Blob[] = [];

        recorder.addEventListener('start', () => {
          setRecording(true);
        });

        recorder.addEventListener('dataavailable', event => {
          chunks.push(event.data);
        });

        recorder.addEventListener('stop', () => {
          setRecording(false);
          setRecordingDuration(0);

          if (chunks.length === 0) return;

          const audioBlob = new Blob(chunks, { type: 'audio/wav' });
          const reader = new FileReader();

          reader.onload = () => {
            const base64String = reader.result?.toString().split(',')[1];
            if (base64String === undefined || base64String.length === 0) return;
            onAudio(base64String);
          };

          reader.readAsDataURL(audioBlob);
        });

        recorder.addEventListener('error', error => {
          setRecording(false);
          setRecordingDuration(0);
          console.error('Error recording audio:', error);
        });
      })
      .catch(error => {
        console.error('Error accessing microphone:', error);
      });
  }, [onAudio]);

  useEffect(() => {
    const handleRecordingLoop = () => {
      if (!recording) return;

      if (recordingDuration >= MAX_VOICE_DURATION) {
        stopRecording();
        return;
      }

      setRecordingDuration(prevDuration => prevDuration + 0.05);
    };

    const recordingLoop = setInterval(handleRecordingLoop, 50);
    return () => clearInterval(recordingLoop);
  }, [recording, recordingDuration]);

  const startRecording = () => {
    mediaRecorderRef.current?.start();
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
  };

  return (
    <>
      <UIElement
        left="4%"
        top="4%"
        onDown={startRecording}
        onUp={stopRecording}
        sx={{ borderColor: recording ? 'red' : 'white' }}
      >
        <div style={{ position: 'relative', width: 100, height: 100 }}>
          {recording && (
            <CircularProgressbar
              styles={buildStyles({ pathColor: 'red', trailColor: 'white' })}
              minValue={0}
              maxValue={10}
              value={recordingDuration}
            />
          )}
          <Mic
            sx={{
              position: 'absolute',
              left: '10px',
              top: '10px',
              fontSize: '80px',
              color: recording ? 'red' : 'white',
            }}
          />
        </div>
      </UIElement>
    </>
  );
};
