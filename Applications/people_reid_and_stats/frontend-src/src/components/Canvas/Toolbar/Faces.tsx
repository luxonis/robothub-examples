import { ToolbarItem } from "./ToolbarItem";
import { Box } from "@luxonis/theme/components/general/Box";
import { Flex } from "@luxonis/theme/components/general/Flex";
import { useCanvas } from "src/hooks/canvas";
import { StyledText } from "@luxonis/theme/components/general/StyledText";
import { useEffect, useState } from "react";
import { NotificationCallback } from "src/hooks/api.types";
import { useVideoStream } from "src/hooks/videoStream";

const PUBLIC_URL = process.env.PUBLIC_URL;
const IMG_PLACEHOLDER_PATH = PUBLIC_URL + "/placeholders/empty.jpg";

type Gender = "male" | "female";
type Emotion = "happy" | "angry" | "neutral" | "sad" | "surprise";

type Face = {
  id?: string;
  gender?: Gender;
  emotion?: Emotion;
  img_path?: string;
  age?: number;
};

const EMOJIS: Record<Emotion, string> = {
  happy: "😁",
  angry: "😠",
  sad: "🙁",
  neutral: "😐",
  surprise: "😮",
};

const COLORS: Record<Emotion, string> = {
  happy: "lime",
  angry: "red",
  sad: "yellow",
  neutral: "blue",
  surprise: "orange",
};

const TEST_FACES: Record<string, Face> = {
  face_1: {
    id: "1",
    img_path: PUBLIC_URL + "/placeholders/cat.jpg",
    emotion: "angry",
    age: 25,
    gender: "female",
  },
  face_2: {
    id: "2",
    img_path: PUBLIC_URL + "/placeholders/cat.jpg",
    emotion: "neutral",
    age: 63,
    gender: "male",
  },
  face_3: {
    id: "3",
    img_path: PUBLIC_URL + "/placeholders/cat.jpg",
    emotion: "happy",
    age: 6,
    gender: "female",
  },
  face_4: {},
};

export const Faces = () => {
  const canvas = useCanvas();
  const { isDev } = useVideoStream();
  const [faces, setFaces] = useState<Record<string, Face>>({});

  const getEmoji = (face: Face) => (face.emotion ? EMOJIS[face.emotion] : "");
  const getColor = (face: Face) => {
    return face.emotion ? COLORS[face.emotion] : "white";
  };
  const getTitle = (face: Face) => {
    return face.gender && face.age ? `${face.gender} (${face.age})` : "Empty";
  };

  useEffect(() => {
    if (isDev) {
      setFaces(TEST_FACES);
      return;
    }

    const handler: NotificationCallback = (notification) => {
      const payload: any = notification.payload;
      if (payload && payload.faces) {
        setFaces(payload.faces as Record<string, Face>);
      }
    };

    window.robothubApi.onNotificationWithKey("faces", handler);
    return window.robothubApi.offNotificationWithKey("faces");
  }, []);

  return (
    <ToolbarItem top="0px" right="0px" ignoreStreamWidth>
      <Flex
        style={{
          height: canvas.height,
          justifyContent: "start",
          marginRight: "10px",
          gap: "0px",
        }}
        direction="column"
      >
        {Object.values(faces).map((face, index) => {
          return (
            <Box
              key={index}
              style={{
                position: "relative",
                borderRadius: "10%",
                border: `0.4vw solid ${getColor(face)}`,
                height: `${canvas.height / 4 - 14}px`,
                marginTop: "10px",
                overflow: "hidden",
              }}
            >
              <StyledText
                style="display-lg"
                cssStyles={{
                  fontSize: "2vw",
                  lineHeight: 0,
                  position: "absolute",
                  left: "1%",
                  top: "15%",
                }}
              >
                {getEmoji(face)}
              </StyledText>
              <img src={face.img_path || IMG_PLACEHOLDER_PATH} height="100%" />
              <Flex
                style={{
                  position: "absolute",
                  bottom: 0,
                  right: 0,
                  background: "white",
                  width: "100%",
                  padding: "0.4vw",
                  lineHeight: "2px",
                }}
              >
                <div
                  style={{
                    position: "absolute",
                    left: 0,
                    top: 0,
                    opacity: 0.1,
                    backgroundColor: getColor(face),
                    zIndex: 1,
                    width: "100%",
                    height: "100%",
                  }}
                ></div>
                <Flex
                  style={{ zIndex: 2, width: "100%" }}
                  mainAlign="space-between"
                >
                  <StyledText
                    style="text-xl"
                    weight="bold"
                    cssStyles={{
                      fontSize: "1vw",
                      textTransform: "capitalize",
                      color: "#1D1D1D",
                      lineHeight: "1em",
                    }}
                  >
                    {getTitle(face)}
                  </StyledText>
                  <StyledText
                    style="text-sm"
                    cssStyles={{ fontSize: "0.7vw", lineHeight: "1em" }}
                  >
                    {face.id ? `#${face.id}` : ""}
                  </StyledText>
                </Flex>
              </Flex>
            </Box>
          );
        })}
      </Flex>
    </ToolbarItem>
  );
};
