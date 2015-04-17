#!/usr/bin/python

import random

class CommunicationBus(object):
	def __init__(self, name = None, verbose = False):
		self.name = name
		self.verbose = verbose
		self.tick()

	def tick(self):
		self.messages = []

	def send(self, message):
		if self.verbose:
			print "Message posted to communication bus %s: %s" % (self.name, message)
		self.messages.append(message)

	def receive(self):
		random.shuffle(self.messages)
		return list(self.messages)
