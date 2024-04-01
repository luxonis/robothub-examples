import { Dropdown } from "@luxonis/theme/components/general/Dropdown";
import { useToolbar } from "../../../hooks/toolbar";
import { CSSProperties, useCallback, useEffect, useMemo, useRef } from "react";
import { ToolbarItem } from "./ToolbarItem";
import { SelectedLineOptionsItem } from "src/providers/ToolbarProvider";
import { getAbsoluteX, getAbsoluteY } from "src/utils/math";
import { useCanvas } from "src/hooks/canvas";

export const LineOptions = () => {
  const toolbar = useToolbar();
  const { width, height } = useCanvas();
  const { selectedLineOptions, closeLineOptions } = toolbar;
  const dropdownRef = useRef<HTMLDivElement | null>(null);

  const onItemClick = (item: SelectedLineOptionsItem) => {
    item.handler && item.handler();
    toolbar.setSelectedLine(null);
    closeLineOptions();
  };

  const onClickOutside = useCallback(
    (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        closeLineOptions();
      }
    },
    [closeLineOptions]
  );

  useEffect(() => {
    document.addEventListener("mousedown", onClickOutside);

    return () => {
      document.removeEventListener("mousedown", onClickOutside);
    };
  }, [onClickOutside]);

  const dropdownStyle = useMemo(() => {
    if (!selectedLineOptions) {
      return { display: "none" };
    }

    return {
      display: "flex",
      width: "fit-content",
      left: getAbsoluteX(width, selectedLineOptions.position.x) + "px",
      top: getAbsoluteY(height, selectedLineOptions.position.y) + "px",
    } as CSSProperties;
  }, [selectedLineOptions]);

  return (
    selectedLineOptions && (
      <ToolbarItem ref={dropdownRef}>
        <Dropdown style={dropdownStyle}>
          {selectedLineOptions.options.map((item, index) => (
            <Dropdown.Item
              icon={item.icon || <></>}
              key={index}
              text={item.label}
              onClick={() => onItemClick(item)}
            />
          ))}
        </Dropdown>
      </ToolbarItem>
    )
  );
};
