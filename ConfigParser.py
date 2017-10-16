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

	def __init__(self, filepath):
		if os.path.exists(filepath) == False:
			print('please create config.yml file with simulation parameters !!!')
			sys.exit()

		with open(filepath,"r") as file_descriptor:
			self.data=yaml.load(file_descriptor)

	def getSurfaceType(self):
		return self.data['rest_surface']['type']

	def getSurfacePose(self):
		return self.data['rest_surface']['surface_pose']

	def getCamIntrinsic(self):
		return self.data['camera']['camera_intrinsics']

	def getCamExtrinsic(self):
		return self.data['camera']['camera_poses']

	def getObjModelList(self):
		return self.data['Models']

	def getNumTrainingImages(self):
		return self.data['params']['num_images']

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