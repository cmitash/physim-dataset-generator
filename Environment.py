"""
@file Environment.py
@copyright Software License Agreement (BSD License).
Copyright (c) 2017, Rutgers the State University of New Jersey, New Brunswick.
All Rights Reserved. For a full description see the file named LICENSE.
Authors: Chaitanya Mitash, Kostas Bekris, Abdeslam Boularias.
"""

import bpy
import random
import numpy as np

class Shelf:
    def __init__(self, shape_file):
        bpy.ops.import_scene.obj(filepath=shape_file)
        for planes in bpy.data.objects:
            if 'Plane' in planes.name:
                bpy.context.scene.objects.active = planes
                bpy.ops.rigidbody.object_add(type='ACTIVE')
                bpy.ops.object.modifier_add(type = 'COLLISION')
                planes.rigid_body.enabled = False
                planes.rigid_body.use_margin = True
                planes.rigid_body.collision_margin = 0.01
                bpy.data.objects["Plane.Front"].hide_render = True
        bpy.data.materials["None"].use_shadeless = True
        bpy.data.materials["None_shelfside.JPG"].use_shadeless = True
        bpy.data.materials["None_shelftop.JPG"].use_shadeless = True
        bpy.data.materials["None_shelftop.JPG_shelftop.JPG"].use_shadeless = True

    def setPose(self, pose):
        return

class Table:
    def __init__(self, shape_file):
        bpy.ops.import_scene.obj(filepath=shape_file)
        object_instance = bpy.data.objects["Table"]
        object_instance.location = [0, 0, 0]
        object_instance.rotation_mode = 'QUATERNION'
        object_instance.rotation_quaternion = [0.7, 0.7, 0, 0]

        bpy.context.scene.objects.active = bpy.context.scene.objects["Table"]
        bpy.ops.rigidbody.object_add(type='ACTIVE')
        bpy.ops.object.modifier_add(type = 'COLLISION')
        object_instance.rigid_body.enabled = False
        object_instance.rigid_body.use_margin = True
        object_instance.rigid_body.collision_margin = 0.01
        bpy.data.materials["WHITE_PLASTIC"].use_shadeless = True

    def setPose(self, pose):
        object_instance = bpy.data.objects["Table"]
        object_instance.location = [pose[0], pose[1], pose[2]]
        object_instance.rotation_mode = 'QUATERNION'
        object_instance.rotation_quaternion = [pose[3], pose[4], pose[5], pose[6]]

class RandomTable:
    def __init__(self, shape_file):
        bpy.ops.import_scene.obj(filepath=shape_file)
        object_instance = bpy.data.objects["Cube"]
        object_instance.location = [0, 0, 0]
        object_instance.rotation_mode = 'QUATERNION'
        object_instance.rotation_quaternion = [1, 0, 0, 0]

        bpy.context.scene.objects.active = bpy.context.scene.objects["Cube"]
        bpy.ops.rigidbody.object_add(type='ACTIVE')
        bpy.ops.object.modifier_add(type = 'COLLISION')
        object_instance.rigid_body.enabled = False
        object_instance.rigid_body.use_margin = True
        object_instance.rigid_body.collision_margin = 0.01
        object_instance.hide_render = False
        

    def setPose(self, pose):
        object_instance = bpy.data.objects["Cube"]
        object_instance.location = [pose[0], pose[1], pose[2]]
        object_instance.rotation_mode = 'QUATERNION'
        object_instance.rotation_quaternion = [pose[3], pose[4], pose[5], pose[6]]

    def getRandomTexture(self):
        object_instance = bpy.data.objects["Cube"]

        # set based on the number of candidate material images
        img_num = random.randint(1, 4)
        img_name = "surface_models/random_table/images/image_%05i.jpg" % img_num
        img = bpy.data.images.load(img_name)
        mat = object_instance.data.materials['Material']
        tex = bpy.data.textures.new('random_image', 'IMAGE')
        tex.image = img
        mat.active_texture = tex

    def getCyclesTexture(self):
        object_instance = bpy.data.objects["Cube"]

        # set based on the number of candidate material images
        img_num = random.randint(1, 4)
        img_name = "surface_models/random_table/images/image_%05i.jpg" % img_num
        img = bpy.data.images.load(img_name)
        mat = object_instance.data.materials['Material']
        mat.use_nodes = True

        material_node = mat.node_tree.nodes.get('Material Output')
        if material_node == None:
            material_node = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')

        diffuse_node = mat.node_tree.nodes.get('Diffuse BSDF')
        if diffuse_node == None:
            diffuse_node = mat.node_tree.nodes.new('ShaderNodeBsdfDiffuse')

        tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex_node.image = img

        mat.node_tree.links.new(tex_node.outputs[0], diffuse_node.inputs[0])
        mat.node_tree.links.new(diffuse_node.outputs[0], material_node.inputs[0])


