import { useToolbar } from "../../../hooks/toolbar";
import { Flex } from "@luxonis/theme/components/general/Flex";
import { CSSProperties, useEffect, useMemo, useState } from "react";
import { EMOJIS } from "./Faces";
import { useVideoStream } from "src/hooks/videoStream";
import { useCanvas } from "src/hooks/canvas";
import { NotificationCallback } from "src/hooks/api.types";

const infoNumberStyle: CSSProperties = {
  float: "right",
  color: "black",
};

const emojiStyle: CSSProperties = {
  fontSize: "3.5vw",
  display: "block",
  width: "5vw",
  height: "5vw",
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
      width: "100%",
      marginTop: "5px",
      backgroundColor: "white",
      display: "flex",
      justifyContent: "space-around",
      padding: "20px 20px",
      flexDirection: "row",
      overflow: "hidden",
      fontSize: "1.8vw",
      fontWeight: "600",
      textAlign: "center",
      paddingRight: "50px",
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

  // const getTotalDetections = useCallback(
  //   () =>
  //     minifyNumber(
  //       Object.values(linesStats.detections).reduce((acc, val) => acc + val, 0)
  //     ),
  //   [linesStats]
  // );

  return (
    <>
      <Flex style={wrapperStyle}>
        <div
          style={{ width: "0.1vw", height: "100%", background: "#cfcfcf" }}
        ></div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <b style={{ ...infoNumberStyle, fontSize: "2.8vw" }}>{stats.age}</b>
          <span style={{ fontSize: "1.2vw" }}>Average Age</span>
        </div>

        <div style={{ display: "flex", justifyContent: "center", gap: "2vw" }}>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <b style={{ ...infoNumberStyle, color: "#299FE9" }}>
              {stats.males}%
            </b>
            <img
              src={process.env.PUBLIC_URL + "/assets/male.png"}
              style={{ width: "5vw", height: "5vw" }}
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column" }}>
            <b style={{ ...infoNumberStyle, color: "#F32C7D" }}>
              {stats.females}%
            </b>
            <img
              src={process.env.PUBLIC_URL + "/assets/female.png"}
              style={{ width: "5vw", height: "5vw" }}
            />
          </div>
        </div>

        <div
          style={{ width: "0.1vw", height: "100%", background: "#cfcfcf" }}
        ></div>

        <div style={{ display: "flex", justifyContent: "center", gap: "3vw" }}>
          <div style={{ display: "flex", flexDirection: "column" }}>
            {stats.happy}%<br />
            <span style={emojiStyle}>{EMOJIS.happy}</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column" }}>
            {stats.neutral}%<br />
            <span style={emojiStyle}>{EMOJIS.neutral}</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column" }}>
            {stats.surprise}%<br />
            <span style={emojiStyle}>{EMOJIS.surprise}</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column" }}>
            {stats.angry}%<br />
            <span style={emojiStyle}>{EMOJIS.angry}</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column" }}>
            {stats.sad}%<br />
            <span style={emojiStyle}>{EMOJIS.sad}</span>
          </div>
        </div>
      </Flex>
    </>
  );
};
