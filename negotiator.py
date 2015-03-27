#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time

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
		return list(self.messages)

class Entity(object):
	def __init__(self, communication_bus):
		self.combus = communication_bus
	
	def tick(self):
		pass

class WifiAP(Entity):
	def __init__(self, BSSID, SSID, communication_bus, connection_scope, connection_speed, traffic_price, signal_strength, verbose = False):
		self.BSSID = BSSID
		self.SSID = SSID
		self.combus = communication_bus
		self.connection_scope = connection_scope
		self.connection_speed = connection_speed
		self.traffic_price = traffic_price
		self.signal_strength = signal_strength
		self.verbose = verbose
		self.available_bandwidth = connection_speed

	def advertise(self):
		message = {'message_type': 'offer', 'offer_type': 'connection', 'connection_scope': self.connection_scope, 'connection_speed': self.available_bandwidth, 'traffic_price': self.traffic_price, 'connection_type': 'wifi', 'signal_strength': self.signal_strength, 'message_source': self.BSSID, 'message_destination': 'all', 'BSSID': self.BSSID, 'SSID': self.SSID}
		message_str = json.dumps(message)
		self.combus.send(message_str)

	def tick(self):
		self.advertise()
		self.listen()

	def listen(self):
		messages = [json.loads(msg) for msg in self.combus.receive()]
		for message in messages:
			if message['message_destination'] in [self.BSSID, 'all']:
				if self.verbose:
					print "Message received by %s: %s" % (self.BSSID, json.dumps(message))
				

class FreeWifiWanter(Entity):
	def __init__(self, MAC, communication_bus, verbose = False):
		self.MAC = MAC
		self.combus = communication_bus
		self.verbose = verbose
		self.is_satisfied = False
		self.is_negotiating = False

	def tick(self):
		self.listen()
		if self.is_negotiating:
			message = {'message_type': 'demand', 'demand_type': 'connection', 'connection_type': 'wifi', 'message_source': self.MAC, 'message_destination': self.negotiating_party, 'requested_bandwight': 12345, 'requested_price': 0}
			message_str = json.dumps(message)
			self.combus.send(message_str)

	def listen(self):
		messages = [json.loads(msg) for msg in self.combus.receive()]
		for message in messages:
			if message['message_destination'] in [self.MAC, 'all']:
				if self.verbose:
					print "Message received by %s: %s" % (self.MAC, json.dumps(message))
				if not self.is_satisfied and not self.is_negotiating and message['message_type'] == 'offer' and message['offer_type'] == 'connection' and message['connection_type'] == 'wifi' and message['connection_scope'] == 'WAN' and message['traffic_price'] == 0:
						if self.verbose:
							print "Found it:", message
						self.is_negotiating = True
						self.negotiating_party = message['message_source']
				
def main():
	combus = CommunicationBus(name = "Common Communication Bus", verbose = True)

	cmu_ap = WifiAP(BSSID = "12:34:56:78:90:AB", SSID = "CMU WiFi", communication_bus = combus, connection_scope = "WAN", connection_speed = 14400, traffic_price = 0, signal_strength = -40, verbose = True)

	crossmobile_ap = WifiAP(BSSID = "21:43:65:87:09:BA", SSID = "Cross Mobile WiFi", communication_bus = combus, connection_scope = "LAN", connection_speed = 192000, traffic_price = 0, signal_strength = -60, verbose = True)

	client = FreeWifiWanter(MAC = 'AB:CD:EF:FE:DC:BA', communication_bus = combus, verbose = True)

	entities = [cmu_ap, crossmobile_ap, client]

	while True:
		for entity in entities:
			entity.tick()
		combus.tick()
		print "\n"
		time.sleep(0.5)

if __name__ == "__main__":
	main()
