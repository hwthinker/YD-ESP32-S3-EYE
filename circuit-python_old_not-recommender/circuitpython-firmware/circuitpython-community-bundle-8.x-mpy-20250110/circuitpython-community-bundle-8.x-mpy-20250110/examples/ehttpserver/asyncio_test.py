import board
import time
import wifi
import mdns
import socketpool
import digitalio
import asyncio

from ehttpserver import Server, Response, route

class MyServer(Server):

  # --- request-handler for /   -----------------------------------------------

  @route("/","GET")
  def _handle_main(self,path,query_params, headers, body):
    """ handle request for main-page """
    return Response("<b>Hello, world!</b>", content_type="text/html")

  # --- run AP   -------------------------------------------------------------

  def start_ap(self):
    """ start AP-mode """

    wifi.radio.stop_station()
    try:
      wifi.radio.start_ap(ssid="my_ssid",password="my_password")
    except NotImplementedError:
      # workaround for older CircuitPython versions
      pass

  # --- run server   ---------------------------------------------------------

  def run_server(self):

    server = mdns.Server(wifi.radio)
    server.hostname = "myhostname"
    server.advertise_service(service_type="_http",
                             protocol="_tcp", port=80)
    pool = socketpool.SocketPool(wifi.radio)
    print(f"starting {server.hostname}.local ({wifi.radio.ipv4_address_ap})")
    with pool.socket() as server_socket:
      yield from self.start(server_socket)

# --- some helper functions   ------------------------------------------------

# minimal implementation of asyncio.sleep() as a generator
def asyncio_sleep(seconds):
  start_time = time.monotonic()
  while time.monotonic() - start_time < seconds:
    yield

# blink LED
async def blink_builtin_led():
  with digitalio.DigitalInOut(board.LED) as led:
    led.switch_to_output(value=False)
    while True:
      led.value = not led.value
      await asyncio.sleep(0.1)

async def run_my_server(server):
  for _ in server.run_server():
    await asyncio.sleep(0)

# --- main execution loop   --------------------------------------------------

myserver = MyServer()
myserver.start_ap()

# run both coroutines at the same time
print(f"Listening on http://{wifi.radio.ipv4_address_ap}:80")
asyncio.run(asyncio.gather(blink_builtin_led(), run_my_server(myserver)))
