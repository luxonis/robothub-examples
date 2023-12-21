import { Button } from "@luxonis/theme/components/general/Button";
// import { TRACK_LABELS } from "../utils";
import { useToolbar } from "../../../hooks/toolbar";
import { TrackLabel } from "../types";
import { Flex } from "@luxonis/theme/components/general/Flex";
import { CSSProperties, useCallback } from "react";
// import { Badge } from "@luxonis/theme/components/general/Badge";
import { ToolbarItem } from "./ToolbarItem";
import { StyledText } from "@luxonis/theme/components/general/StyledText";
import { minifyNumber } from "src/utils/format";

const wrapperStyle: CSSProperties = {
  gap: 0,
  borderRadius: "5px",
  overflow: "hidden",
};

const infoNumberStyle: CSSProperties = {
  float: "right",
  marginLeft: "10px",
};

export const LabelSelector = () => {
  const { selectedLabel, linesStats } = useToolbar();

  // const getLabelDetections = useCallback(
  //   (label: TrackLabel) => {
  //     return minifyNumber(linesStats.detections[label.id] ?? 0);
  //   },
  //   [linesStats]
  // );

  const getTotalDetections = useCallback(
    () =>
      minifyNumber(
        Object.values(linesStats.detections).reduce((acc, val) => acc + val, 0)
      ),
    [linesStats]
  );

  const getButtonStyle = (label?: TrackLabel) => {
    const styles: CSSProperties = {
      border: 0,
      color: "black",
      borderRadius: 0,
      backgroundColor: "#fafafa",
    };

    if (label) {
      styles.backgroundColor =
        selectedLabel?.id === label?.id ? "#e0e0e0" : "#fafafa";
    }

    return styles;
  };

  return (
    <ToolbarItem left="10px" top="10px">
      <Flex>
        <Flex style={wrapperStyle}>
          <Button type="primary" style={getButtonStyle()} onClick={() => {}}>
            <StyledText
              style="text-xs"
              align="left"
              cssStyles={{ lineHeight: "14px" }}
            >
              Total Crossings
              <b style={infoNumberStyle}>{getTotalDetections()}</b>
              <br></br>
              Lines
              <b
                style={{
                  ...infoNumberStyle,
                  color: linesStats.total >= 20 ? "red" : "black",
                }}
              >
                {linesStats.total}
              </b>
            </StyledText>
          </Button>
        </Flex>

        {/* <Flex style={{ marginLeft: "8px", ...wrapperStyle }}>
          {TRACK_LABELS.map((label, index) => (
            <Button
              key={index}
              type="primary"
              style={getButtonStyle(label)}
              onClick={() => setSelectedLabel(label)}
            >
              <Badge color={label.color}>{getLabelDetections(label)}</Badge>
              {label.name}
            </Button>
          ))}
        </Flex> */}
      </Flex>
    </ToolbarItem>
  );
};
