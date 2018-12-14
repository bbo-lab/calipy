from .ImagePoint import ImagePoint
from .Coordinate import Coordinate

import pandas as pd

import numpy as np
import scipy

def computeDistanceMatrix(P_one, P_two, **kwargs):
    """
    Return distance between two matrices as Pandas DataFrame.

    Distances are supplied per dimension and as norm across all dimensions.

    Supports up to four dimensions.
    """
    # Compute dims
    N_pts, N_dims = P_one.shape

    # Compute difference
    diff = P_two - P_one

    # Save overall distance
    dist = np.linalg.norm(diff, axis=1)
    data = {'point_id':  range(N_pts),
            'direction': "all",
            'error':     dist}

    data.update(kwargs)

    df = pd.DataFrame(data)

    # Save diff per direction
    directions = ['x', 'y', 'z', 'w']
    for idx, name in enumerate(directions[:N_dims]):

        dim_dist = abs(diff[:, idx])

        data = {'point_id':  range(N_pts),
                'direction': name,
                'error':     dim_dist}

        data.update(kwargs)

        df = df.append(pd.DataFrame(data), ignore_index=True)

    return df


def computeDistance3Dto3D(coords_one, coords_two, **kwargs):

    assert len(coords_one) == len(coords_two)

    # Rebase data to commen basis
    basis_one = coords_one[0].basis
    coords_two_rebased = [c.rebase(basis_one) for c in coords_two]

    # Turn objects to matrix
    P_one = Coordinate.toMatrix(coords_one)
    P_two_rebased = Coordinate.toMatrix(coords_two_rebased)

    # Compute and return dist
    df = computeDistanceMatrix(P_one, P_two_rebased, **kwargs)

    return df

def computeDistance2Dto3D(cams, points, coords, **kwargs):
    # ToDo: Add dimension checks

    # Prepare result
    df = pd.DataFrame(columns=['point_id',
                               'cam_id',
                               'direction',
                               'error'])

    # Rebase data to commen basis
    basis = cams[0].basis

    coords = [c.rebase(basis) for c in coords]

    # Compute error in each camera
    for cam_id, (cam, pts) in enumerate(zip(cams, points)):

        N_pts = len(pts)

        P_real = ImagePoint.toMatrix(pts)

        pts_proj = [cam.project(c) for c in coords]
        P_proj = ImagePoint.toMatrix(pts_proj)

        kwargs["cam_id"] = cam_id

        dist_df = computeDistanceMatrix(P_real, P_proj, **kwargs)

        df = df.append(dist_df, ignore_index=True)

    return df


def computeImageSections(width, height):
    """Compute beginning and end of five image subsections arranged in a cross"""
    sections_x = width  * np.array([[1, 3, 3, 5, 3],
                                    [3, 5, 5, 7, 5]]) / 8.0

    sections_y = height * np.array([[3, 1, 3, 3, 5],
                                    [5, 3, 5, 5, 7]]) / 8.0

    sections_name = ["left", "top", "center", "right", "bottom"]

    return sections_x.T.astype(int), sections_y.T.astype(int), sections_name


def getImageSection(image, name):
    sec_x, sec_y, sec_n = computeImageSections(*image.shape[::-1])

    if not name in sec_n:
        raise ValueError("Unknown section name: " + name)

    idx = sec_n.index(name)

    return image[slice(*sec_y[idx, :]),
                 slice(*sec_x[idx, :])]


def plotImageSections(plt, width, height, color="w"):

    for x_s, y_s, name in zip(*computeImageSections(width, height)):

        idx = [0, 1, 1, 0, 0]
        x = np.array(x_s)[idx]
        y = np.array(y_s)[idx[::-1]]

        plt.plot(x, y, color=color)
        plt.text(np.mean(x_s),
                 np.mean(y_s),
                 name,
                 color = color,
                 verticalalignment='center',
                 horizontalalignment='center')

    plt.xlim([-0.5, width - 0.5])
    plt.ylim([height - 0.5, -0.5])


DEFAULT_ROI = np.array([-1, np.iinfo(int).max])

def computeShiftedImageCorrelation(im_one, im_two, mask, max_shift, roi_x=DEFAULT_ROI, roi_y=DEFAULT_ROI, **kwargs):
    """
    Return correlation
    """
    height, width = im_one.shape

    df = pd.DataFrame()

    for shift in range(-max_shift, max_shift + 1):

        params = {'x':  (1,  0),
                  'y':  (0,  1),
                  'xy': (1,  1),
                  'yx': (1, -1)}

        for direction, (x_shift_factor, y_shift_factor) in params.items():
            # Comput shift and clip regions of interest
            if x_shift_factor != 0:
                clip_x = np.clip(roi_x, max_shift, width - max_shift)
                shift_x = clip_x + (x_shift_factor * shift)
            else:
                clip_x = np.clip(roi_x, 0, width)
                shift_x = clip_x

            if y_shift_factor != 0:
                clip_y = np.clip(roi_y, max_shift, height - max_shift)
                shift_y = clip_y + (y_shift_factor * shift)
            else:
                clip_y = np.clip(roi_y, 0, height)
                shift_y = clip_y

            #print("clip x: {} y: {} shift total: {} x: {}  y: {} dir: {}".format(clip_x, clip_y, shift, shift_x, shift_y, direction))

            # Crop or shift and then flatten
            im_one_cropped = im_one[clip_y[0]:clip_y[1], clip_x[0]:clip_x[1]]
            im_one_flatten = im_one_cropped.flatten()

            im_two_shifted = im_two[shift_y[0]:shift_y[1], shift_x[0]:shift_x[1]]
            im_two_flatten = im_two_shifted.flatten()

            mask_cropped      = mask[clip_y[0]:clip_y[1], clip_x[0]:clip_x[1]]
            mask_flatten      = mask_cropped.flatten()

            # Mask images
            im_one_masked = im_one_flatten[mask_flatten]
            im_two_masked = im_two_flatten[mask_flatten]

            # Compute correlation
            r = np.corrcoef(im_one_masked, im_two_masked)[0, 1]

            data = {'direction':   direction,
                    'shift':       shift,
                    'correlation': r}

            data.update(kwargs)

            df = df.append(data, ignore_index=True)

    return df

def computeFullShiftedImageCorrelation(image_one, image_two, mask, max_shift, **kwargs):

    kwargs['section'] = 'full'

    # Run on full image
    corr_df = computeShiftedImageCorrelation(image_one, image_two, mask, max_shift, **kwargs)

    return corr_df


def computeSectionedShiftedImageCorrelation(image_one, image_two, mask, max_shift, **kwargs):
    # Define sections
    sections_x, sections_y, sections_name = computeImageSections(*image_one.shape[::-1])

    # For each section
    df = pd.DataFrame()
    for x_lim, y_lim, name in zip(sections_x, sections_y, sections_name):

        kwargs['section'] = name

        corr_df = computeShiftedImageCorrelation(image_one, image_two, mask, max_shift,
                                                 roi_x=x_lim, roi_y=y_lim, **kwargs)

        df = df.append(corr_df)

    return df
