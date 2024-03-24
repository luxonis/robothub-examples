import { Circle, Group, Line, Text } from "react-konva";
import {
  getAbsolutePoints,
  getAbsoluteX,
  getAbsoluteY,
  getRelativeX,
  getRelativeY,
  isInBounds,
} from "../../../utils/math";
import { minifyNumber } from "src/utils/format";
import { useCanvas } from "../../../hooks/canvas";
import { KonvaEventObject } from "konva/lib/Node";
import { Vector2d } from "konva/lib/types";
import { useRobotHubApi } from "../../../hooks/robotHubApi";
import { useToolbar } from "../../../hooks/toolbar";
import { LineData } from "./types";
import {
  getLinePointX,
  getLinePointY,
  isValidLine,
  prepareAgentLine,
} from "./utils";
import { tagName } from "../utils";
import { DatabaseSvg } from "@luxonis/icons/Database";
import { TrashSvg } from "@luxonis/icons/Trash";
import { useCanvasScope } from "src/hooks/canvasScope";
import { PlaySvg } from "@luxonis/icons/Play";
import { PauseSvg } from "@luxonis/icons/Pause";

interface CanvasLinesRendererProps {
  minLength: number;
  lines: LineData[];
  isDrawing: boolean;
  isDragging: boolean;
  onLinesChange: (lines: LineData[]) => void;
  onIsDraggingChange: (isDragging: boolean) => void;
}

