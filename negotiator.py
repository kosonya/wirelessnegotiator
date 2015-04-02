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
	
	def talk(self):
		pass

	def listen(self):
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
		self.partners = {} #{"AB:CD:EF:FE:DC:BA": {"negotiation_stage": "foo", "serving_bandwidth": 12345, "remaining_cycles": 10}}

	def advertise(self):
		message = {'message_type': 'offer', 'offer_type': 'connection', 'connection_scope': self.connection_scope, 'connection_speed': self.available_bandwidth, 'traffic_price': self.traffic_price, 'connection_type': 'wifi', 'signal_strength': self.signal_strength, 'message_source': self.BSSID, 'message_destination': 'all', 'BSSID': self.BSSID, 'SSID': self.SSID}
		message_str = json.dumps(message)
		self.combus.send(message_str)

	def talk(self):
		if self.available_bandwidth >= 0:
			self.advertise()
		for partner in self.partners.keys():
			if self.partners[partner]["negotiation_stage"] == "contract_offered":
				send_message =  {'message_type': 'contract_unilateral', 'contract_type': 'connection', 'connection_scope': self.connection_scope, 'connection_speed': self.partners[partner]["serving_bandwidth"], 'traffic_price': self.partners[partner]["price"], 'connection_type': 'wifi',  'message_source': self.BSSID, 'message_destination': partner, 'contract_length': self.partners[partner]["remaining_cycles"]}
				send_message_str = json.dumps(send_message)
				self.combus.send(send_message_str)
			if self.partners[partner]["negotiation_stage"] == "serving":
				if self.partners[partner]["remaining_cycles"] > 0:
					send_message = {'message_type': 'service_token', 'service_type': 'connection', 'connection_scope': self.connection_scope, 'connection_speed': self.partners[partner]["serving_bandwidth"], 'traffic_price': self.partners[partner]["price"], 'connection_type': 'wifi',  'message_source': self.BSSID, 'message_destination': partner}
					send_message_str = json.dumps(send_message)
					self.combus.send(send_message_str)
					self.partners[partner]["remaining_cycles"] -= 1
				else:
					self.available_bandwidth += self.partners[partner]["serving_bandwidth"]
					del self.partners[partner]
				


	def tick(self):
		if self.verbose:
			self.show()

	def show(self):
		print "\n", self.SSID, self.BSSID, "available bandwidth:", self.available_bandwidth
		if self.partners:
			for partner in self.partners.keys():
				print self.partners[partner]
		print "\n"

	def listen(self):
		messages = [json.loads(msg) for msg in self.combus.receive()]
		for message in messages:
			if message['message_destination'] in [self.BSSID, 'all']:
				if self.verbose:
					print "Message received by %s: %s" % (self.BSSID, json.dumps(message))
				if message['message_type'] == 'demand' and message['connection_type'] == 'wifi' and message['requested_bandwight'] <= self.available_bandwidth and message['requested_price'] >= self.traffic_price and message['message_source'] not in self.partners.keys():
					self.partners[message['message_source']] = {"negotiation_stage": "contract_offered", "serving_bandwidth": message['requested_bandwight'], "remaining_cycles": message['requested_time'], "price":message['requested_price']}
					self.available_bandwidth -= message['requested_bandwight']
				if message['message_type'] == 'contract_signed' and message['message_source'] in self.partners.keys() and self.partners[message['message_source']]["negotiation_stage"] ==  "contract_offered":
					self.partners[message['message_source']]["negotiation_stage"] = "serving"

				

class FreeWifiWanter(Entity):
	def __init__(self, MAC, communication_bus, verbose = False, requested_service_time = 3, requested_bandwight = 1234):
		self.MAC = MAC
		self.combus = communication_bus
		self.verbose = verbose
		self.requested_service_time = requested_service_time
		self.negotiation_stage = "looking for partners"
		self.negotiation_party = None
		self.received_tokens = 0
		self.requested_bandwight = requested_bandwight 

	def talk(self):
		if self.negotiation_stage == "sending demand":
			message = {'message_type': 'demand', 'demand_type': 'connection', 'connection_type': 'wifi', 'message_source': self.MAC, 'message_destination': self.negotiation_party, 'requested_bandwight': self.requested_bandwight, 'requested_price': 0, 'requested_time': self.requested_service_time}
			message_str = json.dumps(message)
			self.combus.send(message_str)
			self.negotiation_stage = "waiting for demand answer"
		if self.negotiation_stage == "signing contract":
			message = {'message_type': 'contract_signed', 'contract_type': 'connection', 'connection_type': 'wifi', 'message_source': self.MAC, 'message_destination': self.negotiation_party, 'requested_bandwight': 1234, 'requested_price': 0, 'requested_time': self.requested_service_time}
			message_str = json.dumps(message)
			self.combus.send(message_str)
			self.negotiation_stage = "being served"

	def tick(self):
		if self.verbose:
			self.show()

	def show(self):
		print "\n", self.MAC, ";negotiation stage:", self.negotiation_stage, ";negotiation party:", self.negotiation_party, ";received tokens:", self.received_tokens

	def listen(self):
		messages = [json.loads(msg) for msg in self.combus.receive()]
		for message in messages:
			if message['message_destination'] in [self.MAC, 'all']:
				if self.verbose:
					print "Message received by %s: %s" % (self.MAC, json.dumps(message))
				if self.negotiation_stage == "looking for partners" and message['message_type'] == 'offer' and message['offer_type'] == 'connection' and message['connection_type'] == 'wifi' and message['connection_scope'] == 'WAN' and message['traffic_price'] == 0:
						if self.verbose:
							print "Found it:", message
						self.negotiation_stage = "sending demand"
						self.negotiation_party = message['message_source']
				if self.negotiation_stage == "waiting for demand answer" and message['message_type'] == 'contract_unilateral' and message['contract_type'] == 'connection' and message['connection_type'] == 'wifi' and message['connection_scope'] == 'WAN' and message['traffic_price'] == 0 and message['contract_length'] == self.requested_service_time:
					self.negotiation_stage = "signing contract"
				if self.negotiation_stage == "being served" and message['message_type'] == 'service_token':
					self.received_tokens += 1
					if self.received_tokens >= self.requested_service_time:
						self.negotiation_stage = "happy"
				
def main():
	combus = CommunicationBus(name = "Common Communication Bus", verbose = False)

	cmu_ap = WifiAP(BSSID = "12:34:56:78:90:AB", SSID = "CMU WiFi", communication_bus = combus, connection_scope = "WAN", connection_speed = 14400, traffic_price = 0, signal_strength = -40, verbose = True)

	crossmobile_ap = WifiAP(BSSID = "21:43:65:87:09:BA", SSID = "Cross Mobile WiFi", communication_bus = combus, connection_scope = "LAN", connection_speed = 192000, traffic_price = 0, signal_strength = -60, verbose = False)

	client = FreeWifiWanter(MAC = 'AB:CD:EF:FE:DC:BA', communication_bus = combus, verbose = True, requested_service_time = 3, requested_bandwight = 1234)

	client2 = FreeWifiWanter(MAC = 'BA:CD:EF:FE:DC:BA', communication_bus = combus, verbose = True, requested_service_time = 10, requested_bandwight = 12100)


	entities = [cmu_ap, crossmobile_ap, client, client2]

	while True:
		for entity in entities:
			entity.talk()
		for entity in entities:
			entity.listen()
		for entity in entities:
			entity.tick()
		combus.tick()
		print "\n"
		time.sleep(0.5)

if __name__ == "__main__":
	main()
