import { Box } from '@mui/material';
import { CirclePicker } from 'react-color';

type ColorPickerProps = {
  color: string;
  colors: string[];
  onChange: (hex: string) => void;
};

export const ColorPicker = (props: ColorPickerProps): JSX.Element => {
  const { color, colors, onChange } = props;

  return (
    <Box
      display="flex"
      width="100%"
      alignItems="center"
      justifyContent="center"
      padding={2}
      borderRadius="12px"
      sx={{ backgroundColor: 'rgba(0, 0, 0, 0.1)' }}
    >
      <CirclePicker
        colors={colors}
        color={color}
        onChangeComplete={(col: { hex: string }) => {
          onChange(col.hex);
        }}
      />
    </Box>
  );
};
