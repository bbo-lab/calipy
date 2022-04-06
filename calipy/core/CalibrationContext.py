# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

import pickle

import cv2

import numpy as np

from .BaseContext import BaseContext

from calipy import detect, calib, math


class CalibrationContext(BaseContext):
    """ Controller-style class to handle camera systems calibration """

    DETECTORS = [detect.ChArucoDetector]

    MODELS = [calib.PinholeCameraModel, calib.SphericalCameraModel]

    def __init__(self):
        super().__init__()

        # Initialize detectors and models with context
        self.detectors = [D(self) for D in self.DETECTORS]
        self.models = [M(self) for M in self.MODELS]

        # Current selection
        self.detector_index = 0
        self.model_index = 0

        # Initialize results
        self.detections = {}  # det_id > src_id > frm_idx > { <detector specific> }
        self.size = {}  # src_id > (w, h)
        self.detection_params = {} # det_id > src_id > { <detector specific> }

        self.calibrations = {}  # mod_id > cam_id > { r_vec: vec3, t_vec: vec3, <calibration specific> }
        self.estimations = {}  # mod_id > src_id > frm_idx > { r_vec: vec3, t_vec: vec3 }

        self.sys_calibrations = {} # mod_id > cam_id > { rX1: vec3, tX1: vec3, <calibration specific> } \
                                    # mod_id > { refcam_id, opt_result, intrinsic_flags }
        # Assumed single source for each camera
        self.refcam_estimations = {} # mod_id > refcam_id > src_id > frm_idx > { r1: vec3, t1: vec3 }

    def get_available_subsets(self):
        """ Override available subsets to add calibration based subsets"""
        subsets = super().get_available_subsets()

        # Add detections and estimations as subset
        detections = self.get_current_detections()
        det_idx = set()

        estimations = self.get_current_estimations()
        est_idx = set()

        for rec in self.recordings.values():
            src_id = rec.get_source_id()
            det_idx.update(detections.get(src_id, []))
            est_idx.update(estimations.get(src_id, []))

        if len(det_idx):
            subsets['Detections'] = sorted(det_idx)

        if len(est_idx):
            subsets['Estimations'] = sorted(est_idx)

        return subsets

    def get_frame(self, id):
        """ Override frame retrieval to draw calibration result """
        frame = super().get_frame(id)
        src_id = self.get_source_id(id)

        #if id in self.calibrations:
        #    frame = self.get_current_model().undistort(frame, self.calibrations[id])

        detection = self.get_current_detections().get(src_id, {}).get(self.frame_index, None)
        parameters_all = self.get_current_detector_params()
        
        if detection:
            # Make sure we draw in color by converting the frame to color first if necessary
            if frame.ndim < 3 or frame.shape[2] == 1:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            
            #board parameters
            parameters = parameters_all.get(src_id, {})
            
            # Draw detection result
            detector = self.get_current_detector()
            detector.configure(parameters)
            frame = detector.draw(frame, detection)

            calibration = self.get_current_calibrations().get(id, None)
            estimation = self.get_current_estimations().get(src_id, {}).get(self.frame_index, None)

            # Draw calibration result
            
            model = self.get_current_model()
            model.configure(parameters)
            frame = model.draw(frame, detection, calibration, estimation)

        return frame

    # Detector and detection management

    def get_detector_names(self):
        return [a.NAME for a in self.detectors]

    def select_detector(self, index):
        self.detector_index = index

    def set_current_detector_parameter(self, name, value):
        print("{}: {}".format(name, value))

    def get_current_detector(self):
        return self.detectors[self.detector_index]

    def get_current_detector_params(self):
        return self.detection_params.get(self.get_current_detector().ID, {})

    def get_current_detections(self):
        return self.detections.get(self.get_current_detector().ID, {})

    # Model and calibration management

    def get_model_names(self):
        return [a.NAME for a in self.models]

    def select_model(self, index):
        self.model_index = index

    def get_current_model(self):
        return self.models[self.model_index]

    def get_current_calibrations(self):
        return self.calibrations.get(self.get_current_model().ID, {})

    def get_current_estimations(self):
        return self.estimations.get(self.get_current_model().ID, {})
    
    def get_current_system_calibrations(self):
        return self.sys_calibrations.get(self.get_current_model().ID, {})
    
    def get_current_refcam_estimations(self):
        return self.refcam_estimations.get(self.get_current_model().ID, {})

    # Overall reault management

    def save_result(self, url):
        with open(url, "wb") as file:
            temp = {'detections': self.detections,
                    'size': self.size,
                    'detection_params': self.detection_params,
                    'calibrations': self.calibrations,
                    'estimations': self.estimations,
                    'sys_calibrations': self.sys_calibrations,
                    'refcam_estimations': self.refcam_estimations}
            pickle.dump(temp, file)

    def load_result(self, url):
        with open(url, "rb") as file:
            temp = pickle.load(file)

            for cam in self.get_cameras():
                if cam.id in self.recordings:
                    src_id = self.recordings[cam.id].get_source_id()

                    if cam.id in temp['detections']:
                        det_id = self.get_current_detector().ID

                        self.detections.setdefault(det_id, {})[src_id] = temp['detections'].pop(cam.id)
                        self.size[src_id] = temp['size'].pop(cam.id)

                    if cam.id in temp['estimations']:
                        mod_id = self.get_current_model().ID

                        self.estimations.setdefault(mod_id, {})[src_id] = temp['estimations'].pop(cam.id)

                if cam.id in temp['calibrations']:
                    mod_id = self.get_current_model().ID

                    self.calibrations.setdefault(mod_id, {})[cam.id] = temp['calibrations'].pop(cam.id)

            self.detections.update(temp['detections'])
            self.size.update(temp['size'])
            self.detection_params = temp.get('detection_params', {})

            self.calibrations.update(temp['calibrations'])
            self.estimations.update(temp['estimations'])

            self.sys_calibrations = temp.get('sys_calibrations', {})
            self.refcam_estimations = temp.get('refcam_estimations', {})

    def cleanup_result(self):
        """ Delete any results from unmatched source id """
        
        # TODO: keep or remove
        pass

    def clear_result(self):
        self.detections.clear()
        self.size.clear()

        self.calibrations.clear()
        self.estimations.clear()

        self.sys_calibrations.clear()
        self.refcam_estimations.clear()

    # Run current detection

    def run_detection(self, parameters, progress):
        if not self.session:
            raise RuntimeError("No session selected")

        detector = self.get_current_detector()
        detector.configure(parameters)

        for cam_id, rec in self.recordings.items():
            src_id = rec.get_source_id()

            progress.setLabelText("Processing data from '{}'...".format(cam_id))
            progress.setMaximum(rec.get_length())

            # Clear last result
            self.detections.setdefault(detector.ID, {})[src_id] = {}

            for index in range(rec.get_length()):
                progress.setValue(index)

                if progress.wasCanceled():
                    return

                frame = rec.get_frame(index)
                result = detector.detect(frame)

                if result:
                    self.detections[detector.ID][src_id][index] = result

            self.detection_params.setdefault(detector.ID, {})[src_id] = parameters

            self.size[src_id] = rec.get_size()

    # Run current calibration

    def prepare_detections(self, parameters, detections):

        detector = self.get_current_detector()
        detector.configure(parameters)

        object_pts = []
        image_pts = []
        square_ids = []
        rej = []

        for index, detected in enumerate(detections):
            
            extracted = detector.extract(detected)

            if not extracted:
                rej.append(index)
                continue

            # Current backend expect at least 4 points per pattern
            # Updated 4 to min_det_feats
            if len(extracted['image_pts']) < detector.min_det_feats:
                rej.append(index)
                continue

            # Make sure detected points are not all on one line
            if math.are_points_on_line(extracted['object_pts']):
                rej.append(index)
                continue

            # checks if consecutive frames are too similar
            if len(image_pts):
                previous_pts = np.zeros((detector.num_feats, 2), dtype=np.float64)
                current_pts = np.zeros((detector.num_feats, 2), dtype=np.float64)
                previous_pts[square_ids[-1].ravel()] = image_pts[-1].squeeze()
                current_pts[extracted['square_ids'].ravel()] = extracted['image_pts'].squeeze()
                
                diff = current_pts - previous_pts
                ids_use = np.intersect1d(square_ids[-1].ravel(), extracted['square_ids'].ravel())              
                diff = diff[ids_use]
                dist = np.sqrt(np.sum(diff**2, 1))
                
                # use frame when all ids are different
                if (np.size(dist) == 0):
                    dist_max = np.inf
                else:
                    dist_max = np.max(dist)
                # check if maximum distance is greater than one pixel
                if not(dist_max > 1.0):
                    # Include the frame if it has more markers than the previosly accepted similar frame
                    if len(extracted['square_ids'].ravel()) <= len(square_ids[-1].ravel()):
                        rej.append(index)
                        continue
                    
            object_pts.append(extracted['object_pts'])
            image_pts.append(extracted['image_pts'])
            square_ids.append(extracted['square_ids'])

        return object_pts, image_pts, rej
    

    def calibrate_cameras(self, progress):
        model = self.get_current_model()

        source_maps = self.get_all_source_ids()
        detections_all = self.get_current_detections()
        parameters_all = self.get_current_detector_params()

        if progress.wasCanceled():
            return
        
        for cam in self.get_cameras():
            # Retrieve all sources for cameras
            source_ids = [src_map[cam.id] for src_map in source_maps if cam.id in src_map]

            # Extract detection object and image points
            object_pts = []
            image_pts = []
            used_indices = []
            rejected_indices = []
            for src_id in source_ids:
                detections = detections_all.get(src_id, {})
                
                detection_keys = [(src_id, idx) for idx in detections]
                detection_values = list(detections.values())
                
                parameters = parameters_all.get(src_id, {})
                model.configure(parameters)
                
                obj_pts, img_pts, rejections = self.prepare_detections(parameters, detection_values)
                
                object_pts += obj_pts
                image_pts += img_pts

                for r in sorted(rejections, reverse=True):
                    rejected_indices.append(detection_keys[r])
                    del detection_keys[r]

                used_indices += detection_keys
            sizes = [self.size[sid] for sid in source_ids]
            
            total = len(object_pts)
            
            progress.setLabelText("Calibration of '{}'...".format(cam.id))
            progress.setMaximum(total)
            
            calibration = None

            # Run batches with increasing size
            for batch_size in range(total // 4, total, (total // 4) + 1):
                progress.setValue(batch_size)

                if progress.wasCanceled():
                    return

                print("Calibration of {} with {} / {} detections".format(cam.id, batch_size, total))

                try:
                    calibration = model.calibrate_camera(sizes[0], object_pts[:batch_size], image_pts[:batch_size], calibration)
                except Exception as e:
                    print("Batch Calibration with {:d} / {:d} detections failed: {:s}".format(batch_size, total, str(e)))

            progress.setValue(total)

            print("Calibration of {} with all {} detections".format(cam.id, total))

            # Run final optimization
            calibration = model.calibrate_camera(sizes[0], object_pts, image_pts, calibration)

            # Save calibration and estimation if successfull
            if calibration:
                calibration['rej'] = rejected_indices  # Needed for stats

                self.calibrations.setdefault(model.ID, {})[cam.id] = calibration

                if 'idx' in calibration:
                    used_indices = [used_indices[i] for i in calibration['idx'].flatten()]

                for src_id in source_ids:
                    self.estimations.setdefault(model.ID, {})[src_id] = {}
                
                for index, (src_id, frm_idx) in enumerate(used_indices):
                    self.estimations[model.ID][src_id][frm_idx] = {'r_vec': calibration['r_vecs'][index],
                                                                   't_vec': calibration['t_vecs'][index]}
            
            if progress.wasCanceled():
                return
    
    # Run system calibration
    
    def prepare_syscal_frames(self, cam_frame_bool, source_maps, estimations_all):
        
        # Identify the poses (corresponding frames) that were PROPERLY captured in more than one camera for system calibration. A PROPER capture is when number of detected features >= min_det_feats    
        num_orig_frames = cam_frame_bool.shape[1]
        
        for cam_idx, cam in enumerate(self.get_cameras()):
            # Retrieve all sources for cameras
            source_ids = [src_map[cam.id] for src_map in source_maps if cam.id in src_map]
            
            for src_id in source_ids:
                estimations_old = estimations_all.get(src_id, {})

                used_indices = np.array([idx for idx in estimations_old])
                used_indices = used_indices[used_indices < num_orig_frames]
                cam_frame_bool[cam_idx, used_indices] = True
            
        frame_bool = np.zeros(num_orig_frames, dtype=bool)
        for frame_idx in range(num_orig_frames):
            frame_score = np.sum(cam_frame_bool[:, frame_idx])

            if (frame_score > 1):
                frame_bool[frame_idx] = True
        
        
        # Find reference camera => camera which has captured the most poses
        cam_score = np.sum(cam_frame_bool[:, frame_bool], 1)
        refcam_idx = np.where(cam_score == np.max(cam_score))[0][0]
        
        # Only use frames where the reference camera has PROPERLY captured the poses
        frame_bool = (frame_bool & cam_frame_bool[refcam_idx,:])
        num_used_frames = int(np.sum(frame_bool))
        print( str(num_used_frames) + " frames are used for system calibration.")
        
        return refcam_idx, frame_bool
    
    
    def prepare_syscal(self, frame_bool, square_ids, image_pts, estimations, 
                       parameters, detections, estimations_old):

        num_orig_frames = frame_bool.size
        
        detector = self.get_current_detector()
        detector.configure(parameters)
        
        indices = np.arange(num_orig_frames)[frame_bool]
        index2 = 0
        
        for index in indices:
            
            if index in estimations_old:
                extracted = detector.extract(detections[index])
                square_ids[index2] = np.squeeze( np.array(extracted['square_ids'], dtype = np.int32) )
                image_pts[index2] = np.squeeze( extracted['image_pts'] )
                estimations[index2] = estimations_old[index]
            
            else:
                square_ids[index2] = np.array([], dtype = np.int32)
                image_pts[index2] = np.array([])
                estimations[index2] = {}
                
            index2 += 1

        return square_ids, image_pts, estimations
     
    
    def calibrate_system(self, progress):
        
        model = self.get_current_model()
        source_maps = self.get_all_source_ids()
        parameters_all = self.get_current_detector_params()

        detections_all = self.get_current_detections()
        calibrations_all = self.get_current_calibrations()
        estimations_all = self.get_current_estimations()
        
        syscal = {}
        
        if progress.wasCanceled():
            return
        
        # TODO: Obtain flags from user for intrinsic parameters ex: distortion coefficients
        flags = {}
        
        if not bool(calibrations_all):
            raise RuntimeError("Please, Calibrate Cameras.")
            
        num_cams = len(self.get_cameras())
        if num_cams < 2:
            raise RuntimeError("There are less than two cameras. Calibrate System not applicable.")
        
        # Num of frames considered
        num_orig_frames = np.zeros(num_cams, dtype = np.int64)
        
        for cam_idx, rec in enumerate(self.recordings.values()):
            num_orig_frames[cam_idx] = rec.get_length()

        num_orig_frames = min(num_orig_frames)                         
        print("The first {:d} frames are considered for system calibration".format(num_orig_frames))
        
        cam_frame_bool = np.zeros((num_cams, num_orig_frames), dtype=bool)
        refcam_idx, frame_bool = self.prepare_syscal_frames(cam_frame_bool, source_maps, estimations_all)
        
        # Extract square_ids, image points, intrinsic and extrensic parameters
        square_ids = {}
        image_pts = {}
        estimations_new = {}
        calibrations_new = {}
        
        for cam_idx, (cam) in enumerate(self.get_cameras()):
            
            if cam_idx == refcam_idx:
                syscal['refcam_id'] = cam.id
                syscal['refcam_idx'] = refcam_idx
            
            # Retrieve all sources for cameras
            source_ids = [src_map[cam.id] for src_map in source_maps if cam.id in src_map]
            sizes = [self.size[sid] for sid in source_ids]
            
            sq_ids, img_pts, estimations = ({} for i in range(3))
            
            # Assumed single source for each camera
            for src_id in source_ids:
                
                detections = detections_all.get(src_id, {})
                estimations_old = estimations_all.get(src_id, {})

                parameters = parameters_all.get(src_id, {})                
                
                sq_ids, img_pts, estimations = self.prepare_syscal(frame_bool, sq_ids, img_pts, estimations, 
                                                                   parameters, detections, estimations_old)
                
                if cam_idx == refcam_idx:
                    used_indices = [(src_id, idx) for idx in detections if frame_bool[idx]]
                
            square_ids[cam_idx] = sq_ids
            image_pts[cam_idx] = img_pts
            estimations_new[cam_idx] = estimations
            
            calibration = calibrations_all.get(cam.id, {})
            calibrations_new[cam_idx] = calibration
        
        model.configure(parameters)
        
        syscal['int_para_flags'] = flags
        
        progress.setLabelText("System calibration in progress: {:d} cameras and {:d} poses".format(num_cams, np.int(sum(frame_bool))))
        if progress.wasCanceled():
            return
        
        # Run system calibration
        syscal = model.calibrate_system(sizes[0], square_ids, image_pts, estimations_new, calibrations_new, flags, syscal)
        
        # Save calibration and estimations if successfull
        if syscal['convergence']:
            
            for cam_idx, (cam) in enumerate(self.get_cameras()):
                self.sys_calibrations.setdefault(model.ID, {})[cam.id] = syscal['cam_{:d}'.format(cam_idx)]
            
                if cam_idx == refcam_idx:
                    self.sys_calibrations[model.ID]['refcam_id'] = cam.id
                    self.refcam_estimations.setdefault(model.ID, {})[cam.id] = {}
                    
                    for index, (src_id, frm_idx) in enumerate(used_indices):
                        self.refcam_estimations[model.ID][cam.id].setdefault(src_id, {})[frm_idx] = syscal['refcam'][index]
                        
            self.sys_calibrations[model.ID]['optimization_result'] = syscal['result']
            self.sys_calibrations[model.ID]['mean_rms_error'] = syscal['mean_rms_error']
            self.sys_calibrations[model.ID]['int_para_flags'] = flags
            
        if progress.wasCanceled():
            return

   # Results statistics

    def get_detection_stats(self):
        stats = {}

        detections = self.get_current_detections()

        for cam_id, rec in self.recordings.items():
            src_id = rec.get_source_id()

            # Skip detection that were never run
            if src_id not in detections:
                continue

            # Count detections and markers
            patterns = 0
            markers = 0

            for detected in detections[src_id].values():
                if 'square_corners' in detected:
                    patterns += 1
                    markers += len(detected['marker_corners'])

            stats[cam_id] = (patterns, markers)

        return stats

    def get_calibration_stats(self):
        stats = {}

        source_maps = self.get_all_source_ids()

        detections = self.get_current_detections()
        det_stats = self.get_detection_stats()
        
        calibrations = self.get_current_calibrations()
        estimations = self.get_current_estimations()

        for cam_id, calibration in calibrations.items():
            source_ids = [src_map[cam_id] for src_map in source_maps if cam_id in src_map]
            
            orig_count_det = sum([len(detections.get(sid, [])) for sid in source_ids])
            count_det = det_stats[cam_id][0]
            
            count_est = sum([len(estimations.get(sid, [])) for sid in source_ids])
            count_rej = len(calibration['rej'])

            stats[cam_id] = {
                'error': calibration['err'],
                'detections': count_det,
                'usable': orig_count_det - count_rej,
                'estimations': count_est
            }
        
        # TODO: currently screwed up, check again
        return stats
    
    def get_system_calibration_stats(self):
        
        model = self.get_current_model()
        source_maps = self.get_all_source_ids()
        
        det_stats = self.get_detection_stats()
        
        sys_calibrations = self.get_current_system_calibrations()
        refcam_estimations = self.get_current_refcam_estimations()
        
        if 'optimization_result' in sys_calibrations:
            refcam_id = sys_calibrations['refcam_id']
        
            source_ids = [src_map[refcam_id] for src_map in source_maps if refcam_id in src_map]
            count_est = sum([len(refcam_estimations[refcam_id].get(sid, [])) for sid in source_ids])
            
            stats  = {
                'error': sys_calibrations['mean_rms_error'],
                'detections': det_stats[refcam_id][0],
                'estimations': count_est
            }
        else:
            stats = {}
        
        return stats