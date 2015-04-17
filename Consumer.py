#!/usr/bin/python

from Entity import Entity
import json

class Consumer(Entity):
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
		if self.negotiation_stage == "waiting to ask again":
			if self.cycles_to_wait_before_asking > 0:
				self.cycles_to_wait_before_asking -= 1
			else:
				self.negotiation_stage = "looking for partners"
		if self.verbose:
			self.show()

	def show(self):
		if self.negotiation_stage == "waiting to ask again":
			print "\n", self.MAC, ";negotiation stage:", self.negotiation_stage, ";negotiation party:", self.negotiation_party, ";received tokens:", self.received_tokens,  "cycles_to_wait_before_asking:", self.cycles_to_wait_before_asking
		else:
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
				if self.negotiation_stage == "waiting for demand answer":
					if message['message_type'] == 'contract_unilateral' and message['contract_type'] == 'connection' and message['connection_type'] == 'wifi' and message['connection_scope'] == 'WAN' and message['traffic_price'] == 0 and message['contract_length'] == self.requested_service_time:
						self.negotiation_stage = "signing contract"
					elif message['message_type'] == "demand_rejected" and message["can_ask_later"]:
						self.negotiation_stage = "waiting to ask again"
						self.cycles_to_wait_before_asking = message["cycles_to_wait_before_asking"]
				if self.negotiation_stage == "being served" and message['message_type'] == 'service_token':
					self.received_tokens += 1
					if self.received_tokens >= self.requested_service_time:
						self.negotiation_stage = "happy"
		
