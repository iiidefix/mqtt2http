from mqtt2http.mqttClt import mqttClt
from mqtt2http.httpSrv import httpSrv
import sys, os, logging, json, threading, signal


def main():
	# MQTT Configuration
	MQTT_HOST = os.environ.get('MQTT_HOST', 'localhost')
	MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
	MQTT_USER = os.environ.get('MQTT_USER')
	MQTT_PASS = os.environ.get('MQTT_PASS')

	# HTTP Configuration
	HTTP_BIND = os.environ.get('HTTP_BIND', '127.0.0.1')
	HTTP_PORT = int(os.environ.get('HTTP_PORT', 8080))


	''' Start mqtt client '''
	mqttCltObj = mqttClt(MQTT_HOST, port=MQTT_PORT, username=MQTT_USER, password=MQTT_PASS)


	''' Start http server '''
	httpSrvObj = httpSrv(HTTP_BIND, HTTP_PORT, mqttCltObj)
	httpSrvThread = threading.Thread(name='httpSrv', target=httpSrvObj.start)
	httpSrvThread.start()


	''' Load startup.json '''
	file = os.path.realpath(os.path.dirname(__file__) + '/startup.json')
	if os.path.exists(file):
		try:
			f = open(file)
			d = json.load(f)
			f.close()
		except:
			logging.error("Json data invalid")
			d = {}

		for uuid in d:
			hook = d[uuid]
			if all(key in hook for key in ["topic", "qos", "url", "method"]):
				mqttCltObj.subscribeWebhook(hook["topic"], hook["url"], hook["qos"], hook["method"], uuid)



	signal.signal(signal.SIGINT, lambda signum, frame: signal_handler(signum, frame, mqttCltObj, httpSrvObj))
	print('Press Ctrl+C to shutdown')

	forever = threading.Event()
	forever.wait()

def signal_handler(signal, frame, mqttCltObj, httpSrvObj):
	httpSrvObj.cleanup()
	mqttCltObj.disconnect()
	sys.exit(0)

if __name__ == "__main__":
	main()
