import bpy
import random

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

    def inside_shelf(me_ob):
        shelf_dims = Vector((0.43,0.28,0.22)) # (x, y, z) dimensions

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

    def placePointLight(self):
        lx = random.uniform(0.8, 1.2)
        ly = random.uniform(-0.12, 0.12)
        lz = random.uniform(0.12, 0.42)
        bpy.data.objects['Point'].location = [lx, ly, lz]
        bpy.data.objects['Point'].data.energy = random.randint(0, 4)
        color_idx = random.randint(0, len(self.lightColors) - 1)
        bpy.data.objects['Point'].data.color = (self.lightColors[color_idx][0]/255,
                                                self.lightColors[color_idx][1]/255,
                                                self.lightColors[color_idx][2]/255)