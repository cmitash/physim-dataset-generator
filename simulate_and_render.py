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
from scipy.spatial import distance

# Verify if repository path is set in bashrc
if os.environ.get('PHYSIM_GENDATA') == None:
    print("Please set PHYSIM_GENDATA in bashrc!")
    sys.exit()

g_repo_path = os.environ['PHYSIM_GENDATA']
sys.path.append(g_repo_path)

from Environment import Shelf, Table, Bin, RandomTable, Light
from ConfigParser import ConfigParser
from Camera import Camera

if __name__ == "__main__":

    ## read configuration file
    cfg = ConfigParser("config.yml", "camera_info.yml")

    ## initialize resting surface
    env = cfg.getSurfaceType()
    if env == 'table':
        surface = Table('surface_models/table/table.obj')
    elif env == 'shelf':
        surface = Shelf('surface_models/shelf/shelf.obj')
    elif env == 'bin':
        surface = Bin('surface_models/bin/shelf.obj')
    elif env == 'randomized_table':
        surface = RandomTable('surface_models/random_table/table.obj')

    sPose = cfg.getSurfacePose()
    surface.setPose(sPose)

    ## initialize camera
    camIntrinsic = cfg.getCamIntrinsic()
    maxCamViews, camExtrinsic = cfg.getCamExtrinsic()  # maxCamViews: num of poses
    numViews = cfg.getNumViews()
    cam = Camera(camIntrinsic, camExtrinsic, numViews)

    ## initialize light
    pLight = Light()

    ## initialize objects
    objModelList = cfg.getObjModelList()
    numInstances = cfg.getNumInstances()
    objectlist = []  #object names
    object_materials = []
    for objFileName in objModelList:
        for instances in range(0, numInstances):
            
            if cfg.getObjectModelType() == 'obj':
                # for obj objects materials are read from the mtl file
                bpy.ops.import_scene.obj(filepath="obj_models/" + objFileName + "/" + objFileName + ".obj")
                imported = bpy.context.selected_objects[0]
            else:
                # for ply files material needs to be initialized
                bpy.ops.import_mesh.ply(filepath="obj_models/" + objFileName + "/" + objFileName + ".ply")

                # Initialize a basic new material for ply models
                material_name = "mat_%s_%05i" % (objFileName, instances)
                mat = bpy.data.materials.new(name=material_name)
                mat.emit = 0
                mat.use_vertex_color_paint = True
                mat.use_cast_buffer_shadows = True
                mat.diffuse_intensity = 0.8
                mat.specular_intensity = 0.3
                
                imported = bpy.context.selected_objects[0]
                imported.data.materials.append(mat)
                imported.data.use_auto_smooth = True
                imported.data.auto_smooth_angle = math.radians(10)   
                object_materials.append(mat)

            objectlist.append(imported.name)
    
    # FLAT RENDERING BLANDER INTERNAL
    if cfg.getRenderer() == 'flat':
        bpy.context.scene.render.use_raytrace = False
        bpy.context.scene.render.use_shadows = False
        bpy.context.scene.render.use_antialiasing = False
        bpy.context.scene.render.use_textures = True
        for item in bpy.data.materials:
            item.use_shadeless = True
            item.use_cast_buffer_shadows = False

    # BLENDER RENDER::TODO: Look into the effect of these parameters
    if cfg.getRenderer() == 'blender':
        bpy.context.scene.render.use_shadows = True
        bpy.context.scene.render.use_raytrace = False
        bpy.context.scene.render.use_antialiasing = True
        bpy.context.scene.render.use_textures = True
        for item in bpy.data.materials:
            item.emit = random.uniform(0.1, 0.6)

    # CYCLES RENDERER
    if cfg.getRenderer() == 'cycles':
        bpy.context.scene.render.use_shadows = True
        bpy.context.scene.render.use_raytrace = True
        bpy.context.scene.render.use_antialiasing = True
        bpy.context.scene.render.use_textures = True
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.device = 'GPU'
        bpy.context.scene.cycles.samples = 100

        # For Cycles Material
        if cfg.getObjectModelType() == 'obj':
            bpy.ops.ml.refresh()
            for item in bpy.data.materials:
                texture_node = item.node_tree.nodes.get('Image Texture')
                material_node = item.node_tree.nodes.get('Material Output')
                if not texture_node == None:
                    if not material_node == None:
                        diffuse_node = item.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
                        item.node_tree.links.new(texture_node.outputs[0], diffuse_node.inputs[0])
                        item.node_tree.links.new(diffuse_node.outputs[0], material_node.inputs[0])
        else:
            for item in object_materials:
                item.use_nodes = True
                attr_node = item.node_tree.nodes.new('ShaderNodeAttribute')
                attr_node.attribute_name = "Col"

                diffuse_node = item.node_tree.nodes.get('Diffuse BSDF')
                if diffuse_node == None:
                    diffuse_node = item.node_tree.nodes.new('ShaderNodeBsdfDiffuse')

                material_node = item.node_tree.nodes.get('Material Output')
                if material_node == None:
                    material_node = item.node_tree.nodes.new('ShaderNodeOutputMaterial')

                item.node_tree.links.new(attr_node.outputs[0], diffuse_node.inputs[0])
                item.node_tree.links.new(diffuse_node.outputs[0], material_node.inputs[0])

    num = 0
    numImages = cfg.getNumTrainingImages()
    while num < numImages:
        print ('Number of images synthesized..... ', num)
        
        if env == 'randomized_table':
            surface.getRandomTexture()
        elif env == 'bin':
            surface.randomizeTexture()

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
        placed_pts = []
        for i in range(0, numObjectsInScene):
            index = selectedobj[i]
            shape_file = objectlist[index]
            sceneobjectlist[index] = shape_file
            bpy.data.objects[shape_file].hide = False
            bpy.data.objects[shape_file].hide_render = False
            bpy.data.objects[shape_file].pass_index = i + 1
            range_x = cfg.getRangeX()
            range_y = cfg.getRangeY()
            range_z = cfg.getRangeZ()
            range_euler_x = cfg.getRangeEulerX()
            range_euler_y = cfg.getRangeEulerY()
            range_euler_z = cfg.getRangeEulerZ()

            # random poses
            pos_x = random.uniform(range_x[0], range_x[1])
            pos_y = random.uniform(range_y[0], range_y[1])
            pos_z = random.uniform(range_z[0], range_z[1])
            rot_x = random.randint(range_euler_x[0], range_euler_x[1])*3.14/180.0
            rot_y = random.randint(range_euler_y[0], range_euler_y[1])*3.14/180.0
            rot_z = random.randint(range_euler_z[0], range_euler_z[1])*3.14/180.0

            # AVOID COLLISION in XY Plane
            pos_x = 0
            pos_y = 0
            validPlacement = False
            while validPlacement == False:
                validPlacement = True
                pos_x = random.uniform(range_x[0], range_x[1])
                pos_y = random.uniform(range_y[0], range_y[1])
                curr_pt = [pos_x, pos_y]
                for pt in placed_pts:
                    dist = distance.euclidean(pt, curr_pt)
                    if dist < cfg.getMinDistance():
                        validPlacement = False
            
            placed_pts.append([pos_x, pos_y])
            # AVOID COLLISION MODULE ENDS

            bpy.data.objects[shape_file].location = (pos_x, pos_y, pos_z)
            bpy.data.objects[shape_file].rotation_mode = 'XYZ'
            bpy.data.objects[shape_file].rotation_euler = (rot_x, rot_y, rot_z)

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

        
        if cfg.getRenderer() == 'cycles':

            if env == 'randomized_table':
                surface.getCyclesTexture()

            # Light source config
            bpy.data.lamps["Point"].shadow_soft_size = 2
            bpy.data.lamps['Point'].use_nodes = True
            bpy.data.lamps['Point'].node_tree.nodes.new(type='ShaderNodeEmission')
            bpy.data.lamps["Point"].node_tree.nodes["Emission"].inputs['Strength'].default_value = random.randint(50, 200)

        # Use nodes for rendering depth images and object masks
        bpy.context.scene.render.use_compositing = True
        bpy.context.scene.render.layers["RenderLayer"].use_pass_object_index = True
        bpy.context.scene.use_nodes = True

        for i in range(0,cam.numViews):
            cam_view = random.randint(0, maxCamViews-1)
            cam_pose = cam.placeCamera(cam_view)
            tree = bpy.context.scene.node_tree
            links = tree.links

            for n in tree.nodes:
                tree.nodes.remove(n)

            render_node = tree.nodes.new('CompositorNodeRLayers')

            # For depth rendering
            bpy.context.scene.render.image_settings.file_format = 'OPEN_EXR'
            depth_node = tree.nodes.new('CompositorNodeOutputFile') 
            depth_node.base_path = "rendered_images/image_%05i/depth/" % num
            depth_node.file_slots[0].path = "image_"
            links.new(render_node.outputs[2], depth_node.inputs[0])

            for j in range(0, numObjectsInScene):

                bpy.context.scene.render.image_settings.file_format = 'PNG'
                bpy.context.scene.render.image_settings.color_mode = 'BW'
                tmp_node = tree.nodes.new('CompositorNodeIDMask')
                tmp_node.index = j + 1
                links.new(render_node.outputs[14], tmp_node.inputs[0])

                tmp_out = tree.nodes.new('CompositorNodeOutputFile') 
                tmp_out.base_path = "rendered_images/debug/"
                tmp_out.file_slots[0].path = "image_%05i_%02i_" % (num, j)

                links.new(tmp_node.outputs[0], tmp_out.inputs[0])

            output_img = "rendered_images/image_%05i/rgb/image.png" % num
            bpy.context.scene.render.resolution_percentage = 100
            bpy.context.scene.render.image_settings.file_format = 'PNG'
            bpy.context.scene.render.image_settings.color_mode = 'RGB'
            bpy.context.scene.render.filepath = os.path.join(g_repo_path, output_img) 
            bpy.ops.render.render(write_still=True)

            os.makedirs("rendered_images/image_%05i/labels" % num)

            # Write class id, pose
            output_filepath = "rendered_images/debug/class_id_%05i.txt" % num

            for i in range(0, numObjectsInScene):
                index = selectedobj[i]
                shape_file = sceneobjectlist[index]
                classId = int(index/numInstances)
                with open(output_filepath, "a+") as file:
                    file.write("%i\n" % classId)

                output_pose = "rendered_images/image_%05i/labels/obj_%02i.yml" % (num, classId + 1)
                cam.write_object_pose(output_pose, bpy.data.objects[shape_file], classId, cam_pose)

            output_filepath = "rendered_images/dataset_info.txt"
            with open(output_filepath, "a+") as file:
                file.write("%i,%i\n" % (num,numObjectsInScene))

            # save to temp.blend
            # if cfg.saveDebugFile() == True: 
            #     mainfile_path = os.path.join("rendered_images/debug/", "blend_%05d.blend" % num)
            #     bpy.ops.file.autopack_toggle()
            #     bpy.ops.wm.save_as_mainfile(filepath=mainfile_path)

            num = num + 1
            if num >= numImages:
                break
            
        

    

        