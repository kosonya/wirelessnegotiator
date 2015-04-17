#!/usr/bin/python


class Entity(object):
	def __init__(self, communication_bus):
		self.combus = communication_bus
	
	def tick(self):
		pass
	
	def talk(self):
		pass

	def listen(self):
		pass
