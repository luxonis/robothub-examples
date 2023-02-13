import robothub_depthai


class Application(robothub_depthai.RobotHubApplication):
    def on_start(self):
        for camera in self.unbooted_cameras:
            color = camera.create_camera('color', resolution='1080p', fps=30)
            nn = camera.create_nn('person-detection-retail-0013', input=color)
            stereo = camera.create_stereo('800p', fps=30)

            # It will automatically create a stream and assign matching callback based on Component type
            camera.create_stream(component=color,
                                 unique_key=f'color_stream_{camera.id}',
                                 name=f'Color stream {camera.id}')
            camera.create_stream(component=nn,
                                 unique_key=f'nn_stream_{camera.id}',
                                 name=f'Detections stream {camera.id}')
            camera.create_stream(component=stereo,
                                 unique_key=f'depth_{camera.id}',
                                 name=f'Depth stream {camera.id}')
