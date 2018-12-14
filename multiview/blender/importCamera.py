import bpy

from mathutils import Matrix

import numpy as np

def importCamera(camera):
    """Import geom.Camera into blender"""
    # ToDo: Read this from camera
    width = 1280
    height = 1024

    # Create camera
    location = camera.t
    rotation = Matrix(camera.R).to_euler()
    rotation[0] += np.pi # Blender projects to Z not -Z
    bpy.ops.object.camera_add(location=location, rotation=rotation)
    bcamera = bpy.context.active_object

    # Get current scene object
    scene = bpy.context.scene

    # Set chip size based on focal length
    f = bcamera.data.lens
    aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y

    bcamera.data.sensor_width = f * width / camera.fx
    bcamera.data.sensor_height = f * height * aspect_ratio / camera.fy

    # Set shift based on camera center
    bcamera.data.shift_x = (camera.cx / width) - 0.5
    bcamera.data.shift_y = (camera.cy / height) - 0.5

    # View distance should have some sensible default
    bcamera.data.clip_end = 10000 # 10m

    # Set up render resolution
    scene.render.resolution_x = width
    scene.render.resolution_y = height

    # ToDo: Should we change this?
    scene.render.resolution_percentage = 100

    return bcamera
