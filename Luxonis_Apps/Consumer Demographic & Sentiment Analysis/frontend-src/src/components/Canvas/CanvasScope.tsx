import { ReactNode } from "react";
import { CanvasScopeProvider } from "src/providers/CanvasScopeProvider";

type CanvasScopeProps = {
  children: ReactNode;
  scopeKey: string;
};

export const CanvasScope = ({ scopeKey, children }: CanvasScopeProps) => {
  return (
    <CanvasScopeProvider scopeKey={scopeKey}>{children}</CanvasScopeProvider>
  );
};