class Bin:
    def __init__(self, shape_file):
        bpy.ops.import_scene.obj(filepath=shape_file)
        self.planes = []
        for planes in bpy.data.objects:
            if 'Plane' in planes.name:
                self.planes.append(planes.name)
                bpy.context.scene.objects.active = planes
                bpy.ops.rigidbody.object_add(type='ACTIVE')
                bpy.ops.object.modifier_add(type = 'COLLISION')
                planes.rigid_body.enabled = False
                planes.rigid_body.use_margin = True
                planes.rigid_body.collision_margin = 0.01
                planes.hide_render = False

    def setPose(self, pose):
        for planes in bpy.data.objects:
            if 'Plane' in planes.name:
                planes.location = [pose[0], pose[1], pose[2]]
                planes.rotation_mode = 'QUATERNION'
                planes.rotation_quaternion = [pose[3], pose[4], pose[5], pose[6]]

    def randomizeTexture(self):
        r = random.uniform(0, 1)
        g = random.uniform(0, 1)
        b = random.uniform(0, 1)
        for plane in self.planes:
            planes = bpy.data.objects[plane]
            for slot in planes.material_slots:
                new_mat = bpy.data.materials.new(name="color")
                new_mat.diffuse_color = (r,g,b)
                slot.material = new_mat

    def hideBin(self):
        for planes in bpy.data.objects:
            if 'Plane' in planes.name:
                planes.hide_render = True

class Light:
    lightColors = [[255,197,142], [255,214,170], [255,241,224],
                   [255,250,244], [255,255,251], [255,255,255]]
    GlobalEnergyLowbound = 0.5
    GlobalEnergyHighbound = 1

    def __init__(self):
        bpy.ops.object.select_by_type(type='LAMP')
        bpy.ops.object.delete(use_global=False)
        bpy.context.scene.world.light_settings.use_environment_light = True
        bpy.context.scene.world.light_settings.environment_energy = random.uniform(self.GlobalEnergyLowbound, self.GlobalEnergyHighbound)
        bpy.context.scene.world.light_settings.environment_color = 'PLAIN'

        #add a point light source
        bpy.ops.object.lamp_add(type='POINT', view_align = False)
        bpy.data.objects['Point'].data.use_specular = False
        bpy.data.objects['Point'].data.shadow_method = 'RAY_SHADOW'
        bpy.data.objects['Point'].data.shadow_ray_samples = 2
        bpy.data.objects['Point'].data.shadow_soft_size = 0.5

    def placePointLight(self, light_range_x, light_range_y, light_range_z):
        lx = random.uniform(light_range_x[0], light_range_x[1])
        ly = random.uniform(light_range_y[0], light_range_y[1])
        lz = random.uniform(light_range_z[0], light_range_z[1])
        bpy.data.objects['Point'].location = [lx, ly, lz]
        bpy.data.objects['Point'].data.energy = random.uniform(1, 4)
        color_idx = random.randint(0, len(self.lightColors) - 1)
        bpy.data.objects['Point'].data.color = (self.lightColors[color_idx][0]/255,
                                                self.lightColors[color_idx][1]/255,
                                                self.lightColors[color_idx][2]/255)