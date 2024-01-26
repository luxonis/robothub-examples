import { Layout as ThemeLayout } from "@luxonis/theme/components/general/Layout";
import { Outlet } from "@remix-run/react";
import { StyledText } from "@luxonis/theme/components/general/StyledText";
import { useVideoStream } from "src/hooks/videoStream";
import { VideoStreamProvider } from "src/providers/VideoStreamProvider";
import { memo } from "react";
import {
  ModalContext,
  MultiModalContextProvider,
  useNewMultiModalContext,
} from "@luxonis/theme/hooks/useMultiModal";
import { ImportExportModal } from "./Modals/ImportExportModal";
import { AppConfigurationModal } from "./Modals/AppConfigurationModal";
import { LabelSelector } from "./Canvas/Toolbar/LabelSelector";
import { Box } from "@luxonis/theme/components/general/Box";

export type AppModalsContext = {
  importExportModal: Record<string, never>;
  configurationModal: Record<string, never>;
};

export const Layout = () => {
  const modalContext = useNewMultiModalContext<AppModalsContext>();

  return (
    <ThemeLayout mainMenu={[]} showMainMenu={false}>
      <VideoStreamProvider>
        <div
          style={{
            width: "100vw",
            height: "100vh",
            display: "flex",
            overflow: "hidden",
            flexDirection: "column",
          }}
        >
          <Header modalContext={modalContext} />
          <Outlet />
        </div>

        <MultiModalContextProvider context={modalContext}>
          <ImportExportModal />
          <AppConfigurationModal />
        </MultiModalContextProvider>
      </VideoStreamProvider>
    </ThemeLayout>
  );
};

const Header = memo(
  ({}: { modalContext: ModalContext<AppModalsContext> }) => {
    const { appConfig } = useVideoStream();

    // const handleRobotHubRedirect = () => {
    //   if (!appConfig) return;
    //   const { robotId, robotAppId } = appConfig;

    //   window.open(
    //     `https://robothub.luxonis.com/robots/${robotId}/perception-apps/${robotAppId}`
    //   );
    // };

    return (
      <div>
        <div
          style={{
            display: "flex",
            justifyContent: "space-around",
          }}
        >
          <Box
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              alignSelf: "center",
              marginTop: "auto",
              marginBottom: "auto",
              padding: "15px",
            }}
          >
            <div style={{ width: "15vh" }}>
              <img
                style={{ objectFit: "contain", display: "block" }}
                src={process.env.PUBLIC_URL + "/assets/qr-code.png"}
                alt="Luxonis website"
              />
            </div>
          </Box>
          <div
            style={{
              width: "35vh",
              textAlign: "center",
              alignSelf: "center",
              padding: "15px",
              display: 'flex',
              flexDirection: 'column'
            }}
          >
            <img
              style={{ objectFit: "contain", display: "inline-block" }}
              src={process.env.PUBLIC_URL + "/assets/luxonis_logo.png"}
              alt="Luxonis logo"
            />
            <StyledText
              style="text-md"
              cssStyles={{
                textAlign: "center",
                fontSize: "1vw",
                fontWeight: "600",
                marginTop: '5%'
              }}
            >
              <div>Consumer demographic</div>
              <div>•</div>
              <div>Sentiment analysis</div>
            </StyledText>
          </div>

          <LabelSelector />
        </div>
      </div>
    );
  }
);
