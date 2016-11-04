'''
RENDER_MODEL_VIEWS.py
brief:
usage:
inputs:
author:
'''

import os
import bpy
import bpy_extras
import sys
import os, tempfile, glob, shutil
import math
import random
import time
import numpy as np
from mathutils import Vector
from mathutils import Matrix
from mathutils import Quaternion

# Different Light Settings
r = [255, 255, 255, 255, 255, 255]
g = [197, 214, 241, 250, 255, 255]
b = [142, 170, 224, 244, 251, 255]
g_syn_light_environment_energy_lowbound = 0.5
g_syn_light_environment_energy_highbound = 1

# Camera Intrinsic matrix
K = Matrix(([619.444214, 0.0, 320],[0.0, 619.444336, 240],[0.0, 0.0, 1.0 ]))

# Camera Location options
cam_location = [[0.5, 0, 0.12], [0.5, -0.15, 0.12], [0.5, 0.15, 0.12], [0.5, 0, 0.3]]
cam_rotation = [[0.5, 0.5, 0.5, 0.5], [0.612, 0.612, 0.354, 0.354], [0.354, 0.354, 0.612, 0.612], [0.612, 0.354, 0.354, 0.612]]

# Creates a blender camera consistent with a given intrinsic matrix
def set_camera_using_intrinsics():
    scene = bpy.context.scene
    sensor_width_in_mm = K[1][1]*K[0][2] / (K[0][0]*K[1][2])
    sensor_height_in_mm = 1  # doesn't matter
    resolution_x_in_px = K[0][2]*2  # principal point assumed at the center
    resolution_y_in_px = K[1][2]*2  # principal point assumed at the center

    s_u = resolution_x_in_px / sensor_width_in_mm
    s_v = resolution_y_in_px / sensor_height_in_mm
    f_in_mm = K[0][0] / s_u

    # recover original resolution
    scene.render.resolution_x = resolution_x_in_px
    scene.render.resolution_y = resolution_y_in_px
    scene.render.resolution_percentage = 100

    # set camera parameters
    cam_ob = scene.objects['Camera']
    cam_ob.location = [0, 0, 0]
    cam_ob.rotation_mode = 'QUATERNION'
    cam_ob.rotation_quaternion = [1, 0, 0, 0]

    cam_ob.data.type = 'PERSP'
    cam_ob.data.lens = f_in_mm 
    cam_ob.data.lens_unit = 'MILLIMETERS'
    cam_ob.data.sensor_width  = sensor_width_in_mm

    scene.camera = cam_ob
    bpy.context.scene.update()

def get_3x4_RT_matrix_from_blender(cam):
    # bcam stands for blender camera
    R_bcam2cv = Matrix(
        ((1, 0,  0),
         (0, -1, 0),
         (0, 0, -1)))

    # Use matrix_world instead to account for all constraints
    location, rotation = cam.matrix_world.decompose()[0:2]
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
def get_3x4_P_matrix_from_blender(cam):
    RT = get_3x4_RT_matrix_from_blender(cam)
    return K*RT, K, RT

# Compute the bounds of the object by iterating over all vertices
def camera_view_bounds_2d(me_ob):
    min_x, max_x = 10000, 0.0
    min_y, max_y = 10000, 0.0

    scene = bpy.context.scene
    cam_ob = scene.objects['Camera']

    print ("object location : ", me_ob.matrix_world.translation)

    coworld = [(me_ob.matrix_world * v.co) for v in me_ob.data.vertices]
    proj, K, RT = get_3x4_P_matrix_from_blender(cam_ob)

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

    print ("bbox : ", min_x, max_x, min_y, max_y)
    return (min_x, min_y, max_x - min_x, max_y - min_y)

