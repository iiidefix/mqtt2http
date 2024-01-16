import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, parse_qsl
import logging, json


class httpSrv:
	def __init__(self, host, port, mqttClient):
		self._log = logging.getLogger(__name__)

		self.host = host
		self.port = port

		if ":" in host:
			self._httpd = HTTPServerV6((host, port), handlerFunc(mqttClient))
		else:
			self._httpd = HTTPServer((host, port), handlerFunc(mqttClient))


	def start(self):
		self._log.warning("Start HTTP server on %s:%s", self.host, self.port)
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
				path, query = path.split('?', 1)
				qs = {k: v[0] for k, v in parse_qs(query).items()}

			action = path.lstrip("/").split("/", 1)[0]

			if not action:
				self.path = '../index.html'
				return SimpleHTTPRequestHandler.do_GET(self)

			if action in self.__actions:
				self._actions(action, qs)
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
				path, query = path.split('?', 1)
				qs = {k: v[0] for k, v in parse_qs(query).items()}

			action = path.lstrip("/").split("/", 1)[0]

			if not action:
				self._log.error("POST Path missing")
				self._send_error(500, '{"status":"endpoint_missing"}')
				return

			try:
				json_body = json.loads(body if body else "{}")
			except:
				self._log.error("Json data invalid")
				self._send_error(500, '{"status":"json_data_invalid"}')
				return

			if action in self.__actions:
				self._actions(action, json_body | qs)
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
				self._send_json(json.dumps(mqttClient.listSubsriptions()))

			elif action == "subscribe":
				if 'topic' in data and 'url' in data:
					data = {"qos": 0, "method": "POST"} | data
					uuid = mqttClient.subscribeWebhook(data["topic"], data["url"], data["qos"], data["method"])
					self._send_json(f'{{"status":"ok","uuid":"{uuid}"}}')
				else:
					self._send_error(500, '{"status":"data-missing"}')

			elif action == "unsubscribe":
				if 'uuid' in data:
					mqttClient.unsubscribeWebhook(data["uuid"])
					self._send_json('{"status":"ok"}')
				else:
					self._send_error(500, '{"status":"data-missing"}')

			elif action == "publish":
				if "topic" in data and "data" in data:
					self._log.info("Publish: %s <=> '%s'", data["topic"], data["data"])
					mqttClient.publish(data["topic"], data["data"], int(data['qos']) if 'key' in data else 0, bool(data['retain']) if 'retain' in data else False)
					self._send_json('{"status":"ok"}')
				else:
					self._log.error("POST publish data missing")
					self._send_error(500, '{"status":"data-missing"}')

	return reqHandler