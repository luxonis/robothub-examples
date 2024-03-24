import { Button } from "@luxonis/theme/components/general/Button";
import { ToolbarItem } from "./ToolbarItem";
import { useToolbar } from "src/hooks/toolbar";
import { VisibleSvg } from "src/icons/Visible";
import { InvisibleSvg } from "src/icons/Invisible";

export const HideCanvasButton = () => {
  const { isCanvasVisible, setIsCanvasVisible } = useToolbar();

  const toggle = () => {
    setIsCanvasVisible(!isCanvasVisible);
  };

  return (
    <ToolbarItem top="10px" right="10px">
      <Button onClick={toggle} type="primary">
        {isCanvasVisible ? <InvisibleSvg /> : <VisibleSvg /> }
      </Button>
    </ToolbarItem>
  );
};