def inside_shelf(me_ob):
    shelf_dims = Vector((0.43,0.28,0.22))

    if me_ob.matrix_world.translation[0] < (-shelf_dims[0]/2) or \
       me_ob.matrix_world.translation[0] > (shelf_dims[0]/2) or \
       me_ob.matrix_world.translation[1] < (-shelf_dims[1]/2) or \
       me_ob.matrix_world.translation[1] > (shelf_dims[1]/2) or \
       me_ob.matrix_world.translation[2] < 0 or \
       me_ob.matrix_world.translation[2] > (shelf_dims[2]):
        print("Object is out of shelf : ", me_ob.matrix_world.translation)
        return 0 
    else:
        return 1

def write_bounds_2d(filepath, me_ob):
    in_shelf = inside_shelf(me_ob)
    with open(filepath, "a+") as file:
        print("get bounding box of " + me_ob.name)
        print("3d location ", me_ob.matrix_world.translation)
        x, y, width, height = camera_view_bounds_2d(me_ob)
        if x > scene.render.resolution_x or \
           y > scene.render.resolution_y or \
           x + width < 0 or \
           y + height < 0 or \
           width < 0 or height < 0 or \
           in_shelf == 0:
            print ("bbox out of range: (x, y, width, height), ignored!", x, y, width, height)
            return -1, -1, -1, -1
        else:
            # if bbox is out of camera range, crop it
            if x < 0:
                width = width + x
                x = 0
            if y < 0:
                height = height + y
                y = 0
            if x + width > scene.render.resolution_x:
                width = scene.render.resolution_x - x
            if y + height > scene.render.resolution_y:
                height = scene.render.resolution_y - y
            file.write(me_ob.name)
            file.write(",%i,%i,%i,%i,%f\n" % (x, y, width, height, me_ob.matrix_world.translation[0]))
            return x, y, width, height

# Input parameters
num_of_images = int(sys.argv[-3])
env = sys.argv[-2]
syn_images_folder = sys.argv[-1]
if not os.path.exists(syn_images_folder):
    os.mkdir(syn_images_folder)

scene = bpy.context.scene
objects = bpy.data.objects

#load environment
if env == 'table':
    shape_file = 'table_models/table.obj'
    bpy.ops.import_scene.obj(filepath=shape_file)

    objects["Table"].location = [0, 0, 0]
    objects["Table"].rotation_mode = 'QUATERNION'
    objects["Table"].rotation_quaternion[0] = 0.7
    objects["Table"].rotation_quaternion[1] = 0.7
    objects["Table"].rotation_quaternion[2] = 0
    objects["Table"].rotation_quaternion[2] = 0

    scene.objects.active = scene.objects["Table"]
    bpy.ops.rigidbody.object_add(type='ACTIVE')
    bpy.ops.object.modifier_add(type = 'COLLISION')
    objects["Table"].rigid_body.enabled = False
    objects["Table"].rigid_body.use_margin = True
    objects["Table"].rigid_body.collision_margin = 0.01

