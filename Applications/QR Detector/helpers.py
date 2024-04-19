import numpy as np

# coordinates order - x, y
def transform_coords(coords_from, coords_to, bbox, mean = 0):
    # calculate scale values for the given coordinates combination and extend the resulting vector
    # to match the dimensions of the bounding box (xmin, ymin, xmax, ymax),
    # i.e., [x_s, y_s] -> [x_s, y_s, x_s, y_s]
    S = coords_to / coords_from
    S = np.tile(S, 2)
    
    M = np.array(mean)
    # if M is a vector, extend it to match the dimensions of the bounding box (xmin, ymin, xmax, ymax),
    # i.e., [x_m, y_m] -> [x_m, y_m, x_m, y_m].
    # There is no need to do this if M is a scalar.
    if np.ndim(M) > 0:
        M = np.tile(M, 2)  

    res = bbox * S + M

    # clip the result to get rid of negative numbers that might occur
    np.clip(res, a_min=0, a_max=None, out=res)  # in-place clipping

    return res.astype(int)

# scale_factor can be scalar (= same for both x,y) or vector [scale_x, scale_y]
def wh_from_frame(frame, scale_factor = 1):
    # CONSIDER: is this flipping a good idea? it seems confusing when indexing frames (CV images)
    # which use "matrix" indexing - i,j (height, width)
    wh = np.flip(frame.shape[0:-1])     # order of coordinates: x, y (width, height)
    return wh * np.array(scale_factor)
