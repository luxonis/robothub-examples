import { Layout as ThemeLayout } from "@luxonis/theme/components/general/Layout";
import { Outlet } from "@remix-run/react";
import { PageHeader } from "@luxonis/theme/components/general/PageHeader";
import { StyledText } from "@luxonis/theme/components/general/StyledText";
import { Badge } from "@luxonis/theme/components/general/Badge";
import { Flex } from "@luxonis/theme/components/general/Flex";
import { useVideoStream } from "src/hooks/videoStream";
import { VideoStreamProvider } from "src/providers/VideoStreamProvider";
import { MoreMenu } from "@luxonis/theme/components/general/MoreMenu";
import { RobotSvg } from "@luxonis/icons/Robot";
import { memo } from "react";
import { Button } from "@luxonis/theme/components/general/Button";
import {
  ModalContext,
  MultiModalContextProvider,
  useNewMultiModalContext,
} from "@luxonis/theme/hooks/useMultiModal";
import { ImportExportModal } from "./Modals/ImportExportModal";
import { AppConfigurationModal } from "./Modals/AppConfigurationModal";
// import { SettingsSvg } from "@luxonis/icons/Settings";
import { DatabaseSvg } from "@luxonis/icons/Database";

export type AppModalsContext = {
  importExportModal: Record<string, never>;
  configurationModal: Record<string, never>;
};

export const Layout = () => {
  const modalContext = useNewMultiModalContext<AppModalsContext>();

  return (
    <ThemeLayout mainMenu={[]} showMainMenu={false}>
      <VideoStreamProvider>
        <Header modalContext={modalContext} />

        <Outlet />

        <MultiModalContextProvider context={modalContext}>
          <ImportExportModal />
          <AppConfigurationModal />
        </MultiModalContextProvider>
      </VideoStreamProvider>
    </ThemeLayout>
  );
};

const Header = memo(
  ({ modalContext }: { modalContext: ModalContext<AppModalsContext> }) => {
    const { appConfig } = useVideoStream();

    const handleRobotHubRedirect = () => {
      if (!appConfig) return;
      const { robotId, robotAppId } = appConfig;

      window.open(
        `https://robothub.luxonis.com/robots/${robotId}/perception-apps/${robotAppId}`
      );
    };

    return (
      <PageHeader
        title={<HeaderTitle />}
        extra={
          <>
            {/* <Button type="secondary" iconEnd={<SettingsSvg />} onClick={() => modalContext.open("configurationModal", {})}>
              Configuration
            </Button> */}
            <Button
              type="secondary"
              iconEnd={<DatabaseSvg />}
              onClick={() => modalContext.open("importExportModal", {})}
            >
              Import/Export Lines
            </Button>

            <MoreMenu>
              <MoreMenu.Item
                text="App In RobotHub"
                icon={<RobotSvg />}
                onClick={handleRobotHubRedirect}
              />
            </MoreMenu>
          </>
        }
      />
    );
  }
);

const HeaderTitle = memo(() => {
  const { status } = useVideoStream();

  const getBadge = () => {
    switch (status) {
      case "connecting":
        return <Badge color="orange">Connecting</Badge>;
      case "running":
        return <Badge color="success">Running</Badge>;
      case "stopped":
        return <Badge color="error">Stopped</Badge>; // Not working currently
    }
  };

  return (
    <Flex>
      <StyledText
        style="text-lg"
        weight="medium"
        cssStyles={{ marginRight: "5px" }}
      >
        App Counter
      </StyledText>
      {getBadge()}
    </Flex>
  );
});
