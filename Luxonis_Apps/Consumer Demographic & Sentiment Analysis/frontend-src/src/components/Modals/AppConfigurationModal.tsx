import { Form } from "@luxonis/theme/components/general/Form";
import {
  Modal,
  ModalContextAware,
} from "@luxonis/theme/components/general/Modal";
import { useRequireMultiModalContext } from "@luxonis/theme/hooks/useMultiModal";
import { memo, useMemo } from "react";
import { useRobotHubApi } from "src/hooks/robotHubApi";
import { AppModalsContext } from "../Layout";
import { StyledText } from '@luxonis/theme/components/general/StyledText';
import { useVideoStream } from 'src/hooks/videoStream';

export const AppConfigurationModal = memo((): JSX.Element => {
  const context = useRequireMultiModalContext<AppModalsContext>();
  return (
    <ModalContextAware
      context={context}
      which="configurationModal"
      closable={true}
    >
      {(_, handleOnClose) => (
        <AppConfigurationModalBody {...{ handleOnClose }} />
      )}
    </ModalContextAware>
  );
});

const AppConfigurationModalBody = ({
  handleOnClose,
}: {
  handleOnClose: () => void;
}): JSX.Element => {
  const { notify } = useRobotHubApi();
  const { appConfig} = useVideoStream();
  const appConfigurationForm = Form.useCreateForm({
    nnTreshold: 0.6,
  });

  Form.useOnSubmit(
    appConfigurationForm,
    async ({ values }) => {
      try {
        const newConfig = {};
        notify("update_config", { config: newConfig });
      } catch (e: any) {
        console.error("Failed to save app configuration", e);
      }

      handleOnClose();
    },
    []
  );

  const robotHubAppConfigUrl = useMemo(() => {
    if (!appConfig) return '#';
    const { robotId, robotAppId } = appConfig;
    return `https://robothub.luxonis.com/robots/${robotId}/perception-apps/${robotAppId}`
  }, [appConfig])

  return (
    <>
      <Modal.Header title="App Configuration" subtitle={<StyledText style="text-sm">For all app settings, click <a href={robotHubAppConfigUrl} target="_blank">here</a> to access the RobotHub app configuration.</StyledText>} closeAction />
      <Form
        form={appConfigurationForm}
        noPadding
        style="compact"
        encType="multipart/form-data"
        actions={
          <>
            <Form.Action type="submit">Apply & Restart App</Form.Action>
          </>
        }
      >
      </Form>
    </>
  );
};
