import { PageContent } from "@luxonis/theme/components/general/PageContent";
import { VideoStream } from "../VideoStream";

export const AppRoute = () => {
  return (
    <PageContent noPadding>
      <VideoStream uniqueKey="color" />
    </PageContent>
  );
};
