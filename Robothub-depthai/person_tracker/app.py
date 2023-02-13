import robothub
from depthai import TrackerType, TrackerIdAssignmentPolicy, Tracklet

import robothub_depthai

THRESHOLD = 0.25

tracked_objects = {}
counter = {'up': 0, 'down': 0, 'left': 0, 'right': 0}


def get_centroid(roi):
    x1 = roi.topLeft().x
    y1 = roi.topLeft().y
    x2 = roi.bottomRight().x
    y2 = roi.bottomRight().y
    return ((x2 - x1) / 2 + x1, (y2 - y1) / 2 + y1)


def tracklet_removed(tracklet, coords2):
    coords1 = tracklet['coords']
    deltaX = coords2[0] - coords1[0]
    deltaY = coords2[1] - coords1[1]

    if abs(deltaX) > abs(deltaY) and abs(deltaX) > THRESHOLD:
        direction = 'left' if 0 > deltaX else 'right'
        counter[direction] += 1
        print(f'Person moved {direction}')
    elif abs(deltaY) > abs(deltaX) and abs(deltaY) > THRESHOLD:
        direction = 'up' if 0 > deltaY else 'down'
        counter[direction] += 1
        print(f'Person moved {direction}')


def callback(packet, visualizer):
    for t in packet.daiTracklets.tracklets:
        # If new tracklet, save its centroid
        if t.status == Tracklet.TrackingStatus.NEW:
            tracked_objects[str(t.id)] = {}  # Reset
            tracked_objects[str(t.id)]['coords'] = get_centroid(t.roi)

        elif (t.status == Tracklet.TrackingStatus.REMOVED) and 'lost' not in tracked_objects[str(t.id)]:
            tracklet_removed(tracked_objects[str(t.id)], get_centroid(t.roi))

            robothub.COMMUNICATOR.notify(
                key='rhSchema/number',
                payload={'id': 'left', 'value': counter['left']}
            )
            robothub.COMMUNICATOR.notify(
                key='rhSchema/number',
                payload={'id': 'right', 'value': counter['right']}
            )
            robothub.COMMUNICATOR.notify(
                key='rhSchema/number',
                payload={'id': 'total', 'value': counter['left'] + counter['right']}
            )


class Application(robothub_depthai.RobotHubApplication):
    def on_start(self):
        for oak in self.unbooted_cameras:
            color = oak.create_camera('color', fps=10)
            nn = oak.create_nn('person-detection-retail-0013', color, tracker=True)

            nn.config_nn(aspect_ratio_resize_mode='stretch')
            nn.config_tracker(tracker_type=TrackerType.ZERO_TERM_COLOR_HISTOGRAM,
                              track_labels=[1],
                              assignment_policy=TrackerIdAssignmentPolicy.SMALLEST_ID)

            oak.create_stream(component=nn, unique_key=f'nn_stream_{oak.id}', name=f'Detections stream {oak.id}')
            oak.callback(nn.out.tracker, callback=callback)
