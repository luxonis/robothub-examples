import { CanvasScopeContext } from "src/providers/CanvasScopeProvider";
import { useCanvas } from "./canvas";
import { useCallback, useContext } from "react";

export const useCanvasScope = () => {
  const canvasScope = useContext(CanvasScopeContext);
  const { interactingKey, setInteractingKey } = useCanvas();
  const { scopeKey } = canvasScope;

  const canInteract = useCallback(() => {
    return interactingKey === null || interactingKey === scopeKey;
  }, [interactingKey, scopeKey]);

  const cantInteract = useCallback(() => {
    return interactingKey !== null && interactingKey !== scopeKey;
  }, [interactingKey, scopeKey]);

  const takeInteraction = useCallback(() => {
    if (interactingKey === null) {
      setInteractingKey(scopeKey);
      return true;
    }
    return interactingKey === scopeKey;
  }, [interactingKey, setInteractingKey, scopeKey]);

  const releaseInteraction = useCallback(() => {
    if (interactingKey === scopeKey) {
      setInteractingKey(null);
      return true;
    }
    return interactingKey === null;
  }, [interactingKey, setInteractingKey, scopeKey]);

  return {
    ...canvasScope,
    canInteract,
    cantInteract,
    takeInteraction,
    releaseInteraction,
  };
};
