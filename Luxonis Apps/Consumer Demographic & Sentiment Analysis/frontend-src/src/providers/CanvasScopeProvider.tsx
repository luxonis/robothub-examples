import React, { ReactNode, createContext } from "react";

type CanvasSchopeProps = {
  children: ReactNode;
  scopeKey: string;
};

export type CanvasScopeData = {
  scopeKey: string;
};

export const CanvasScopeContext = createContext<CanvasScopeData>({
  scopeKey: "",
});

export const CanvasScopeProvider: React.FC<CanvasSchopeProps> = ({
  children,
  scopeKey,
}) => (
  <CanvasScopeContext.Provider
    value={{
      scopeKey,
    }}
  >
    {children}
  </CanvasScopeContext.Provider>
);
