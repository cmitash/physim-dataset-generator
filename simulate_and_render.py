"""
@file simulate_and_render.py
@copyright Software License Agreement (BSD License).
Copyright (c) 2017, Rutgers the State University of New Jersey, New Brunswick,
All Rights Reserved. For a full description see the file named LICENSE.
Authors: Chaitanya Mitash, Kostas Bekris, Abdeslam Boularias.
"""

import sys, os, tempfile, glob, shutil, time
import bpy
import math, random, numpy

# Verify if repository path is set in bashrc
if os.environ.get('PHYSIM_GENDATA') == None:
    print("Please set PHYSIM_GENDATA in bashrc!")
    sys.exit()

g_repo_path = os.environ['PHYSIM_GENDATA']
sys.path.append(g_repo_path)

from Environment import Shelf, Table, Light
from ConfigParser import ConfigParser
from Camera import Camera

if __name__ == "__main__":

    ## read configuration file
    cfg = ConfigParser("config.yml")

    ## initialize resting surface
    env = cfg.getSurfaceType()
    if env == 'table':
        surface = Table('surface_models/table/table.obj')
    elif env == 'shelf':
        surface = Shelf('surface_models/shelf/shelf.obj')
    sPose = cfg.getSurfacePose()
    surface.setPose(sPose)

    ## initialize camera
    camIntrinsic = cfg.getCamIntrinsic()
    camExtrinsic = cfg.getCamExtrinsic()
    numViews = cfg.getNumViews()
    cam = Camera(camIntrinsic, camExtrinsic, numViews)

    ## initialize light
    pLight = Light()

    ## initialize objects
    objModelList = cfg.getObjModelList()
    objectlist = []
    for objFileName in objModelList:
        bpy.ops.import_scene.obj(filepath="obj_models/" + objFileName + "/" + objFileName + ".obj")
        imported = bpy.context.selected_objects[0]
        objectlist.append(imported.name)
    for item in bpy.data.materials:
        print (item)
        item.emit = 0.05

    num = 0
    numImages = cfg.getNumTrainingImages()
    while num < numImages:

        ## hide all objects
        for obj in objectlist:
            bpy.data.objects[obj].hide = True
            bpy.data.objects[obj].hide_render = True
            bpy.data.objects[obj].location[0] = 100.0

        ## choose a random subset of objects for the scene
        sceneobjectlist = list(objectlist)
        minObjects = cfg.getMinObjectsScene()
        maxObjects = cfg.getMaxObjectsScene()
        numObjectsInScene = random.randint(minObjects, maxObjects)
        selectedobj = list()
        while len(selectedobj) < numObjectsInScene:
            index = random.randint(0, len(objectlist)-1)
            if index in selectedobj:
                continue
            selectedobj.append(index)

        print ("numObjectsInScene : ", numObjectsInScene)
        print ("selected set is : ", selectedobj)
        
        ## sample initial pose for each of the selected object
        for i in range(0, numObjectsInScene):
            index = selectedobj[i]
            shape_file = objectlist[index]
            sceneobjectlist[index] = shape_file
            bpy.data.objects[shape_file].hide = False
            bpy.data.objects[shape_file].hide_render = False
            range_x = cfg.getRangeX()
            range_y = cfg.getRangeY()
            range_z = cfg.getRangeZ()
            bpy.data.objects[shape_file].location = (random.uniform(range_x[0], range_x[1]),
                                                        random.uniform(range_y[0], range_y[1]),
                                                        random.uniform(range_z[0], range_z[1]))

            bpy.data.objects[shape_file].rotation_mode = 'XYZ'
            bpy.data.objects[shape_file].rotation_euler = (random.randint(0, 360)*3.14/180.0, 
                                                           random.randint(0, 360)*3.14/180.0, 
                                                           random.randint(0, 360)*3.14/180.0)

            bpy.context.scene.objects.active = bpy.context.scene.objects[shape_file]
            bpy.ops.rigidbody.object_add(type='ACTIVE')
            bpy.ops.object.modifier_add(type = 'COLLISION')
            bpy.context.scene.objects[shape_file].rigid_body.mass = 10.0
            bpy.context.scene.objects[shape_file].rigid_body.use_margin = True
            bpy.context.scene.objects[shape_file].rigid_body.collision_margin = 0
            bpy.context.scene.objects[shape_file].rigid_body.linear_damping = 0.9
            bpy.context.scene.objects[shape_file].rigid_body.angular_damping = 0.9


        ## performing simulation
        framesIter = cfg.getNumSimulationSteps()
        for i in range(1,framesIter):
            bpy.context.scene.frame_set(i)

        ## pick lighting
        light_range_x = cfg.getLightRangeX()
        light_range_y = cfg.getLightRangeY()
        light_range_z = cfg.getLightRangeZ()
        pLight.placePointLight(light_range_x, light_range_y, light_range_z)

        ## rendering configuration
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.viewport_shade = 'TEXTURED'

        bpy.context.scene.render.use_raytrace = False
        bpy.context.scene.render.use_shadows = False

        for i in range(0,cam.numViews):
            cam.placeCamera(i)
            output_img = "rendered_images/image_%05i.png" % num
            bpy.context.scene.render.filepath = os.path.join(g_repo_path, output_img) 
            bpy.ops.render.render(write_still=True)

            #2-D bounding boxes
            output_bbox = "rendered_images/debug/raw_bbox_%05i.txt" % num
            for i in range(0, numObjectsInScene):
                index = selectedobj[i]
                shape_file = sceneobjectlist[index]
                print (index, shape_file)
                x, y, width, height = cam.write_bounds_2d(output_bbox, bpy.data.objects[shape_file], index)

            # save to temp.blend
            mainfile_path = os.path.join("rendered_images/debug/", "blend_%05d.blend" % num)
            bpy.ops.file.autopack_toggle()
            bpy.ops.wm.save_as_mainfile(filepath=mainfile_path)

            num = num + 1
            if num >= numImages:
                break
            
        

    

        