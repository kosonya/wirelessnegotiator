#!/usr/bin/python

from Entity import Entity
import json

class Provider(Entity):
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
			elif self.partners[partner]["negotiation_stage"] == "serving":
				if self.partners[partner]["remaining_cycles"] > 0:
					send_message = {'message_type': 'service_token', 'service_type': 'connection', 'connection_scope': self.connection_scope, 'connection_speed': self.partners[partner]["serving_bandwidth"], 'traffic_price': self.partners[partner]["price"], 'connection_type': 'wifi',  'message_source': self.BSSID, 'message_destination': partner}
					send_message_str = json.dumps(send_message)
					self.combus.send(send_message_str)
					self.partners[partner]["remaining_cycles"] -= 1
				else:
					self.available_bandwidth += self.partners[partner]["serving_bandwidth"]
					del self.partners[partner]
			elif self.partners[partner]["negotiation_stage"] == "demand_rejected":
				if self.partners[partner]["can_ask_later"]:
					send_message = {"message_type": "demand_rejected", "rejection_reason": "not_enough_bandwidth", "can_ask_later": True, "cycles_to_wait_before_asking": 2,'message_source': self.BSSID, 'message_destination': partner}
				else:
					send_message = {"message_type": "demand_rejected", "rejection_reason": "not_enough_bandwidth", "can_ask_later": False, 'message_source': self.BSSID, 'message_destination': partner}
				send_message_str = json.dumps(send_message)
				self.combus.send(send_message_str)
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
				if message['message_type'] == 'demand' and message['connection_type'] == 'wifi' and message['requested_price'] >= self.traffic_price and message['message_source'] not in self.partners.keys():
					if message['requested_bandwight'] <= self.available_bandwidth:
						self.partners[message['message_source']] = {"negotiation_stage": "contract_offered", "serving_bandwidth": message['requested_bandwight'], "remaining_cycles": message['requested_time'], "price":message['requested_price']}
						self.available_bandwidth -= message['requested_bandwight']
					else:
						if message['requested_bandwight'] <= self.connection_speed:
							self.partners[message['message_source']] = {"negotiation_stage": "demand_rejected", "rejection_reason": "not_enough_bandwidth", "can_ask_later": True, "cycles_to_wait_before_asking": 2} #FIXME -- need a better algorithm of computing cycles_to_wait_before_asking
						else:
							self.partners[message['message_source']] = {"negotiation_stage": "demand_rejected", "rejection_reason": "not_enough_bandwidth", "can_ask_later": False}
				if message['message_type'] == 'contract_signed' and message['message_source'] in self.partners.keys() and self.partners[message['message_source']]["negotiation_stage"] ==  "contract_offered":
					self.partners[message['message_source']]["negotiation_stage"] = "serving"
