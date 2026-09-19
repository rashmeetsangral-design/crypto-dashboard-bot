import requests
import time
import websocket
import json
import threading


# ==================================================
# TELEGRAM SETTINGS
# ==================================================

BOT_TOKEN = import os"8935907911:AAGxfd0XDQFU4b_UeWzc1o3j1PGfMdr0hpA"
CHAT_ID = import os"7945412116"

# ==================================================
# TEST TELEGRAM BOT TOKEN
# ==================================================

def test_telegram_token():

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"

    try:

        response = requests.get(
            url,
            timeout=10
        )

        print(
            "🤖 Telegram Token Test:",
            response.json()
        )

    except Exception as error:

        print(
            "🔴 Telegram Test Error:",
            error
        )


test_telegram_token()


# ==================================================
# PRICE ALERT SETTINGS
# ==================================================

BTC_HIGH = 76000
BTC_LOW = 75000

ETH_HIGH = 2450
ETH_LOW = 2350


# ==================================================
# VOLUME ALERT SETTINGS
# ==================================================

VOLUME_SPIKE_RATIO = 1.0

last_volume_alert = False

# Stores previous completed candle volumes
volume_history = []

# Stores the timestamp of the current live candle
current_candle_time = None

ETH_VOLUME_SPIKE_RATIO = 2.0

last_eth_volume_alert = False
eth_volume_history = []
current_eth_candle_time = None


# ==================================================
# ALERT STATUS
# ==================================================

btc_high_sent = False
btc_low_sent = False

eth_high_sent = False
eth_low_sent = False


# ==================================================
# GET BTC PRICE
# ==================================================

def get_btc_price():

    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"

    response = requests.get(url, timeout=10)

    data = response.json()

    return data["price"]


# ==================================================
# GET ETH PRICE
# ==================================================

def get_eth_price():

    url = "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT"

    response = requests.get(url, timeout=10)

    data = response.json()

    return data["price"]


# ==================================================
# SEND TELEGRAM MESSAGE
# ==================================================

