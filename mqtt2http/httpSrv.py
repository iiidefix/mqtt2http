import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, parse_qsl
import logging, json


class httpSrv:
	def __init__(self, host, port, mqttClient):
		self._log = logging.getLogger(__name__)

		self.port = port
		self.host = host

		self.__reqHandle = handlerFunc(mqttClient)
		if ":" in host:
			self._httpd = HTTPServerV6((host, port), self.__reqHandle)
		else:
			self._httpd = HTTPServer((host, port), self.__reqHandle)


	def start(self):
		self._log.warning("Start HTTP server on %s:%s",self.host,self.port)
		self._httpd.serve_forever()

	def cleanup(self):
		self._httpd.shutdown()
		self._log.info("HTTP server is down")

class HTTPServerV6(HTTPServer):
	address_family = socket.AF_INET6

def handlerFunc(mqttClient):
	class reqHandler(SimpleHTTPRequestHandler):
		def log_message(self, *args):
			pass

		def do_GET(self):
			self._log = logging.getLogger(__name__)

			qs = {}
			path = self.path
			if '?' in path:
				path, tmp = path.split('?', 1)
				qs = parse_qs(tmp)
				for p in qs:
					qs[p] = qs[p][0]

			pathArray = []
			for data in path.split("/"):
				if data:
					pathArray.append(data)


			if len(pathArray) == 0:
				self.path = '../README.md'
				return SimpleHTTPRequestHandler.do_GET(self)

			if pathArray[0] in self.__actions:
				self._actions(pathArray[0], qs)
				return

			else:
				self._log.warning("GET Path not found %s", self.path)
				self._send_error(404, '{"status":"not_found"}')


		def do_POST(self):
			self._log = logging.getLogger(__name__)

			content_len = int(self.headers.get('Content-Length'))
			body = self.rfile.read(content_len).decode('utf-8')

			qs = {}
			path = self.path
			if '?' in path:
				path, tmp = path.split('?', 1)
				qs = parse_qs(tmp)
				for p in qs:
					qs[p] = qs[p][0]

			pathArray = []
			for data in path.split("/"):
				if data:
					pathArray.append(data)

			if len(pathArray) == 0:
				self._log.error("POST Path missing")
				self._send_error(500, '{"status":"endpoint_missing"}')
				return

			if len(body) == 0:
				body = "{}"
			try:
				json_content = json.loads(body)
			except:
				self._log.error("Json data invalid")
				self._send_error(500, '{"status":"json_data_invalid"}')
				return

			if pathArray[0] in self.__actions:
				self._actions(pathArray[0], json_content | qs)
				return

			else:
				self._log.warning("POST Path not found %s", self.path)
				self._send_error(404, '{"status":"not_found"}')

		def do_PUT(self):
			self._log = logging.getLogger(__name__)
			self._log.setLevel(logging.INFO)

			topic = self.path.strip("/")
			content_len = int(self.headers.get('Content-Length'))
			body = self.rfile.read(content_len).decode('utf-8')

			self._log.info("Publish: %s <=> '%s'", topic, body)
			mqttClient.publish(topic, body)
			self._send_json('{"status":"ok"}')

		def do_OPTIONS(self) :
			self.send_response(200)
			self.send_header('Content-type', 'application/json')
			self._send_cors_headers()
			self.send_header("Access-Control-Allow-Headers", "accept, Content-Type")
			self.end_headers()


		def _send_cors_headers(self):
			self.send_header("Access-Control-Allow-Origin", "*")
			self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT")
			self.send_header("Access-Control-Allow-Headers", "Content-Type")


		def _send_text(self, data):
			self.send_response(200)
			self.send_header('Content-type', 'text/plain')
			self._send_cors_headers()
			self.end_headers()

			self.wfile.write(data.encode('utf-8'))

		def _send_json(self, data):
			self.send_response(200)
			self.send_header('Content-type', 'application/json')
			self._send_cors_headers()
			self.end_headers()

			self.wfile.write(data.encode('utf-8'))

		def _send_error(self, err, data):
			self.send_response(err)
			self.send_header('Content-type', 'application/json')
			self._send_cors_headers()
			self.end_headers()

			self.wfile.write(data.encode('utf-8'))


		__actions = ["list", "subscribe", "unsubscribe", "publish"]

		def _actions(self, action, data):
			if action == "list":
				self._send_json(json.dumps(mqttClient._subscriptions))
				return

			elif action == "subscribe":
				if 'topic' in data and 'url' in data:
					data = {"qos":0, "method": "POST"} | data
					uuid = mqttClient.subscribeWebhook(data["topic"], data["url"], data["qos"], data["method"])
					self._send_json(f'{{"status":"ok","uuid":"{uuid}"}}')
					return
				else:
					self._send_error(500, '{"status":"data-missing"}')
					return

			elif action == "unsubscribe":
				if 'uuid' in data:
					mqttClient.unsubscribeWebhook(data["uuid"])
					self._send_json('{"status":"ok"}')
					return
				else:
					self._send_error(500, '{"status":"data-missing"}')
					return

			elif action == "publish":
				if "topic" in data and "data" in data:
					self._log.info("Publish: %s <=> '%s'", data["topic"], data["data"])
					mqttClient.publish(data["topic"], data["data"])
					self._send_json('{"status":"ok"}')
					pass
				else:
					self._log.error("POST publish data missing")
					self._send_error(500, '{"status":"data-missing"}')
					return

	return reqHandler