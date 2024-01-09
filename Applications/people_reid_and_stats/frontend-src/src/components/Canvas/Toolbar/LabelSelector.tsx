import { useToolbar } from "../../../hooks/toolbar";
import { Flex } from "@luxonis/theme/components/general/Flex";
import {
  CSSProperties,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { ToolbarItem } from "./ToolbarItem";
import { minifyNumber } from "src/utils/format";
import { EMOJIS } from "./Faces";
import { useVideoStream } from "src/hooks/videoStream";
import { useCanvas } from "src/hooks/canvas";
import { NotificationCallback } from "src/hooks/api.types";

const infoNumberStyle: CSSProperties = {
  float: "right",
  marginLeft: "10px",
  color: "black",
};

type Stats = {
  age: number;
  males: number;
  females: number;
  happy: number;
  neutral: number;
  surprise: number;
  angry: number;
  sad: number;
};

const TEST_STATS: Stats = {
  age: 52.1,
  males: 92.2,
  females: 7.8,
  happy: 24.1,
  neutral: 62.3,
  surprise: 12.3,
  angry: 52.5,
  sad: 42.2,
};

export const LabelSelector = () => {
  const { width } = useCanvas();
  const { isDev } = useVideoStream();
  const { linesStats } = useToolbar();
  const [stats, setStats] = useState<Stats>({
    age: 0,
    males: 0,
    females: 0,
    happy: 0,
    neutral: 0,
    surprise: 0,
    angry: 0,
    sad: 0,
  });

  const wrapperStyle: CSSProperties = useMemo(
    () => ({
      gap: 0,
      borderRadius: "5px",
      width: `${width - 10}px`,
      background: "white",
      display: "flex",
      justifyContent: "space-between",
      padding: "10px 10px",
      flexDirection: "row",
      overflow: "hidden",
      fontSize: "1.3vw",
      fontWeight: "600",
      color: "#454545",
    }),
    [width]
  );

  useEffect(() => {
    if (isDev) {
      setStats(TEST_STATS);
      return;
    }

    const handler: NotificationCallback = (notification) => {
      const payload: any = notification.payload;
      if (payload && payload.stats) {
        setStats(payload.stats);
      }
    };

    window.robothubApi.onNotificationWithKey("faces", handler);
    return window.robothubApi.offNotificationWithKey("faces");
  }, []);

  const getTotalDetections = useCallback(
    () =>
      minifyNumber(
        Object.values(linesStats.detections).reduce((acc, val) => acc + val, 0)
      ),
    [linesStats]
  );

  return (
    <ToolbarItem left="10px" top="10px">
      <Flex style={wrapperStyle}>
        <div>
          Total Crossings
          <b style={infoNumberStyle}>{getTotalDetections()}</b>
        </div>

        <div>
          Lines:
          <b
            style={{
              ...infoNumberStyle,
              color: linesStats.total >= 20 ? "red" : "black",
            }}
          >
            {linesStats.total}
          </b>
        </div>

        <div>
          Avg. Age:
          <b style={infoNumberStyle}>{stats.age}</b>
        </div>

        <div>
          Males:
          <b style={infoNumberStyle}>{stats.males}%</b>
        </div>

        <div>
          Females:
          <b style={infoNumberStyle}>{stats.females}%</b>
        </div>

        <div>
          {EMOJIS.happy}:<b style={infoNumberStyle}>{stats.happy}%</b>
        </div>

        <div>
          {EMOJIS.neutral}:<b style={infoNumberStyle}>{stats.neutral}%</b>
        </div>

        <div>
          {EMOJIS.surprise}:<b style={infoNumberStyle}>{stats.surprise}%</b>
        </div>

        <div>
          {EMOJIS.angry}:<b style={infoNumberStyle}>{stats.angry}%</b>
        </div>

        <div>
          {EMOJIS.sad}:<b style={infoNumberStyle}>{stats.sad}%</b>
        </div>
      </Flex>
    </ToolbarItem>
  );
};
