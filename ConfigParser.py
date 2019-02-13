"""
@file ConfigParser.py
@copyright Software License Agreement (BSD License).
Copyright (c) 2017, Rutgers the State University of New Jersey, New Brunswick.
All Rights Reserved. For a full description see the file named LICENSE.
Authors: Chaitanya Mitash, Kostas Bekris, Abdeslam Boularias.
"""

import yaml
import os,sys

class ConfigParser:
	data = []
	cam_data = []

	def __init__(self, cfg_filepath, cam_filepath):
		if os.path.exists(cfg_filepath) == False:
			print('please create config.yml file with simulation parameters !!!')
			sys.exit()

		with open(cfg_filepath,"r") as file_descriptor:
			self.data=yaml.load(file_descriptor)

		with open(cam_filepath,"r") as file_descriptor:
			self.cam_data=yaml.load(file_descriptor)

	def getSurfaceType(self):
		return self.data['rest_surface']['type']

	def getSurfacePose(self):
		return self.data['rest_surface']['surface_pose']

	def getCamIntrinsic(self):
		return self.data['camera']['camera_intrinsics']

	def getCamExtrinsic(self):
		num_poses = self.cam_data['num_poses']
		cam_poses = []
		for pose in range(0, num_poses):
			trans = self.cam_data[pose][0]['cam_t_m2c']
			rot = self.cam_data[pose][0]['cam_R_m2c']
			cam_pose = [trans[0], trans[1], trans[2], rot[0], rot[1], rot[2], rot[3]]
			cam_poses.append(cam_pose)
		return num_poses, cam_poses

	def getObjModelList(self):
		return self.data['Models']

	def getNumTrainingImages(self):
		return self.data['params']['num_images']

	def getObjectModelType(self):
		return self.data['params']['object_model_type']

	def isFlatRendering(self):
		return self.data['params']['flat_rendering']

	def getLabelType(self):
		return self.data['params']['label_type']

	def getMinObjectsScene(self):
		return self.data['params']['minimum_objects_in_scene']

	def getMaxObjectsScene(self):
		return self.data['params']['maximum_objects_in_scene']

	def getRangeX(self):
		return self.data['params']['range_x']

	def getRangeY(self):
		return self.data['params']['range_y']

	def getRangeZ(self):
		return self.data['params']['range_z']

	def getRangeEulerX(self):
		return self.data['params']['range_euler_x']
	
	def getRangeEulerY(self):
		return self.data['params']['range_euler_y']
	
	def getRangeEulerZ(self):
		return self.data['params']['range_euler_z']

	def getNumSimulationSteps(self):
		return self.data['params']['num_simulation_steps']

	def getNumViews(self):
		return self.data['camera']['num_poses']

	def getLightRangeX(self):
		return self.data['params']['light_position_range_x']

	def getLightRangeY(self):
		return self.data['params']['light_position_range_y']

	def getLightRangeZ(self):
		return self.data['params']['light_position_range_z']
		
	def getNumInstances(self):
		return self.data['params']['num_object_instances']