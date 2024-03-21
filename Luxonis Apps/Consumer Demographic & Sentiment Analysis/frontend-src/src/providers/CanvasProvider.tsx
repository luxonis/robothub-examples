import { Vector2d } from "konva/lib/types";
import React, {
  ReactNode,
  createContext,
  useCallback,
  useRef,
  useState,
} from "react";

type CanvasProps = {
  children: ReactNode;
  width: number;
  height: number;
  offset: Vector2d;
};

export type CanvasData = {
  width: number;
  height: number;
  offset: Vector2d;
  begPos: Vector2d | null;
  endPos: Vector2d | null;
  interactingKey: string | null;
  setInteractingKey: (key: string | null) => void;
  setBegPos: (pos: Vector2d | null) => void;
  setEndPos: (pos: Vector2d | null) => void;
  onEvent: (eventKey: string, handler: any) => void;
  offEvent: (eventKey: string, handler: any) => void;
  triggerEvent: (eventKey: string, handler: any) => void;
};

export const CanvasContext = createContext<CanvasData>({
  width: 0,
  height: 0,
  offset: { x: 0, y: 0 },
  begPos: null,
  endPos: null,
  interactingKey: null,
  setInteractingKey: () => {},
  setBegPos: () => {},
  setEndPos: () => {},
  onEvent: () => {},
  offEvent: () => {},
  triggerEvent: () => {},
});

export const CanvasProvider: React.FC<CanvasProps> = ({
  children,
  width,
  height,
  offset,
}) => {
  const [begPos, setBegPos] = useState<Vector2d | null>(null);
  const [endPos, setEndPos] = useState<Vector2d | null>(null);
  const [interactingKey, setInteractingKey] = useState<string | null>(null);

  const events = useRef<any>({ mouseDown: [], mouseMove: [], mouseUp: [] });

  const onEvent = useCallback((eventKey: string, handler: any) => {
    events.current[eventKey].push(handler);
  }, []);

  const offEvent = useCallback((eventKey: string, handler: any) => {
    events.current[eventKey] = events.current[eventKey].filter(
      (h: any) => h !== handler
    );
  }, []);

  const triggerEvent = useCallback((...args: any[]) => {
    const handlerArguments = [...args];
    handlerArguments.shift();
    events.current[args[0]].forEach((handler: any) =>
      handler(...handlerArguments)
    );
    events.current[args[0]] = [];
  }, []);

  return (
    <CanvasContext.Provider
      value={{
        width,
        height,
        offset,
        begPos,
        endPos,
        interactingKey,
        setInteractingKey,
        setBegPos,
        setEndPos,
        onEvent,
        offEvent,
        triggerEvent,
      }}
    >
      {children}
    </CanvasContext.Provider>
  );
};