export const LinesRenderer = (props: CanvasLinesRendererProps) => {
  const {
    minLength,
    lines,
    isDragging,
    isDrawing,
    onLinesChange,
    onIsDraggingChange,
  } = props;
  const canvas = useCanvas();
  const toolbar = useToolbar();
  const { setSelectedLine, selectedLine, selectedLabel } = toolbar;
  const { cantInteract, canInteract } = useCanvasScope();
  const { begPos, endPos, width, height } = canvas;
  const { notify } = useRobotHubApi();

  const handleLinePointDragStart = (
    line: LineData,
    pointIndex: number,
    _e: KonvaEventObject<MouseEvent>
  ) => {
    line.isDragging = true;
    onLinesChange([...lines]);
    onIsDraggingChange(true);

    setSelectedLine(line);

    // Snap to exact corner of line
    canvas.setBegPos({
      x: pointIndex ? line.x1 : line.x2,
      y: pointIndex ? line.y1 : line.y2,
    });
  };

  const handleLinePointDragMove = (
    _line: LineData,
    _pointIndex: number,
    { target }: KonvaEventObject<MouseEvent>
  ) => {
    onIsDraggingChange(true);

    canvas.setEndPosAsRel({ x: target.x(), y: target.y() });
  };

  const handleLinePointDragEnd = (
    line: LineData,
    pointIndex: number,
    { target }: KonvaEventObject<MouseEvent>
  ) => {
    const newX = getRelativeX(width, target.x());
    const newY = getRelativeY(height, target.y());

    onIsDraggingChange(false);
    canvas.resetPos();

    line.isDragging = false;

    const opositePointX = pointIndex ? line.x1 : line.x2;
    const opositePointY = pointIndex ? line.y1 : line.y2;

    const valid = isValidLine(
      width,
      height,
      minLength,
      newX,
      newY,
      opositePointX,
      opositePointY
    );

    // Move line to previous position if invalid
    if (!valid) {
      const currentPointX = pointIndex ? line.x2 : line.x1;
      const currentPointY = pointIndex ? line.y2 : line.y1;
      target.setPosition({ x: currentPointX, y: currentPointY });
      onLinesChange([...lines]);
      return;
    }

    // Update line to new position
    line[pointIndex ? "x2" : "x1"] = newX;
    line[pointIndex ? "y2" : "y1"] = newY;
    onLinesChange([...lines]);

    notify("update_line", prepareAgentLine(line));
  };

  const handleLinePointEnter = (
    line: LineData,
    pointIndex: number,
    _e: KonvaEventObject<MouseEvent>
  ) => {
    if (cantInteract()) return;

    line.isHovering = true;
    line.hoverCornerIndex = pointIndex;

    onLinesChange([...lines]);
  };

  const handleLinePointLeave = (
    line: LineData,
    _pointIndex: number,
    _e: KonvaEventObject<MouseEvent>
  ) => {
    line.hoverCornerIndex = null;
    onLinesChange([...lines]);
  };

  const handleLineMouseDown = (
    line: LineData,
    { evt }: KonvaEventObject<MouseEvent>
  ) => {
    if (evt.button !== 0) return;
    setSelectedLine(line);
  };

  const setLineHover = (line: LineData, isHovering: boolean) => {
    if (cantInteract()) return;
    line.isHovering = isHovering;
    onLinesChange([...lines]);
  };

  const getLineColor = (line: LineData) => {
    if (selectedLine?.id === line.id) return "white";
    return line.isDisabled ? "gray" : line.color;
  };

  const getPlaceholderLineColor = (vec1: Vector2d, vec2: Vector2d) => {
    const valid = isValidLine(
      width,
      height,
      minLength,
      vec1.x,
      vec1.y,
      vec2.x,
      vec2.y
    );
    if (!valid) {
      return "red";
    }
    if (isDrawing) {
      return selectedLabel?.color;
    }
    return "white";
  };

  const getLineCountColor = (line?: LineData) => {
    if (!line) return isDrawing ? "white" : "black";
    return selectedLine?.id === line.id ? "black" : "white";
  };

  const onOptions = (line: LineData, { evt }: KonvaEventObject<MouseEvent>) => {
    evt.preventDefault();

    const modalX = getRelativeX(width, evt.offsetX);
    const modalY = getRelativeY(height, evt.offsetY);

    toolbar.openLineOptions(line, { x: modalX, y: modalY }, [
      {
        label: line.isDisabled ? "Enable Tracking" : "Disable Tracking",
        icon: line.isDisabled ? <PlaySvg /> : <PauseSvg />,
        handler: () => {
          line.isDisabled = !line.isDisabled;
          onLinesChange([...lines]);
          notify("toggle_line", { id: line.id, isDisabled: line.isDisabled });
        },
      },
      {
        label: "Reset Counter",
        icon: <DatabaseSvg />,
        handler: () => {
          line.count = 0;
          notify("reset_line", line.id);
        },
      },
      {
        label: "Delete",
        icon: <TrashSvg />,
        handler: () => {
          onLinesChange([...lines.filter((f) => f.id !== line.id)]);
          notify("delete_line", line.id);
        },
      },
    ]);
  };

  return (
    <>
      {lines.map((line) => (
        <Group
          name="LINE"
          key={line.id}
          opacity={line.isDragging ? 0 : 1}
          onMouseEnter={() => setLineHover(line, true)}
          onMouseLeave={() => setLineHover(line, false)}
          onMouseDown={(e) => handleLineMouseDown(line, e)}
          onContextMenu={(e) => onOptions(line, e)}
        >
          <Line
            name={tagName("LINE_SHAPE", ["IGNORE_MOUSE_DOWN"])}
            points={getAbsolutePoints(width, height, [
              line.x1,
              line.y1,
              line.x2,
              line.y2,
            ])}
            stroke={getLineColor(line)}
            strokeWidth={4}
          />
          <Circle
            name={tagName("LINE_COUNT_SHAPE", ["IGNORE_MOUSE_DOWN"])}
            x={getAbsoluteX(width, (line.x1 + line.x2) / 2)}
            y={getAbsoluteY(height, (line.y1 + line.y2) / 2)}
            radius={14}
            fill={getLineColor(line)}
          />

          {[0, 1].map((index) => (
            <Group
              key={index}
              name="LINE_CORNERS"
              onMouseEnter={(e) => handleLinePointEnter(line, index, e)}
              onMouseLeave={(e) => handleLinePointLeave(line, index, e)}
            >
              <Circle
                name="LINE_CORNER_SHAPE"
                radius={6}
                fill={getLineColor(line)}
                x={getAbsoluteX(width, getLinePointX(line, index))}
                y={getAbsoluteY(height, getLinePointY(line, index))}
              />
              <Circle
                name="LINE_CORNER_HOVER_EFFECT"
                radius={14}
                opacity={line.hoverCornerIndex === index ? 0.3 : 0}
                x={getAbsoluteX(width, getLinePointX(line, index))}
                y={getAbsoluteY(height, getLinePointY(line, index))}
                fill={
                  isInBounds(
                    getLinePointX(line, 0),
                    getLinePointY(line, 0),
                    getLinePointX(line, 1),
                    getLinePointY(line, 1)
                  )
                    ? getLineColor(line)
                    : "red"
                }
              />
              <Circle
                name={tagName("LINE_POINT_HITBOX", ["IGNORE_MOUSE_DOWN"])}
                radius={14}
                draggable={canInteract()}
                opacity={0}
                strokeWidth={2}
                stroke="red"
                dash={line.hoverCornerIndex === index ? [] : [5]}
                x={getAbsoluteX(width, getLinePointX(line, index))}
                y={getAbsoluteY(height, getLinePointY(line, index))}
                onDragStart={(e) => handleLinePointDragStart(line, index, e)}
                onDragMove={(e) => handleLinePointDragMove(line, index, e)}
                onDragEnd={(e) => handleLinePointDragEnd(line, index, e)}
              />
            </Group>
          ))}
          <Text
            name={tagName("LINE_COUNT_VALUE", ["IGNORE_MOUSE_DOWN"])}
            x={getAbsoluteX(width, (line.x1 + line.x2) / 2) - 50}
            y={getAbsoluteY(height, (line.y1 + line.y2) / 2) - 50}
            text={minifyNumber(line.count || 0)}
            width={100}
            height={100}
            fontStyle="bold"
            align="center"
            verticalAlign="middle"
            fill={getLineCountColor(line)}
            listening={false}
          />
        </Group>
      ))}

      {(isDrawing || isDragging) && begPos && endPos && (
        <Group name="PLACEHOLDER_LINE">
          <Line
            name="PLACEHOLDER_LINE_SHAPE"
            points={getAbsolutePoints(width, height, [
              begPos.x,
              begPos.y,
              endPos.x,
              endPos.y,
            ])}
            stroke={getPlaceholderLineColor(endPos, begPos)}
            strokeWidth={4}
          />
          <Circle
            name="PLACEHOLDER_LINE_POINT_1"
            x={getAbsoluteX(width, begPos.x)}
            y={getAbsoluteY(height, begPos.y)}
            radius={6}
            fill={getPlaceholderLineColor(endPos, begPos)}
          />
          <Circle
            name="PLACEHOLDER_LINE_POINT_2"
            x={getAbsoluteX(width, endPos.x)}
            y={getAbsoluteY(height, endPos.y)}
            radius={6}
            fill={getPlaceholderLineColor(endPos, begPos)}
          />
          {isValidLine(
            width,
            height,
            minLength,
            begPos.x,
            begPos.y,
            endPos.x,
            endPos.y
          ) && (
            <>
              <Circle
                name="PLACEHOLDER_LINE_COUNT_SHAPE"
                x={getAbsoluteX(width, (begPos.x + endPos.x) / 2)}
                y={getAbsoluteY(height, (begPos.y + endPos.y) / 2)}
                radius={14}
                fill={getPlaceholderLineColor(endPos, begPos)}
              />
              <Text
                name="PLACEHOLDER_LINE_COUNT_VALUE"
                x={getAbsoluteX(width, (endPos.x + begPos.x) / 2) - 50}
                y={getAbsoluteY(height, (endPos.y + begPos.y) / 2) - 50}
                text={minifyNumber(selectedLine?.count || 0)}
                width={100}
                height={100}
                fontStyle="bold"
                align="center"
                verticalAlign="middle"
                fill={getLineCountColor()}
              />
            </>
          )}
        </Group>
      )}
    </>
  );
};
