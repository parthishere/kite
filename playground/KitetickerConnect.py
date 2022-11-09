import logging
from kiteconnect import KiteTicker
from playground import kiteconnect, constants

logging.basicConfig(level=logging.DEBUG)

kws = KiteTicker(constants.KITE_API_KEY, "tTWqR8Yn6hK6ltOXNLAWMqY9sBvXO8eZ")
# Initialise

def startConnection(token):
    print("My Toek n" + token)
    kws = KiteTicker(constants.KITE_API_KEY, token)

def on_ticks(ws, ticks):
    # Callback to receive ticks.
    logging.debug("Ticks: {}".format(ticks))

def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    ws.subscribe([738561, 5633])

    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_FULL, [738561])

def on_close(ws, code, reason):
    # On connection close stop the event loop.
    # Reconnection will not happen after executing `ws.stop()`
    ws.stop()

# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
kws.connect(threaded=True)