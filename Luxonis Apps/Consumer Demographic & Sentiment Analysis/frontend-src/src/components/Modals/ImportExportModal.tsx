import { Form } from "@luxonis/theme/components/general/Form";
import {
  Modal,
  ModalContextAware,
} from "@luxonis/theme/components/general/Modal";
import { useRequireMultiModalContext } from "@luxonis/theme/hooks/useMultiModal";
import { memo } from "react";
import { useRobotHubApi } from "src/hooks/robotHubApi";
import { AppModalsContext } from '../Layout';
import { LineAgentData } from '../Canvas/Lines/types';
import { saveAs } from "file-saver";

export const ImportExportModal = memo((): JSX.Element => {
  const context = useRequireMultiModalContext<AppModalsContext>();
  return (
    <ModalContextAware
      context={context}
      which="importExportModal"
      closable={true}
    >
      {(_, handleOnClose) => <ImportExportModalBody {...{ handleOnClose }} />}
    </ModalContextAware>
  );
});

const ImportExportModalBody = ({
  handleOnClose,
}: {
  handleOnClose: () => void;
}): JSX.Element => {
  const { notify, request} = useRobotHubApi();
  const uploadSourceForm = Form.useCreateForm({
    file: null,
  });

  const handleExport = async () => {
    const response = await request<{ entities: LineAgentData[] }>(
      "export_lines",
      {}
    );
    if (!response) return;

    const data = response.payload.result;
    const jsonBlob = new Blob([JSON.stringify(data)], {
      type: "application/json",
    });

    saveAs(jsonBlob, `app-counter-export.json`);
  };

  Form.useOnSubmit(
    uploadSourceForm,
    async ({ values }) => {
      try {
        const file = values.file("file");
        if (!file) {
          throw new Error("File not selected");
        }

        const importData = await file.text();
        notify("import_lines", { data: JSON.parse(importData) });
      } catch (e: any) {
        console.error("Failed uploading file", e);
      }

      handleOnClose();
    },
    []
  );

  return (
    <>
      <Modal.Header title="Import/Export Lines" closeAction />
      <Form
        form={uploadSourceForm}
        noPadding
        style="compact"
        encType="multipart/form-data"
        actions={
          <>
            <Form.Action type="submit">Import Lines</Form.Action>
            <Form.Action type="custom" onClick={handleExport}>Export Lines</Form.Action>
          </>
        }
      >
        <Form.Dropzone
          item={{
            name: "file",
          }}
          text={"Drag 'n' drop exported JSON file, or click here to select it"}
          accept={{
            "application/json": [],
          }}
        />
      </Form>
    </>
  );
};
