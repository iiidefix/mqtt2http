import paho.mqtt.client as mqtt
import logging, uuid as uuidGen
import requests
import sys, os

class mqttClt:
	def __init__(self, host, port = 1883, username = "", password = "", tls_cert= "", tls_ver="", tls_insecure=True, keepalive = 5):
		self._log = logging.getLogger(__name__)

		self._mqtt = mqtt.Client()

		if username:
			self._mqtt.username_pw_set(username=username, password=password)

		if tls_cert:
			try:
				self._mqtt.tls_set(tls_cert, tls_version=tls_ver)
			except:
				self._log.error("Could not set tls")
			self._mqtt.tls_insecure_set(tls_insecure)

		self._log.info("Connecting to %s:%s@%s:%i", username, password, host, port)

		self._mqtt.on_connect = self.on_connect
		self._mqtt.on_disconnect = self.on_disconnect
		self._mqtt.on_message = self.on_message

		try:
			self._mqtt.connect(host, port, keepalive)
		except:
			self._log.error("Could not connect to mqtt server")
			sys.exit(0)

		self._mqtt.loop_start()

		self._subscriptions = {}



	def on_connect(self, client, userdata, flags, rc):
		''' on_connect callback '''
		self._log.info("MQTT connected with result code " + str(rc))
		self._mqtt._connected = True

	def on_disconnect(self, client, userdata, rc):
		''' on_disconnect callback '''
		self._log.info("MQTT disconnected")
		self._mqtt._connected = False

	def on_message(self, client, userdata, message):
		''' on_message callback '''
		for uuid in self._subscriptions:
			hook = self._subscriptions[uuid]
			if hook["topic"] == message.topic:
				r = requests.request(method=hook["method"], url=hook["url"], data=message.payload)
				self._log.info("Request: %s %d %s", uuid, r.status_code, r.request.url)



	def disconnect(self):
		self._mqtt.disconnect()

	def publish(self, topic, data):
		self._mqtt.publish(topic, data)



	def subscribeWebhook(self, topic, url, qos=0, method="POST", uuid=None):
		''' subscribe to a topic and stores the webhook '''

		uuid = uuid if uuid else str(uuidGen.uuid1())

		if not uuid in self._subscriptions:
			self._subscriptions[uuid] = {
				"topic" : topic,
				"qos": qos,
				"url" : url,
				"method" : method
			}
			self._mqtt.subscribe(topic, qos)
			return uuid
		else:
			self._log.error("Dublicate uuid in webhook subscriptions. This really should not happen. %s", uuid)

	def unsubscribeWebhook(self, uuid):
		if uuid in self._subscriptions:
			self._mqtt.unsubscribe(self._subscriptions[uuid]["topic"])
			del self._subscriptions[uuid]
		else:
			self._log.warn("uuid not in webhook subscriptions. %s", uuid)
