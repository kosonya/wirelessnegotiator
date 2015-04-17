#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import time
from Consumer import Consumer
from CommunicationBus import CommunicationBus
from Provider import Provider

def main():
	combus = CommunicationBus(name = "Common Communication Bus", verbose = False)

	cmu_ap = Provider(BSSID = "12:34:56:78:90:AB", SSID = "CMU WiFi", communication_bus = combus, connection_scope = "WAN", connection_speed = 14400, traffic_price = 0, signal_strength = -40, verbose = True)

	crossmobile_ap = Provider(BSSID = "21:43:65:87:09:BA", SSID = "Cross Mobile WiFi", communication_bus = combus, connection_scope = "LAN", connection_speed = 192000, traffic_price = 0, signal_strength = -60, verbose = False)

	client = Consumer(MAC = 'AB:CD:EF:FE:DC:BA', communication_bus = combus, verbose = True, requested_service_time = 3, requested_bandwight = 1234)

	client2 = Consumer(MAC = 'BA:CD:EF:FE:DC:BA', communication_bus = combus, verbose = True, requested_service_time = 10, requested_bandwight = 12100)

	client3 = Consumer(MAC = '11:CD:FE:FE:DC:BA', communication_bus = combus, verbose = True, requested_service_time = 10, requested_bandwight = 2100)

	client4 = Consumer(MAC = '12:CD:FE:FE:DC:BA', communication_bus = combus, verbose = True, requested_service_time = 7, requested_bandwight = 2100)

	client5 = Consumer(MAC = '13:CD:FE:FE:DC:BA', communication_bus = combus, verbose = True, requested_service_time = 3, requested_bandwight = 12100)

	client6 = Consumer(MAC = '14:CD:FE:FE:DC:BA', communication_bus = combus, verbose = True, requested_service_time = 12, requested_bandwight = 22100)

	client7 = Consumer(MAC = '15:CD:FE:FE:DC:BA', communication_bus = combus, verbose = True, requested_service_time = 6, requested_bandwight = 2100)


	entities = [cmu_ap, crossmobile_ap, client, client2, client3, client4, client5, client6, client7]

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
