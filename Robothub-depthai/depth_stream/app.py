import robothub_depthai


class Application(robothub_depthai.RobotHubApplication):
    def on_start(self):
        for camera in self.unbooted_cameras:
            stereo = camera.create_stereo('800p', fps=30)

            # It will automatically create a stream and assign matching callback based on Component type
            camera.create_stream(component=stereo, unique_key=f'depth_{camera.id}', name=f'Depth stream {camera.id}')