def send_message(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:

        response = requests.post(
            url,
            data=data,
            timeout=10
        )

        print(
            "Telegram:",
            response.json()
        )

    except Exception as error:

        print(
            "🔴 Telegram Error:",
            error
        )


# ==================================================
# CHECK VOLUME SPIKE
# ==================================================

def check_volume_spike(
    current_volume,
    average_volume
):

    global last_volume_alert

    if average_volume <= 0:

        return

    volume_ratio = (
        current_volume
        / average_volume
    )

    print(
        "📊 Bot Volume Ratio:",
        f"{volume_ratio:.2f}x"
    )

    # ----------------------------------------------
    # VOLUME SPIKE ALERT
    # ----------------------------------------------

    if (
        volume_ratio >= VOLUME_SPIKE_RATIO
        and not last_volume_alert
    ):

        send_message(
            f"🚨 BTC VOLUME SPIKE!\n\n"
            f"💰 BTC Volume: "
            f"{current_volume:,.0f}\n"
            f"📊 Average Volume: "
            f"{average_volume:,.0f}\n"
            f"🔥 Volume Ratio: "
            f"{volume_ratio:.2f}x\n\n"
            f"⚡ Volume is above "
            f"{VOLUME_SPIKE_RATIO:.1f}x average"
        )

        last_volume_alert = True

    # ----------------------------------------------
    # RESET ALERT
    # ----------------------------------------------

    if volume_ratio < VOLUME_SPIKE_RATIO:

        last_volume_alert = False

# ==================================================
# CHECK ETH VOLUME SPIKE
# ==================================================

def check_eth_volume_spike(
    current_volume,
    average_volume
):

    global last_eth_volume_alert

    if average_volume <= 0:

        return

    volume_ratio = (
        current_volume
        / average_volume
    )

    print(
        "📊 ETH Volume Ratio:",
        f"{volume_ratio:.2f}x"
    )

    if (
        volume_ratio >= ETH_VOLUME_SPIKE_RATIO
        and not last_eth_volume_alert
    ):

        send_message(

            f"🚨 ETH VOLUME SPIKE!\n\n"
            f"💰 ETH Volume: "
            f"{current_volume:,.0f}\n"
            f"📊 Average Volume: "
            f"{average_volume:,.0f}\n"
            f"🔥 Volume Ratio: "
            f"{volume_ratio:.2f}x\n\n"
            f"⚡ Volume is above "
            f"{ETH_VOLUME_SPIKE_RATIO:.1f}x average"
        )

        last_eth_volume_alert = True

    if volume_ratio < ETH_VOLUME_SPIKE_RATIO:

        last_eth_volume_alert = False

# ==================================================
# LOAD RECENT ETH VOLUME HISTORY
# ==================================================

def load_eth_volume_history():

    global eth_volume_history

    url = (
        "https://api.india.delta.exchange"
        "/v2/history/candles"
    )

    end_time = int(time.time())

    start_time = (
        end_time
        - (25 * 60 * 60)
    )

    params = {
        "resolution": "1h",
        "symbol": "ETHUSD",
        "start": start_time,
        "end": end_time
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        print(
            "📡 ETH History API Status:",
            response.status_code
        )

        data = response.json()

        candles = data.get(
            "result",
            []
        )

        eth_volume_history.clear()

        candles = sorted(
            candles,
            key=lambda candle:
                candle.get("time", 0)
        )

        for candle in candles:

            volume = float(
                candle.get(
                    "volume",
                    0
                )
            )

            if volume > 0:

                eth_volume_history.append(
                    volume
                )

        if len(eth_volume_history) > 20:

            eth_volume_history = (
                eth_volume_history[-20:]
            )

        print(
            "📚 Loaded ETH Volume History:",
            len(eth_volume_history),
            "candles"
        )

    except Exception as error:

        print(
            "🔴 ETH Volume History Error:",
            error
        )

# ==================================================
# LOAD RECENT BTC VOLUME HISTORY
# ==================================================

def load_volume_history():

    global volume_history

    url = (
        "https://api.india.delta.exchange"
        "/v2/history/candles"
    )

    end_time = int(time.time())

    # Load 25 hours so we have enough candles
    start_time = (
        end_time
        - (25 * 60 * 60)
    )

    params = {
        "resolution": "1h",
        "symbol": "BTCUSD",
        "start": start_time,
        "end": end_time
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        print(
            "📡 History API Status:",
            response.status_code
        )

        data = response.json()

        candles = data.get(
            "result",
            []
        )

        volume_history.clear()

        # Sort candles from old → new
        candles = sorted(
            candles,
            key=lambda candle:
                candle.get("time", 0)
        )

        for candle in candles:

            volume = float(
                candle.get(
                    "volume",
                    0
                )
            )

            if volume > 0:

                volume_history.append(
                    volume
                )

        # Keep only latest 20
        if len(volume_history) > 20:

            volume_history = (
                volume_history[-20:]
            )

        print(
            "📚 Loaded Volume History:",
            len(volume_history),
            "candles"
        )

    except Exception as error:

        print(
            "🔴 Volume History Error:",
            error
        )


# ==================================================
# DELTA LIVE BTC + ETH VOLUME STREAM
# ==================================================

def delta_volume_stream():

    global current_candle_time
    global volume_history

    global current_eth_candle_time
    global eth_volume_history

    # ----------------------------------------------
    # WEBSOCKET MESSAGE
    # ----------------------------------------------

    def on_message(ws, message):

        global current_candle_time
        global volume_history

        global current_eth_candle_time
        global eth_volume_history

        try:

            data = json.loads(message)

            # Only process 1H candle messages
            if data.get("type") != "candlestick_1h":

                return

            symbol = data.get("sy")

            current_volume = float(
                data.get("v", 0)
            )

            candle_time = data.get(
                "ts",
                data.get("cst", 0)
            )

            # ======================================
            # BTC
            # ======================================

            if symbol == "BTCUSD":

                print(
                    "📊 Delta BTC Volume:",
                    f"{current_volume:,.0f}"
                )

                if (
                    current_volume > 0
                    and len(volume_history) >= 20
                ):

                    average_volume = (
                        sum(volume_history)
                        / len(volume_history)
                    )

                    check_volume_spike(
                        current_volume,
                        average_volume
                    )

                if candle_time != current_candle_time:

                    current_candle_time = candle_time

                    print(
                        "🕐 New BTC 1H Candle Detected"
                    )

            # ======================================
            # ETH
            # ======================================

            elif symbol == "ETHUSD":

                print(
                    "📊 Delta ETH Volume:",
                    f"{current_volume:,.0f}"
                )

                if (
                    current_volume > 0
                    and len(eth_volume_history) >= 20
                ):

                    average_eth_volume = (
                        sum(eth_volume_history)
                        / len(eth_volume_history)
                    )

                    check_eth_volume_spike(
                        current_volume,
                        average_eth_volume
                    )

                if (
                    candle_time
                    != current_eth_candle_time
                ):

                    current_eth_candle_time = candle_time

                    print(
                        "🕐 New ETH 1H Candle Detected"
                    )

        except Exception as error:

            print(
                "🔴 Volume Error:",
                error
            )


    # ----------------------------------------------
    # WEBSOCKET OPEN
    # ----------------------------------------------

    def on_open(ws):

        print(
            "🟢 Delta BTC + ETH Volume WebSocket Connected"
        )

        subscribe_message = {

            "type": "subscribe",

            "payload": {

                "channels": [

                    {
                        "name": "candlestick_1h",
                        "symbols": [
                            "BTCUSD",
                            "ETHUSD"
                        ]
                    }

                ]

            }

        }

        ws.send(
            json.dumps(
                subscribe_message
            )
        )


    # ----------------------------------------------
    # WEBSOCKET ERROR
    # ----------------------------------------------

    def on_error(ws, error):

        print(
            "🔴 Delta WebSocket Error:",
            error
        )


    # ----------------------------------------------
    # WEBSOCKET CLOSED
    # ----------------------------------------------

    def on_close(
        ws,
        close_status_code,
        close_msg
    ):

        print(
            "🔴 Delta Volume WebSocket Closed"
        )


    # ----------------------------------------------
    # CREATE WEBSOCKET
    # ----------------------------------------------

    ws = websocket.WebSocketApp(

        "wss://public-socket.india.delta.exchange",

        on_open=on_open,

        on_message=on_message,

        on_error=on_error,

        on_close=on_close
    )

    ws.run_forever()

# ==================================================
# START BOT
# ==================================================

print(
    "🟢 Crypto Dashboard Bot Started"
)


# ==================================================
# LOAD VOLUME HISTORY
# ==================================================

load_volume_history()
load_eth_volume_history()


# ==================================================
# START DELTA VOLUME THREAD
# ==================================================

volume_thread = threading.Thread(

    target=delta_volume_stream,

    daemon=True
)

volume_thread.start()


# ==================================================
# MAIN LOOP
# ==================================================


while True:

    try:

        # ------------------------------------------
        # GET PRICES
        # ------------------------------------------

        btc_price = float(
            get_btc_price()
        )

        eth_price = float(
            get_eth_price()
        )


        print(
            "BTC Price:",
            btc_price
        )

        print(
            "ETH Price:",
            eth_price
        )


        # ==========================================
        # BTC HIGH
        # ==========================================

        if (
            btc_price >= BTC_HIGH
            and not btc_high_sent
        ):

            send_message(

                f"🚨 BTC HIGH ALERT!\n\n"
                f"💰 BTC: ${btc_price:.2f}\n"
                f"🎯 Level: ${BTC_HIGH}\n"
                f"⏰ Status: Price crossed HIGH level"
            )

            btc_high_sent = True


        # ==========================================
        # BTC LOW
        # ==========================================

        if (
            btc_price <= BTC_LOW
            and not btc_low_sent
        ):

            send_message(

                f"🚨 BTC LOW ALERT!\n\n"
                f"💰 BTC: ${btc_price:.2f}\n"
                f"🎯 Level: ${BTC_LOW}\n"
                f"⏰ Status: Price crossed LOW level"
            )

            btc_low_sent = True


        # ==========================================
        # ETH HIGH
        # ==========================================

        if (
            eth_price >= ETH_HIGH
            and not eth_high_sent
        ):

            send_message(

                f"🚨 ETH HIGH ALERT!\n\n"
                f"💰 ETH: ${eth_price:.2f}\n"
                f"🎯 Level: ${ETH_HIGH}\n"
                f"⏰ Status: Price crossed HIGH level"
            )

            eth_high_sent = True


        # ==========================================
        # ETH LOW
        # ==========================================

        if (
            eth_price <= ETH_LOW
            and not eth_low_sent
        ):

            send_message(

                f"🚨 ETH LOW ALERT!\n\n"
                f"💰 ETH: ${eth_price:.2f}\n"
                f"🎯 Level: ${ETH_LOW}\n"
                f"⏰ Status: Price crossed LOW level"
            )

            eth_low_sent = True


        # ==========================================
        # RESET BTC LOW
        # ==========================================

        if btc_price > BTC_LOW:

            btc_low_sent = False


        # ==========================================
        # RESET BTC HIGH
        # ==========================================

        if btc_price < BTC_HIGH:

            btc_high_sent = False


        # ==========================================
        # RESET ETH HIGH
        # ==========================================

        if eth_price < ETH_HIGH:

            eth_high_sent = False


        # ==========================================
        # RESET ETH LOW
        # ==========================================

        if eth_price > ETH_LOW:

            eth_low_sent = False


        # ==========================================
        # WAIT 10 SECONDS
        # ==========================================

        time.sleep(10)


    except Exception as error:

        print(
            "🔴 Bot Error:",
            error
        )

        time.sleep(10)