import depthai as dai
import numpy as np


def rotate_point(pointX, pointY, originX, originY, angle):
    angle = angle * np.pi / 180.0
    x = (
        np.cos(angle) * (pointX - originX)
        - np.sin(angle) * (pointY - originY)
        + originX
    )
    y = (
        np.sin(angle) * (pointX - originX)
        + np.cos(angle) * (pointY - originY)
        + originY
    )
    return x, y


def get_rotated_rect_points(bbox: np.ndarray, angle: float):
    x0, y0, x1, y1 = bbox
    points = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    rotated_points = [
        rotate_point(p[0], p[1], x1, y1, np.rad2deg(angle)) for p in points
    ]
    return np.asarray(rotated_points)


def non_max_suppression(
    boxes: np.ndarray, probs=None, angles=None, overlap_threshold=0.3
):
    # if there are no boxes, return an empty list
    if len(boxes) == 0:
        return [], []

    # if the bounding boxes are integers, convert them to floats -- this
    # is important since we'll be doing a bunch of divisions
    if boxes.dtype.kind == "i":
        boxes = boxes.astype("float")

    # initialize the list of picked indexes
    pick = []

    # grab the coordinates of the bounding boxes
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    # compute the area of the bounding boxes and grab the indexes to sort
    # (in the case that no probabilities are provided, simply sort on the bottom-left y-coordinate)
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = y2

    # if probabilities are provided, sort on them instead
    if probs is not None:
        idxs = probs

    # sort the indexes
    idxs = np.argsort(idxs)

    # keep looping while some indexes still remain in the indexes list
    while len(idxs) > 0:
        # grab the last index in the indexes list and add the index value to the list of picked indexes
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)

        # find the largest (x, y) coordinates for the start of the bounding box and the smallest (x, y) coordinates for the end of the bounding box
        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])

        # compute the width and height of the bounding box
        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)

        # compute the ratio of overlap
        overlap = (w * h) / area[idxs[:last]]

        # delete all indexes from the index list that have overlap greater than the provided overlap threshold
        idxs = np.delete(
            idxs, np.concatenate(([last], np.where(overlap > overlap_threshold)[0]))
        )

    # return only the bounding boxes that were picked
    return boxes[pick].astype("int"), angles[pick]


def decode_predictions(
    scores: np.ndarray,
    geometry1: np.ndarray,
    geometry2: np.ndarray,
    conf_threshold: float = 0.5,
):
    # grab the number of rows and columns from the scores volume, then
    # initialize our set of bounding box rectangles and corresponding
    # confidence scores
    (numRows, numCols) = scores.shape[2:4]
    rects = []
    confidences = []
    angles = []

    # loop over the number of rows
    for y in range(0, numRows):
        # extract the scores (probabilities), followed by the
        # geometrical data used to derive potential bounding box
        # coordinates that surround text
        scoresData = scores[0, 0, y]
        xData0 = geometry1[0, 0, y]
        xData1 = geometry1[0, 1, y]
        xData2 = geometry1[0, 2, y]
        xData3 = geometry1[0, 3, y]
        anglesData = geometry2[0, 0, y]

        # loop over the number of columns
        for x in range(0, numCols):
            # if our score does not have sufficient probability,
            # ignore it
            if scoresData[x] < conf_threshold:
                continue

            # compute the offset factor as our resulting feature
            # maps will be 4x smaller than the input image
            (offsetX, offsetY) = (x * 4.0, y * 4.0)

            # extract the rotation angle for the prediction and
            # then compute the sin and cosine
            angle = anglesData[x]
            cos = np.cos(angle)
            sin = np.sin(angle)

            # use the geometry volume to derive the width and height
            # of the bounding box
            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]

            # compute both the starting and ending (x, y)-coordinates
            # for the text prediction bounding box
            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)

            # add the bounding box coordinates and probability score
            # to our respective lists
            rects.append((startX, startY, endX, endY))
            confidences.append(scoresData[x])
            angles.append(angle)

    # return a tuple of the bounding boxes and associated confidences
    return (rects, confidences, angles)


def decode_east(nn_packet: dai.NNData, conf_threshold=0.5, overlap_threshold=0.3):
    scores, geom1, geom2 = (
        nn_packet.getLayerFp16(name) for name in nn_packet.getAllLayerNames()
    )
    scores = np.reshape(scores, (1, 1, 64, 64))
    geom1 = np.reshape(geom1, (1, 4, 64, 64))
    geom2 = np.reshape(geom2, (1, 1, 64, 64))
    bboxes, confs, angles = decode_predictions(scores, geom1, geom2, conf_threshold)
    boxes, angles = non_max_suppression(
        np.array(bboxes),
        probs=confs,
        angles=np.array(angles),
        overlap_threshold=overlap_threshold,
    )
    return boxes, angles
