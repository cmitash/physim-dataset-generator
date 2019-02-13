"""
@file Camera.py
@copyright Software License Agreement (BSD License).
Copyright (c) 2017, Rutgers the State University of New Jersey, New Brunswick.
All Rights Reserved. For a full description see the file named LICENSE.
Authors: Chaitanya Mitash, Kostas Bekris, Abdeslam Boularias.
"""

import bpy
from mathutils import Vector, Matrix, Quaternion

class Camera:

    numViews = []
    camIntrinsic = []
    camExtrinsic = []

    def __init__(self, camIntrinsic, camExtrinsic, numViews):
        self.camIntrinsic = camIntrinsic
        self.camExtrinsic = camExtrinsic
        self.numViews = numViews
        sensor_width_in_mm = self.camIntrinsic[1][1]*self.camIntrinsic[0][2] / (self.camIntrinsic[0][0]*self.camIntrinsic[1][2])
        sensor_height_in_mm = 1  # doesn't matter
        resolution_x_in_px = self.camIntrinsic[0][2]*2  # principal point assumed at the center
        resolution_y_in_px = self.camIntrinsic[1][2]*2  # principal point assumed at the center

        s_u = resolution_x_in_px / sensor_width_in_mm
        s_v = resolution_y_in_px / sensor_height_in_mm
        f_in_mm = self.camIntrinsic[0][0] / s_u

        # recover original resolution
        bpy.context.scene.render.resolution_x = resolution_x_in_px
        bpy.context.scene.render.resolution_y = resolution_y_in_px
        bpy.context.scene.render.resolution_percentage = 100

        # set camera parameters
        cam_ob = bpy.context.scene.objects['Camera']
        cam_ob.location = [0, 0, 0]
        cam_ob.rotation_mode = 'QUATERNION'
        cam_ob.rotation_quaternion = [1, 0, 0, 0]

        cam_ob.data.type = 'PERSP'
        cam_ob.data.lens = f_in_mm 
        cam_ob.data.lens_unit = 'MILLIMETERS'
        cam_ob.data.sensor_width  = sensor_width_in_mm

        bpy.context.scene.camera = cam_ob
        bpy.context.scene.update()

    def placeCamera(self, view):
        bpy.data.objects['Camera'].location = (self.camExtrinsic[view][0], self.camExtrinsic[view][1], self.camExtrinsic[view][2])
        bpy.data.objects['Camera'].rotation_mode = 'QUATERNION'
        bpy.data.objects['Camera'].rotation_quaternion = (self.camExtrinsic[view][3], self.camExtrinsic[view][4],
                                                           self.camExtrinsic[view][5], self.camExtrinsic[view][6])
        return self.camExtrinsic[view]

    def write_object_pose(self, filepath, me_ob, index, cam_pose):
        with open(filepath, "a+") as file:

            cam_trans = Vector((cam_pose[0], cam_pose[1], cam_pose[2]))
            cam_rot = Quaternion((cam_pose[3], cam_pose[4], cam_pose[5], cam_pose[6]))
            
            initrot1 = Matrix(((-1,0,0), 
                            (0,1,0), 
                            (0,0,-1)))
            initrot2 = Matrix(((-1,0,0), 
                            (0,-1,0), 
                            (0,0,1)))
            initrot1 = initrot1.transposed()
            initrot2 = initrot2.transposed()
            cam_rot = cam_rot.to_matrix()
            cam_rot = cam_rot*initrot2
            cam_rot = cam_rot*initrot1

            cam_rot = cam_rot.transposed()
            cam_trans = cam_rot*cam_trans

            inv_cam_matrix = Matrix(
                                    ((cam_rot[0][0], cam_rot[0][1], cam_rot[0][2], -cam_trans[0]),
                                    (cam_rot[1][0], cam_rot[1][1], cam_rot[1][2], -cam_trans[1]),
                                    (cam_rot[2][0], cam_rot[2][1], cam_rot[2][2], -cam_trans[2]),
                                    (0, 0, 0, 1)))

            object_pose_world = me_ob.matrix_world
            object_pose_camera = inv_cam_matrix * object_pose_world
            object_trans_camera = object_pose_camera.translation

            x, y, width, height = self.camera_view_bounds_2d(me_ob)
            if x > bpy.context.scene.render.resolution_x or \
               y > bpy.context.scene.render.resolution_y or \
               x + width < 0 or \
               y + height < 0 or \
               width < 0 or height < 0:
                print ("bbox out of range: (x, y, width, height), ignored!", x, y, width, height)
            else:
                # if bbox is out of camera range, crop it
                if x < 0:
                    width = width + x
                    x = 0
                if y < 0:
                    height = height + y
                    y = 0
                if x + width > bpy.context.scene.render.resolution_x:
                    width = bpy.context.scene.render.resolution_x - x
                if y + height > bpy.context.scene.render.resolution_y:
                    height = bpy.context.scene.render.resolution_y - y

                if width > 20 and height > 20:
                    file.write("- rotation : [%f, %f, %f, %f, %f, %f, %f, %f, %f]\n  translation : [%f, %f, %f]\n" % (object_pose_camera[0][0], object_pose_camera[0][1], object_pose_camera[0][2],
                                                                                                                    object_pose_camera[1][0], object_pose_camera[1][1], object_pose_camera[1][2],
                                                                                                                    object_pose_camera[2][0], object_pose_camera[2][1], object_pose_camera[2][2],
                                                                                                                    object_pose_camera[0][3], object_pose_camera[1][3], object_pose_camera[2][3]))

    def get_3x4_RT_matrix_from_blender(self):
        # bcam stands for blender camera
        R_bcam2cv = Matrix(
            ((1, 0,  0),
             (0, -1, 0),
             (0, 0, -1)))

        # Use matrix_world instead to account for all constraints
        location, rotation = bpy.context.scene.objects['Camera'].matrix_world.decompose()[0:2]
        R_world2bcam = rotation.to_matrix().transposed()

        # Convert camera location to translation vector used in coordinate changes
        # Use location from matrix_world to account for constraints:     
        T_world2bcam = -1*R_world2bcam * location

        # Build the coordinate transform matrix from world to computer vision camera
        R_world2cv = R_bcam2cv*R_world2bcam
        T_world2cv = R_bcam2cv*T_world2bcam

        # put into 3x4 matrix
        RT = Matrix((
            R_world2cv[0][:] + (T_world2cv[0],),
            R_world2cv[1][:] + (T_world2cv[1],),
            R_world2cv[2][:] + (T_world2cv[2],)
             ))
        return RT

    # Return K*RT, K, and RT from the blender camera
    def get_3x4_P_matrix_from_blender(self):
        RT = self.get_3x4_RT_matrix_from_blender()
        return Matrix(self.camIntrinsic)*RT, Matrix(self.camIntrinsic), RT

    # Compute the bounds of the object by iterating over all vertices
    def camera_view_bounds_2d(self, me_ob):
        min_x, max_x = 10000, 0.0
        min_y, max_y = 10000, 0.0

        coworld = [(me_ob.matrix_world * v.co) for v in me_ob.data.vertices]
        proj, K, RT = self.get_3x4_P_matrix_from_blender()

        for v in coworld:
            a = Vector((v.x, v.y, v.z, 1))
            coords = proj * a
            coords /= coords[2]

            if coords.x < min_x:
                min_x = coords.x
            if coords.x > max_x:
                max_x = coords.x
            if coords.y < min_y:
                min_y = coords.y
            if coords.y > max_y:
                max_y = coords.y

        return (min_x, min_y, max_x - min_x, max_y - min_y)