import React, { ReactNode, createContext, useCallback, useState } from "react";
import { TrackLabel } from "../components/Canvas/types";
import { TRACK_LABELS } from "../components/Canvas/utils";
import { Vector2d } from "konva/lib/types";
import { LineData } from "src/components/Canvas/Lines/types";

// Counter App
export type LinesStats = {
  total: number;
  detections: Record<string, number>;
};

type ToolbarLineData = {
  linesStats: LinesStats;
  selectedLabel: TrackLabel | null;
  selectedLine: LineData | null;
  selectedLineOptions: SelectedLineOptions | null;
  setLinesStats: (linesStats: LinesStats) => void;
  setSelectedLabel: (label: TrackLabel | null) => void;
  setSelectedLine: (line: LineData | null) => void;
  openLineOptions: (
    line: LineData,
    positon: Vector2d,
    options: SelectedLineOptionsItem[]
  ) => void;
  closeLineOptions: () => void;
};

export type SelectedLineOptionsItem = {
  label: string;
  icon?: ReactNode;
  handler?: () => void;
};

type SelectedLineOptions = {
  line: LineData;
  position: Vector2d;
  options: SelectedLineOptionsItem[];
};

// Base App
type ToolbarProps = {
  children: ReactNode;
};

interface ToolbarData extends ToolbarLineData {
  isLoading: boolean;
  isCanvasVisible: boolean;
  setIsLoading: (isLoading: boolean) => void;
  setIsCanvasVisible: (isCanvasVisible: boolean) => void;
}

export const ToolbarContext = createContext<ToolbarData>({
  selectedLabel: null,
  selectedLine: null,
  selectedLineOptions: null,
  isLoading: true,
  isCanvasVisible: true,
  linesStats: { total: 0, detections: {} },
  setLinesStats: () => {},
  setIsLoading: () => {},
  setSelectedLabel: () => {},
  setSelectedLine: () => {},
  setIsCanvasVisible: () => {},
  openLineOptions: () => {},
  closeLineOptions: () => {},
});

export const ToolbarProvider: React.FC<ToolbarProps> = (props) => {
  // Base App
  const [isLoading, setIsLoading] = useState(true);
  const [isCanvasVisible, setIsCanvasVisible] = useState(true);

  // Counter App
  const [linesStats, setLinesStats] = useState<LinesStats>({
    total: 0,
    detections: {},
  });

  const [selectedLabel, setSelectedLabel] = useState<TrackLabel | null>(
    TRACK_LABELS[0]
  );

  const [selectedLine, setSelectedLine] = useState<LineData | null>(null);
  const [selectedLineOptions, setSelectedLineOptions] =
    useState<SelectedLineOptions | null>(null);

  const openLineOptions = (
    line: LineData,
    position: Vector2d,
    options: SelectedLineOptionsItem[]
  ) => {
    // Move modal to left when needed so its not out of screen (@TODO: Better solution)
    if (position.x >= 0.8) {
      position.x -= 0.1;
    }
    if (position.y >= 0.8) {
      position.y -= 0.2;
    }

    setSelectedLine(line);
    setSelectedLineOptions({ line, position, options });
  };

  const closeLineOptions = useCallback(() => {
    setSelectedLineOptions(null);
  }, []);

  return (
    <ToolbarContext.Provider
      value={{
        selectedLabel,
        selectedLine,
        selectedLineOptions,
        isLoading,
        isCanvasVisible,
        linesStats,
        setLinesStats,
        setIsLoading,
        setSelectedLine,
        setSelectedLabel,
        setIsCanvasVisible,
        openLineOptions,
        closeLineOptions,
      }}
    >
      {props.children}
    </ToolbarContext.Provider>
  );
};
