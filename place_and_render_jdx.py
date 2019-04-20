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
from mathutils import Vector, Matrix, Quaternion

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
    surface.hideBin()

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
    
    num = 0
    numImages = cfg.getNumTrainingImages()
    cam_pose = cam.placeCamera(0)

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

    cam_matrix = Matrix(((cam_rot[0][0], cam_rot[0][1], cam_rot[0][2], cam_trans[0]),
                        (cam_rot[1][0], cam_rot[1][1], cam_rot[1][2], cam_trans[1]),
                        (cam_rot[2][0], cam_rot[2][1], cam_rot[2][2], cam_trans[2]),
                        (0, 0, 0, 1)))

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

        n1_poses, o1_poses = cfg.getObjPoses(num, 1)
        n2_poses, o2_poses = cfg.getObjPoses(num, 2)

        numObjectsInScene = n1_poses + n2_poses

        sceneobjectlist = list(objectlist)
        selectedobj = list()

        for index in range(0, n1_poses):
            selectedobj.append(index)

        for index in range(numInstances, numInstances + n2_poses):
            selectedobj.append(index)

        print ("numObjectsInScene : ", numObjectsInScene)
        print ("selected set is : ", selectedobj)

        o1_poses = o1_poses + o2_poses
        
        ## sample initial pose for each of the selected object
        for i in range(0, numObjectsInScene):
            index = selectedobj[i]
            shape_file = objectlist[index]
            sceneobjectlist[index] = shape_file
            bpy.data.objects[shape_file].hide = False
            bpy.data.objects[shape_file].hide_render = False
            bpy.data.objects[shape_file].pass_index = i + 1

            obj_trans = Vector((o1_poses[i][0], o1_poses[i][1], o1_poses[i][2]))
            obj_rot = Quaternion((o1_poses[i][3], o1_poses[i][4], o1_poses[i][5], o1_poses[i][6]))
            obj_rot = obj_rot.to_matrix()

            obj_pose = Matrix(((obj_rot[0][0], obj_rot[0][1], obj_rot[0][2], obj_trans[0]),
                                (obj_rot[1][0], obj_rot[1][1], obj_rot[1][2], obj_trans[1]),
                                (obj_rot[2][0], obj_rot[2][1], obj_rot[2][2], obj_trans[2]),
                                (0, 0, 0, 1)))

            obj_pose = cam_matrix*obj_pose

            obj_rot = Matrix(((obj_pose[0][0], obj_pose[0][1], obj_pose[0][2]),
                                (obj_pose[1][0], obj_pose[1][1], obj_pose[1][2]),
                                (obj_pose[2][0], obj_pose[2][1], obj_pose[2][2])))

            trans = obj_pose.translation
            rotq = obj_rot.to_quaternion()
            print (rotq)

            bpy.data.objects[shape_file].location = (trans[0], trans[1], trans[2])
            bpy.data.objects[shape_file].rotation_mode = 'QUATERNION'
            bpy.data.objects[shape_file].rotation_quaternion = (rotq[0], rotq[1], rotq[2], rotq[3])

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

        # FLAT RENDERING BLANDER INTERNAL
        if cfg.getRenderer() == 'flat':
            for item in bpy.data.materials:
                item.use_shadeless = True
                item.use_cast_buffer_shadows = False

        # BLENDER RENDER::TODO: Look into the effect of these parameters
        if cfg.getRenderer() == 'blender':
            bpy.context.scene.render.use_shadows = True
            bpy.context.scene.render.use_raytrace = False
            for item in bpy.data.materials:
                item.emit = random.uniform(0.1, 0.6)

        # CYCLES RENDERER
        if cfg.getRenderer() == 'cycles':
            bpy.context.scene.render.use_shadows = True
            bpy.context.scene.render.use_raytrace = True
            bpy.context.scene.render.engine = 'CYCLES'
            bpy.context.scene.cycles.device = 'GPU'

            bpy.context.scene.render.use_antialiasing = True
            bpy.context.scene.render.use_textures = True
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
            if cfg.saveDebugFile() == True: 
                mainfile_path = os.path.join("rendered_images/debug/", "blend_%05d.blend" % num)
                bpy.ops.file.autopack_toggle()
                bpy.ops.wm.save_as_mainfile(filepath=mainfile_path)

            num = num + 1
            if num >= numImages:
                break
            
        

    

        