import { Helmet } from 'react-helmet';
import { ControlContent } from '../components/views/control/ControlContent.js';

export default function ControlView(): JSX.Element {
  return (
    <>
      <Helmet>
        <title>Control</title>
      </Helmet>
      <ControlContent />
    </>
  );
}
