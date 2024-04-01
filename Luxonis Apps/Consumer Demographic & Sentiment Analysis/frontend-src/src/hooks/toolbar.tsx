import { useContext } from "react";
import { ToolbarContext } from '../providers/ToolbarProvider';

export const useToolbar = () => {
  return useContext(ToolbarContext)
};
