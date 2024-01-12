# mqtt2http

A simple MQTT to HTTP bridge.

## need to know

- URL parameter take precedence over POST data.
- No checks for duplicates: subscriping to the same topic multiple times with the same url will cause duplicate incocations of that url.
- PUT publishes data unchecked to topic in URL.



## configuration

environment variables with default values:
- mqtt-client:
	- `MQTT_HOST`="127.0.0.1"
	- `MQTT_PORT`=1883
	- `MQTT_USER`=""
	- `MQTT_PASS`=""
- http-server:
	- `HTTP_BIND`="::"
	- `HTTP_PORT`=8080



## example requests

### publish
```bash
curl --header "Content-Type: application/json" --request PUT --data '{"Protocol":"SAMSUNG","Bits":32,"Data":"0xE0E0E01F"}' http://127.0.0.1:8080/cmnd/tasmota_5C4C7B/IRSend
```
```json
{"status":"ok"}
```

--- --- --- --- --- --- --- --- ---

```bash
curl --header "Content-Type: application/json" --request PUT --data '{"Protocol":"SAMSUNG","Bits":32,"Data":"0xE0E0D02F"}' http://127.0.0.1:8080/cmnd/tasmota_5C4C7B/IRSend
```
```json
{"status":"ok"}
```

--- --- --- --- --- --- --- --- ---

```bash
curl --header "Content-Type: text/plain" --request PUT --data 'ON' http://127.0.0.1:8080/cmnd/tasmota_24D0BE/Power1
```
```json
{"status":"ok"}
```

--- --- --- --- --- --- --- --- ---

```bash
curl --header "Content-Type: text/plain" --request PUT --data 'OFF' http://127.0.0.1:8080/cmnd/tasmota_24D0BE/Power1
```
```json
{"status":"ok"}
```

--- --- --- --- --- --- --- --- ---

```bash
curl --header "Content-Type: text/plain" --request PUT --data 'TOGGLE' http://127.0.0.1:8080/cmnd/tasmota_24D0BE/Power1
```
```json
{"status":"ok"}
```

--- --- --- --- --- --- --- --- ---

```bash
curl --header "Content-Type: application/json" --request POST --data '{"topic":"cmnd/tasmota_24D0BE/Power1","data":"TOGGLE"}' http://127.0.0.1:8080/publish
```
```json
{"status":"ok"}
```

--- --- --- --- --- --- --- --- ---

```bash
wget -qO- 'http://127.0.0.1:8080/publish?topic=cmnd/tasmota_24D0BE/Power1&data=toggle'
```
```json
{"status":"ok"}
```



### subscribe
```bash
curl 'http://127.0.0.1:8080/subscribe?topic=cmnd/tasmota_24D0BE/Power1&url=http://127.0.0.1/webhook.php'
```
```json
{"status":"ok","uuid":"fd940b12-b0dc-11ee-a34b-0050568e206e"}
```

--- --- --- --- --- --- --- --- ---


```bash
curl --header "Content-Type: application/json" --request POST --data '{"topic":"tele/tasmota_5C4C7B/RESULT","url":"http://127.0.0.1/webhook.php"}' http://127.0.0.1:8080/subscribe
```
```json
{"status":"ok","uuid":"1229f816-b0dd-11ee-a34b-0050568e206e"}
```

--- --- --- --- --- --- --- --- ---

```bash
curl --header "Content-Type: application/json" --request POST --data '{"topic":"tele/tasmota_5C4C7B/RESULT"}' http://127.0.0.1:8080/subscribe?url=http://127.0.0.1/webhook.php
```
```json
{"status":"ok","uuid":"12c8c0cc-b0dd-11ee-a34b-0050568e206e"}
```

--- --- --- --- --- --- --- --- ---

```bash
curl --header "Content-Type: application/json" --request POST --data '' 'http://127.0.0.1:8080/subscribe?topic=tele/tasmota_5C4C7B/RESULT&url=http://127.0.0.1/webhook.php'
```
```json
{"status":"ok","uuid":"136827e8-b0dd-11ee-a34b-0050568e206e"}
```



### unsubscribe
```bash
curl 'http://127.0.0.1:8080/unsubscribe?uuid=fd940b12-b0dc-11ee-a34b-0050568e206e'
```
```json
{"status":"ok"}
```

--- --- --- --- --- --- --- --- ---

```bash
curl --header "Content-Type: application/json" --request POST --data '{"uuid":"a5505e72-b0d9-11ee-b9b3-0050568e206e"}' http://127.0.0.1:8080/unsubscribe
```
```json
{"status":"ok"}
```



### list subscription webhooks
```bash
curl http://127.0.0.1:8080/list | jq
```
```json
{
  "fd940b12-b0dc-11ee-a34b-0050568e206e": {
    "topic": "cmnd/tasmota_24D0BE/Power1",
    "qos": 0,
    "url": "http://127.0.0.1/webhook.php",
    "method": "POST"
  },
  "1229f816-b0dd-11ee-a34b-0050568e206e": {
    "topic": "cmnd/tasmota_24D0BE/Power1",
    "qos": 0,
    "url": "http://127.0.0.1/webhook.php",
    "method": "POST"
  },
  "12c8c0cc-b0dd-11ee-a34b-0050568e206e": {
    "topic": "cmnd/tasmota_24D0BE/Power1",
    "qos": 0,
    "url": "http://127.0.0.1/webhook.php",
    "method": "POST"
  },
  "136827e8-b0dd-11ee-a34b-0050568e206e": {
    "topic": "cmnd/tasmota_24D0BE/Power1",
    "qos": 0,
    "url": "http://127.0.0.1/webhook.php",
    "method": "POST"
  }
}
```



### save subscription webhooks for next startup
```bash
curl http://127.0.0.1:8080/list > startup.json
```
```bash
wget -O startup.json http://127.0.0.1:8080/list
```