elif env == 'shelf':
    shape_file = 'table_models/finalshelf.obj'
    bpy.ops.import_scene.obj(filepath=shape_file)
    objects['Plane'].location[0] = -1
    objects['Plane.001'].location[0] = -1
    objects['Plane.002'].location[0] = -1
    objects['Plane.003'].location[0] = -1
    objects['Plane.004'].location[0] = -1
    objects["Plane.005_Plane.006"].location[0] = -1

    scene.objects.active = scene.objects["Plane"]
    bpy.ops.rigidbody.object_add(type='ACTIVE')
    bpy.ops.object.modifier_add(type = 'COLLISION')
    objects["Plane"].rigid_body.enabled = False
    objects["Plane"].rigid_body.use_margin = True
    objects["Plane"].rigid_body.collision_margin = 0.01

    scene.objects.active = scene.objects["Plane.001"]
    bpy.ops.rigidbody.object_add(type='ACTIVE')
    bpy.ops.object.modifier_add(type = 'COLLISION')
    objects["Plane.001"].rigid_body.enabled = False
    objects["Plane.001"].rigid_body.use_margin = True
    objects["Plane.001"].rigid_body.collision_margin = 0.01

    scene.objects.active = scene.objects["Plane.002"]
    bpy.ops.rigidbody.object_add(type='ACTIVE')
    bpy.ops.object.modifier_add(type = 'COLLISION')
    objects["Plane.002"].rigid_body.enabled = False
    objects["Plane.002"].rigid_body.use_margin = True
    objects["Plane.002"].rigid_body.collision_margin = 0.01

    scene.objects.active = scene.objects["Plane.003"]
    bpy.ops.rigidbody.object_add(type='ACTIVE')
    bpy.ops.object.modifier_add(type = 'COLLISION')
    objects["Plane.003"].rigid_body.enabled = False
    objects["Plane.003"].rigid_body.use_margin = True
    objects["Plane.003"].rigid_body.collision_margin = 0.01

    scene.objects.active = scene.objects["Plane.004"]
    bpy.ops.rigidbody.object_add(type='ACTIVE')
    bpy.ops.object.modifier_add(type = 'COLLISION')
    objects["Plane.004"].rigid_body.enabled = False
    objects["Plane.004"].rigid_body.use_margin = True
    objects["Plane.004"].rigid_body.collision_margin = 0.01

    scene.objects.active = scene.objects["Plane.005_Plane.006"]
    bpy.ops.rigidbody.object_add(type='ACTIVE')
    bpy.ops.object.modifier_add(type = 'COLLISION')
    objects["Plane.005_Plane.006"].rigid_body.enabled = False
    objects["Plane.005_Plane.006"].rigid_body.use_margin = True
    objects["Plane.005_Plane.006"].rigid_body.collision_margin = 0.01
    objects["Plane.005_Plane.006"].hide_render = True

# set camera
set_camera_using_intrinsics()

# environment lighting
bpy.ops.object.select_by_type(type='LAMP')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.world.light_settings.use_environment_light = True
bpy.context.scene.world.light_settings.environment_energy = np.random.uniform(g_syn_light_environment_energy_lowbound, 
                                                                                g_syn_light_environment_energy_highbound)
bpy.context.scene.world.light_settings.environment_color = 'PLAIN'

#add light source
bpy.ops.object.lamp_add(type='POINT', view_align = False, location=(0, 0, 0))
objects['Point'].data.use_specular = False
objects['Point'].data.shadow_method = 'RAY_SHADOW'
objects['Point'].data.shadow_ray_samples = 2
objects['Point'].data.shadow_soft_size = 0.5

object_file_list = ["crayola_24_ct", "expo_dry_erase_board_eraser", "folgers_classic_roast_coffee",
                    "scotch_duct_tape", "dasani_water_bottle", "jane_eyre_dvd",
                    "up_glucose_bottle", "laugh_out_loud_joke_book", "soft_white_lightbulb",
                    "kleenex_tissue_box", "ticonderoga_12_pencils", "dove_beauty_bar",
                    "dr_browns_bottle_brush", "elmers_washable_no_run_school_glue", "rawlings_baseball" ]

# import objects to blender
objectlist = []
for obj_file_name in object_file_list:
    bpy.ops.import_scene.obj(filepath="obj_models/" + obj_file_name + ".obj")
    imported = bpy.context.selected_objects[0]
    objectlist.append(imported.name)

for item in bpy.data.materials:
    # item.use_shadeless = True
    # item.subsurface_scattering.use = True
    item.emit = 0.05

