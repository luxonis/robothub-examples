import robothub_depthai


class DefaultApplication(robothub_depthai.RobotHubApplication):
    def on_start(self):
        for camera in self.unbooted_cameras:
            color_resolution = '1080p'
            mono_resolution = '400p'

            if camera.has_color:
                print(f'Initialized color stream with resolution: {color_resolution}')
                color = camera.create_camera('color', resolution=color_resolution, fps=30)
                camera.create_stream(component=color, unique_key=f'color_{camera.id}', name=f'Color stream {camera.id}')

            if camera.has_stereo:
                print(f'Initialized depth stream with resolution: {mono_resolution}')
                stereo = camera.create_stereo(resolution=mono_resolution, fps=30)
                camera.create_stream(component=stereo, unique_key=f'depth_{camera.id}', name=f'Depth stream {camera.id}')
