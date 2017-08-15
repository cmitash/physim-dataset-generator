import yaml

class ConfigParser:
	data = []

	def __init__(self, filepath):
		with open(filepath,"r") as file_descriptor:
			self.data=yaml.load(file_descriptor)

	def getSurfaceType(self):
		return self.data['rest_surface']['type']

	def getCamIntrinsic(self):
		return self.data['camera']['camera_intrinsics']

	def getCamExtrinsic(self):
		return self.data['camera']['camera_poses']

	def getObjModelList(self):
		return self.data['Models']

	def getNumTrainingImages(self):
		return self.data['params']['num_images']

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