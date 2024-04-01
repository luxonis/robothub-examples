declare global {
  interface Window {
    ROBOT_APP_ID: string;
    ROBOT_APP_STATUS: status | undefined;
  }

  namespace JSX {
    interface IntrinsicElements {
      'rh-video': { 'stream-key': string };
    }
  }
}

declare module '@mui/material/styles' {
  interface Palette {
    title: Palette['title'];
  }

  interface PaletteOptions {
    title?: PaletteOptions['title'];
  }
}

declare module '@mui/material/Button' {
  interface ButtonPropsColorOverrides {
    title: true;
  }
}

export {};
