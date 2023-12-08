import { Card } from "@luxonis/theme/components/general/Card";
import { StyledText } from "@luxonis/theme/components/general/StyledText";
import { useToolbar } from "src/hooks/toolbar";
import { ToolbarItem } from "./ToolbarItem";
import { TRACK_LABELS } from "../utils";
import { useMemo } from "react";
import { timeAgo } from "src/utils/format";

export const LineDetail = () => {
  const { selectedLine, setSelectedLine } = useToolbar();

  const labelName = useMemo(() => {
    const labelId = selectedLine?.trackLabelId;
    if (!labelId) return "";
    const trackLabel = TRACK_LABELS.find((f) => f.id === labelId);
    return trackLabel ? trackLabel.name : "";
  }, [selectedLine]);

  const lastCrossAtText = useMemo(() => {
    if (!selectedLine || !selectedLine.lastCrossAt) return "---";
    return timeAgo(new Date(selectedLine.lastCrossAt * 1000));
  }, [selectedLine]);

  const handleClose = () => {
    setSelectedLine(null);
  };

  return (
    selectedLine && (
      <ToolbarItem bottom='10px' right='10px'>
        <Card>
          <RowItem name="Type:" value={labelName} />
          <RowItem name="Crossings:" value={selectedLine.count.toString()} />
          <RowItem name="Tracking enabled:" value={selectedLine.isDisabled ? "No" : "Yes"} />
          <RowItem name="Last cross:" value={lastCrossAtText} />

          <Card.Action onClick={handleClose} size="xs" fillWidth>
            Close
          </Card.Action>
        </Card>
      </ToolbarItem>
    )
  );
};

type RowItemProps = {
  name: string;
  value: string;
};

const RowItem = (props: RowItemProps) => {
  const { name, value } = props;

  return (
    <StyledText style="text-xs" cssStyles={{ lineHeight: "7px", textAlign: 'left' }}>
      {name} <b style={{ float: "right", marginLeft: "10px" }}>{value}</b>
    </StyledText>
  );
};
