import robothub_depthai


class Application(robothub_depthai.RobotHubApplication):
    def on_start(self):
        for camera in self.unbooted_cameras:
            color = camera.create_camera('color', resolution='1080p', fps=30)
            nn = camera.create_nn('person-detection-retail-0013', input=color)

            # It will automatically create a stream and assign matching callback based on Component type
            camera.create_stream(component=nn,
                                 unique_key=f'nn_stream_{camera.id}',
                                 name=f'Detections stream {camera.id}')
