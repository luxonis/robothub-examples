import { idUtils } from "@luxonis/utility/id";
import { KonvaEventObject } from "konva/lib/Node";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Layer } from "react-konva";
import { useCanvas } from "../../../hooks/canvas";
import { useVideoStream } from "../../../hooks/videoStream";
import { LinesRenderer } from "./LinesRenderer";
import { useRobotHubApi } from "../../../hooks/robotHubApi";
import { useToolbar } from "../../../hooks/toolbar";
import { LineAgentData, LineData } from "./types";
import { TRACK_LABELS, hasTag } from "../utils";
import { isValidLine, prepareAgentLine } from "./utils";
import { LinesStats } from "src/providers/ToolbarProvider";

const MIN_LENGTH = 35;

type CanvasLinesProps = {};

export const Lines = (_props: CanvasLinesProps) => {
  const canvas = useCanvas();
  const toolbar = useToolbar();
  const { setLinesStats } = toolbar;
  const { isVideoReady, isDev, appConfig } = useVideoStream();
  const { request, notify } = useRobotHubApi();
  const { onEvent, offEvent, begPos, endPos, width, height } = canvas;

  const [lines, setLines] = useState<LineData[]>([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const canCreateLine = useMemo(() => {
    if (!appConfig || toolbar.isLoading) return false;
    if (lines.length < 20) return true;
  }, [lines, appConfig, toolbar]);

  const updateLines = useCallback(
    (updatedLines: LineAgentData[]) => {
      const newLines: LineData[] = [];

      for (const line of updatedLines) {
        const existingLine = lines.find((f) => f.id === line.id);

        if (existingLine) {
          existingLine.count = line.count;
          existingLine.isDisabled = line.isDisabled;
          existingLine.lastCrossAt = line.lastCrossAt;
          if (!existingLine.isDragging) {
            existingLine.x1 = line.x1;
            existingLine.y1 = line.y1;
            existingLine.x2 = line.x2;
            existingLine.y2 = line.y2;
          }
          continue;
        }

        const trackLabel = TRACK_LABELS.find((f) => f.id === line.trackLabelId);
        if (!trackLabel) continue;

        newLines.push({
          id: line.id,
          type: "line",
          trackLabelId: line.trackLabelId,
          detectionLabels: line.detectionLabels,
          color: trackLabel.color,
          count: line.count,
          isDisabled: false,
          hoverCornerIndex: null,
          lastCrossAt: line.lastCrossAt,
          x1: line.x1,
          y1: line.y1,
          x2: line.x2,
          y2: line.y2,
        });
      }

      setLines((prevLines) => [...prevLines, ...newLines]);
    },
    [lines]
  );

  const fetchLines = useCallback(async () => {
    try {
      const response = await request<{ entities: LineAgentData[] }>(
        "get_lines",
        {}
      );

      if (!response) return;

      toolbar.setIsLoading(false);
      updateLines(response.payload.result.entities);
    } catch (e) {
      console.error("Problem fetching lines from app", e);
    }
  }, [request, updateLines, toolbar]);

  const handleMouseDown = useCallback(
    ({ target, evt }: KonvaEventObject<MouseEvent>) => {
      if (evt.button !== 0 || isDragging || !canCreateLine) return;

      const name = target.name();
      if (name.length) {
        if (hasTag(name, "IGNORE_MOUSE_DOWN")) {
          canvas.resetPos();
          return;
        }
      }

      toolbar.setSelectedLine(null)

      setIsDrawing(true);
    },
    [isDragging, canvas, canCreateLine]
  );

  const handleMouseUp = useCallback(
    ({ evt }: KonvaEventObject<MouseEvent>) => {
      if (evt.button !== 0) return;

      setIsDrawing(false);
      setIsDragging(false);

      if (
        isDragging ||
        begPos == null ||
        endPos === null ||
        !toolbar.selectedLabel ||
        !canCreateLine
      ) {
        return;
      }

      const x1 = begPos.x;
      const y1 = begPos.y;
      const x2 = endPos.x;
      const y2 = endPos.y;
      if (!isValidLine(width, height, MIN_LENGTH, x1, y1, x2, y2)) {
        return;
      }

      const newLine: LineData = {
        id: idUtils.randomUuid(),
        type: "line",
        trackLabelId: toolbar.selectedLabel.id,
        detectionLabels: toolbar.selectedLabel.labels,
        color: toolbar.selectedLabel.color,
        count: 0,
        isDisabled: false,
        isDragging: false,
        isHovering: false,
        hoverCornerIndex: null,
        lastCrossAt: null,
        x1,
        y1,
        x2,
        y2,
      };

      setLines((prevLines) => [...prevLines, newLine]);
      canvas.resetPos();

      notify("create_line", prepareAgentLine(newLine));
    },
    [
      width,
      height,
      isDragging,
      canvas,
      toolbar,
      canCreateLine,
      begPos,
      endPos,
      notify,
    ]
  );

  useEffect(() => {
    if (isDev) {
      toolbar.setIsLoading(false);
      return;
    }

    // Periodicaly re-fetch lines
    let timer: NodeJS.Timer | null = null;
    if (isVideoReady && timer == null) {
      timer = setInterval(() => {
        if (!isVideoReady) return;
        fetchLines();
      }, 1000);
    }

    return () => {
      timer != null && clearInterval(timer);
    };
  }, [fetchLines, isVideoReady, toolbar, isDev]);

  useEffect(() => {
    onEvent("mouseDown", handleMouseDown);
    onEvent("mouseUp", handleMouseUp);

    return () => {
      offEvent("mouseDown", handleMouseDown);
      offEvent("mouseUp", handleMouseUp);
    };
  }, [onEvent, offEvent, handleMouseDown, handleMouseUp]);

  useEffect(() => {
    const detections: LinesStats["detections"] = {};
    lines.forEach((line) => {
      if (!detections[line.trackLabelId]) {
        detections[line.trackLabelId] = line.count;
      } else {
        detections[line.trackLabelId] += line.count;
      }
    });

    setLinesStats({ total: lines.length, detections });
  }, [setLinesStats, lines]);

  return (
    <Layer>
      <LinesRenderer
        minLength={MIN_LENGTH}
        lines={lines}
        isDragging={isDragging}
        isDrawing={isDrawing}
        onLinesChange={setLines}
        onIsDraggingChange={setIsDragging}
      />
    </Layer>
  );
};
