import { Spinner as ThemeSpinner } from "@luxonis/theme/components/general/Spinner";
import { StyledText } from "@luxonis/theme/components/general/StyledText";
import { Flex } from "@luxonis/theme/components/general/Flex";
import { useCanvas } from "src/hooks/canvas";
import { CSSProperties, useMemo } from "react";
import { ToolbarItem } from "./ToolbarItem";

export const Spinner = () => {
  const { width, height } = useCanvas();

  const wrapperStyle = useMemo(() => {
    return {
      background: "rgba(0, 0, 0, .5)",
      width: width + "px",
      height: height + "px",
    } as CSSProperties;
  }, [width, height]);

  return (
    <ToolbarItem>
      <div style={wrapperStyle}>
        <Flex direction="column" style={{ height: "100%" }}>
          <ThemeSpinner centered onDark />
          <StyledText
            style="text-md"
            align="center"
            color={{ custom: "white" }}
          >
            Loading Canvas...
          </StyledText>
        </Flex>
      </div>
    </ToolbarItem>
  );
};