begin = len(glob.glob1("rendered_images", "image_*.png"))
num = begin
while num < (begin + num_of_images):
    # Random Camera setting
    randcam = random.randint(0,3)
    objects['Camera'].location = cam_location[randcam]
    objects['Camera'].rotation_mode = 'QUATERNION'
    objects['Camera'].rotation_quaternion = cam_rotation[randcam]

    # Random light setting
    lx = random.uniform(0.8, 1.2)
    ly = random.uniform(-0.12, 0.12)
    lz = random.uniform(0.12, 0.42)
    color_idx = random.randint(0, len(r) - 1)
    objects['Point'].location = [lx, ly, lz]
    objects['Point'].data.energy = random.randint(0, 4)
    objects['Point'].data.color = (r[color_idx]/255,g[color_idx]/255,b[color_idx]/255)

    # hide all objects
    for obj in objectlist:
        objects[obj].hide = True
        objects[obj].hide_render = True
        objects[obj].location[0] = 100.0

    sceneobjectlist = list(objectlist)
    numberOfObjects = random.randint(2, 4)
    selectedobj = list()
    while len(selectedobj) < numberOfObjects:
        index = random.randint(0, len(objectlist)-1)
        if index in selectedobj:
            continue
        selectedobj.append(index)

    print ("numberOfObjects : ", numberOfObjects)
    print ("selected set is : ", selectedobj)
    
    for i in range(0, numberOfObjects):
        index = selectedobj[i]
        shape_file = objectlist[index]
        sceneobjectlist[index] = shape_file
        objects[shape_file].hide = False
        objects[shape_file].hide_render = False
        objects[shape_file].location[0] = random.uniform(-0.20, 0.15)
        objects[shape_file].location[1] = random.uniform(-0.12, 0.12)
        objects[shape_file].location[2] = random.uniform(0.08, 0.12)
        objects[shape_file].rotation_mode = 'XYZ'
        objects[shape_file].rotation_euler = (random.randint(0, 360)*3.14/180.0, 
                                              random.randint(0, 360)*3.14/180.0, 
                                              random.randint(0, 360)*3.14/180.0)
        
        print("Object is : ", objectlist[index])
        print("object location is")
        print(objects[shape_file].location )
        print("object rotation is")
        print(objects[shape_file].rotation_euler )

        scene.objects.active = scene.objects[shape_file]
        bpy.ops.rigidbody.object_add(type='ACTIVE')
        bpy.ops.object.modifier_add(type = 'COLLISION')
        scene.objects[shape_file].rigid_body.mass = 10.0
        scene.objects[shape_file].rigid_body.use_margin = True
        scene.objects[shape_file].rigid_body.collision_margin = 0.005

    #Rendering settings
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].region_3d.view_perspective = 'CAMERA'
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.viewport_shade = 'TEXTURED'

    bpy.data.scenes['Scene'].frame_end = 81
    bpy.data.scenes['Scene'].frame_step = 80
    bpy.context.scene.frame_set(80)

    faster = True
    if faster:
        bpy.data.scenes['Scene'].render.use_raytrace = False
        bpy.context.scene.render.use_shadows = False
        bpy.data.worlds['World'].light_settings.use_ambient_occlusion = False

    syn_image_file = "temp.png"
    output_img = "rendered_images/image_%05i.png" % num
    print ("filename stored is " + syn_image_file)
    scene.render.filepath = os.path.join(syn_images_folder, syn_image_file)
    bpy.ops.render.render(write_still=True,animation=True)

    #Copy the final image and clear the temp folder
    imgs = glob.glob(syn_images_folder+'/*.png')
    imgs.sort()
    shutil.move(imgs[-1], output_img)
    shutil.rmtree(syn_images_folder)
        
    #2-D bounding boxes
    output_bbox = "raw_bbox_%05i.txt" % num
    filepath = os.path.join("rendered_images", output_bbox)
    if os.path.isfile(filepath):
        os.remove(filepath)

    for i in range(0, numberOfObjects):
        index = selectedobj[i]
        shape_file = sceneobjectlist[index]
        x, y, width, height = write_bounds_2d(filepath, objects[shape_file])

    # save to temp.blend
    # mainfile_path = os.path.join("rendered_images", "blend_%05d.blend" % num)
    # bpy.ops.file.autopack_toggle()
    # bpy.ops.wm.save_as_mainfile(filepath=mainfile_path)

    num = num + 1





