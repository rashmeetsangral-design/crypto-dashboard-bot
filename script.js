const btcPrice = document.getElementById("btc-price");
const ethPrice = document.getElementById("eth-price");
const paxgPrice = document.getElementById("paxg-price");
const solPrice = document.getElementById("sol-price");
const volumeInfo = document.getElementById("volume-info");
const volumeAlert = document.getElementById("volume-alert");


// ==================================================
// LIVE DELTA EXCHANGE PRICES
// ==================================================

async function updatePrices() {
    try {
        const symbols = [
            "BTCUSD",
            "ETHUSD",
            "PAXGUSD",
            "SOLUSD"
        ];

        const results = await Promise.all(
            symbols.map(symbol =>
                fetch(
                    `https://api.india.delta.exchange/v2/tickers/${symbol}`
                ).then(response => response.json())
            )
        );

        const prices = {};

        results.forEach((data, index) => {
            const symbol = symbols[index];

            if (data.success && data.result) {
                prices[symbol] = Number(
                    data.result.close ||
                    data.result.mark_price ||
                    data.result.last_price
                );
            }
        });

        if (prices.BTCUSD) {
            btcPrice.textContent =
                "$" +
                prices.BTCUSD.toLocaleString("en-US", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
        }

        if (prices.ETHUSD) {
            ethPrice.textContent =
                "$" +
                prices.ETHUSD.toLocaleString("en-US", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
        }

        if (prices.PAXGUSD) {
            paxgPrice.textContent =
                "$" +
                prices.PAXGUSD.toLocaleString("en-US", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
        }

        if (prices.SOLUSD) {
            solPrice.textContent =
                "$" +
                prices.SOLUSD.toLocaleString("en-US", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
        }

    } catch (error) {
        console.error("🔴 Delta price error:", error);
    }
}

updatePrices();
setInterval(updatePrices, 3000);


// ==================================================
// CHART
// ==================================================

const chartContainer =
    document.getElementById("chart-container");

const chart =
    LightweightCharts.createChart(
        chartContainer,
        {
            width: chartContainer.clientWidth,
            height: 500,

            layout: {
                background: {
                    type: "solid",
                    color: "#111827"
                },
                textColor: "#d1d5db"
            },

            grid: {
                vertLines: {
                    color: "#1f2937"
                },
                horzLines: {
                    color: "#1f2937"
                }
            },

            rightPriceScale: {
                visible: true,
                autoScale: true
            },

            timeScale: {
                timeVisible: true,
                secondsVisible: false
            }
        }
    );


// ==================================================
// CURRENT SYMBOL + TIMEFRAME
// ==================================================

let currentSymbol = "BTCUSD";
let currentInterval = "1h";

let liveVolumeHistory = [];
let lastVolumeCandleTime = null;


// ==================================================
// CANDLE SERIES
// ==================================================

const candleSeries =
    chart.addSeries(
        LightweightCharts.CandlestickSeries,
        {
            priceScaleId: "right"
        }
    );

candleSeries.priceScale().applyOptions({
    autoScale: true,

    scaleMargins: {
        top: 0.05,
        bottom: 0.30
    }
});


// ==================================================
// VOLUME SERIES
// ==================================================

const volumeSeries =
    chart.addSeries(
        LightweightCharts.HistogramSeries,
        {
            priceFormat: {
                type: "volume"
            },

            priceScaleId: ""
        }
    );

volumeSeries.priceScale().applyOptions({
    scaleMargins: {
        top: 0.75,
        bottom: 0
    }
});


// ==================================================
// LIVE DELTA WEBSOCKET
// ==================================================

let deltaSocket = null;


function startLiveDeltaChart(
    symbol,
    interval = "1h"
) {

    currentSymbol = symbol;
    currentInterval = interval;

    if (deltaSocket) {
        deltaSocket.close();
        deltaSocket = null;
    }

    deltaSocket =
        new WebSocket(
            "wss://public-socket.india.delta.exchange"
        );


    deltaSocket.onopen = () => {

        console.log(
            "🟢 Delta WebSocket connected"
        );

        deltaSocket.send(
            JSON.stringify({
                type: "subscribe",

                payload: {
                    channels: [
                        {
                            name: "ticker",
                            symbols: [symbol]
                        },

                        {
                            name:
                                "candlestick_" +
                                interval,

                            symbols: [symbol]
                        }
                    ]
                }
            })
        );

        console.log(
            "📡 Live:",
            symbol,
            interval
        );
    };


    deltaSocket.onmessage =
        (event) => {

            const message =
                JSON.parse(event.data);


            // ----------------------------------
            // TICKER
            // ----------------------------------

            if (message.type === "ticker") {
                console.log(
                    "📊 TICKER DATA:",
                    message.d[0]
                );
            }


            // ----------------------------------
            // LIVE CANDLE
            // ----------------------------------

            if (
                message.type ===
                    "candlestick_" + interval ||

                message.type ===
                    "candlestick"
            ) {

                const candle = message;


                const liveCandle = {

                    time:
                        Math.floor(
                            Number(candle.cst) /
                            1000000
                        ),

                    open:
                        Number(candle.o),

                    high:
                        Number(candle.h),

                    low:
                        Number(
                            candle.l ||
                            candle.L
                        ),

                    close:
                        Number(candle.c)
                };


                if (
                    liveCandle.open &&
                    liveCandle.high &&
                    liveCandle.low &&
                    liveCandle.close
                ) {

                    const liveVolume = {

                        time:
                            liveCandle.time,

                        value:
                            Number(candle.v),

                        color:
                            liveCandle.close >=
                            liveCandle.open
                                ? "#22c55e"
                                : "#ef4444"
                    };


                    // ----------------------------------
                    // VOLUME SPIKE DETECTION
                    // ----------------------------------

                    const currentVolume =
                        Number(candle.v);


                    if (
                        liveCandle.time !==
                        lastVolumeCandleTime
                    ) {

                        liveVolumeHistory.push(
                            currentVolume
                        );

                        lastVolumeCandleTime =
                            liveCandle.time;


                        if (
                            liveVolumeHistory.length >
                            20
                        ) {

                            liveVolumeHistory.shift();

                        }
                    }


                    if (
                        liveVolumeHistory.length > 0
                    ) {

                        const averageVolume =
                            liveVolumeHistory.reduce(
                                (sum, volume) =>
                                    sum + volume,
                                0
                            ) /
                            liveVolumeHistory.length;


                        const volumeRatio =
                            currentVolume /
                            averageVolume;


                        console.log(
                            "📈 Volume Ratio:",
                            volumeRatio.toFixed(2) + "x"
                        );


                        console.log(
                            "📊 Average Volume:",
                            averageVolume
                        );


                        // ----------------------------------
                        // DASHBOARD VOLUME STATUS
                        // ----------------------------------

                        if (
                            volumeAlert
                        ) {

                            if (
                                volumeRatio >= 2.0
                            ) {

                                volumeAlert.textContent =
                                    "🚨 VOLUME SPIKE! " +
                                    volumeRatio.toFixed(2) +
                                    "x";

                                volumeAlert.style.color =
                                    "#ef4444";

                            } else {

                                volumeAlert.textContent =
                                    "🟢 Volume Normal " +
                                    volumeRatio.toFixed(2) +
                                    "x";

                                volumeAlert.style.color =
                                    "#22c55e";
                            }
                        }


                        // ----------------------------------
                        // CONSOLE SPIKE ALERT
                        // ----------------------------------

                        if (
                            volumeRatio >= 2.0
                        ) {

                            console.log(
                                "🚨 VOLUME SPIKE!",
                                "Current:",
                                currentVolume,

                                "Average:",
                                averageVolume,

                                "Ratio:",
                                volumeRatio.toFixed(2) +
                                "x"
                            );
                        }
                    }


                    // ----------------------------------
                    // UPDATE CHART
                    // ----------------------------------

                    volumeSeries.update(
                        liveVolume
                    );

                    candleSeries.update(
                        liveCandle
                    );


                    console.log(
                        "🕯️ LIVE:",
                        symbol,
                        interval,
                        liveCandle
                    );
                }
            }
        };


    deltaSocket.onerror =
        (error) => {

            console.error(
                "🔴 Delta WebSocket error:",
                error
            );
        };


    deltaSocket.onclose =
        () => {

            console.log(
                "🟡 Delta WebSocket closed"
            );
        };
}


// ==================================================
// LOAD HISTORICAL DELTA CHART
// ==================================================

async function loadCryptoChart(
    symbol,
    interval = "1h"
) {

    currentSymbol = symbol;
    currentInterval = interval;

    liveVolumeHistory = [];
    lastVolumeCandleTime = null;


    try {

        const end =
            Math.floor(
                Date.now() / 1000
            );


        const resolutionSeconds = {

            "1m": 60,
            "5m": 300,
            "15m": 900,
            "1h": 3600,
            "4h": 14400

        };


        const seconds =
            resolutionSeconds[interval] ||
            3600;


        const start =
            end -
            (200 * seconds);


        const response =
            await fetch(
                `https://api.india.delta.exchange/v2/history/candles?symbol=${symbol}&resolution=${interval}&start=${start}&end=${end}`
            );


        const data =
            await response.json();


        if (
            !data.success ||
            !data.result
        ) {

            console.error(
                "🔴 Delta candle data error:",
                data
            );

            return;
        }


        const sortedData =
            data.result.sort(
                (a, b) =>
                    Number(a.time) -
                    Number(b.time)
            );


        // ----------------------------------
        // CANDLES
        // ----------------------------------

        const candles =
            sortedData.map(
                item => ({

                    time:
                        Number(item.time),

                    open:
                        Number(item.open),

                    high:
                        Number(item.high),

                    low:
                        Number(item.low),

                    close:
                        Number(item.close)

                })
            );


        // ----------------------------------
        // VOLUMES
        // ----------------------------------

        const volumes =
            sortedData.map(
                item => ({

                    time:
                        Number(item.time),

                    value:
                        Number(
                            item.volume || 0
                        ),

                    color:
                        Number(item.close) >=
                        Number(item.open)
                            ? "#22c55e"
                            : "#ef4444"

                })
            );


        // ----------------------------------
        // PUT DATA ON CHART
        // ----------------------------------

        candleSeries.setData(
            candles
        );

        volumeSeries.setData(
            volumes
        );


        // ----------------------------------
        // LOAD LAST 20 VOLUMES
        // ----------------------------------

        liveVolumeHistory =
            volumes
                .slice(-20)
                .map(
                    item =>
                        Number(item.value)
                );


        console.log(
            "📚 Volume history loaded:",
            liveVolumeHistory
        );


        // ----------------------------------
        // LATEST VOLUME
        // ----------------------------------

        const latestVolume =
            volumes[
                volumes.length - 1
            ];


        if (latestVolume) {

            volumeInfo.textContent =
                symbol.replace(
                    "USD",
                    ""
                ) +
                " Volume: " +
                latestVolume.value.toLocaleString();

        }


        // ----------------------------------
        // CHART SCALE
        // ----------------------------------

        chart
            .priceScale("right")
            .setAutoScale(true);


        candleSeries
            .priceScale()
            .setAutoScale(true);


        chart
            .timeScale()
            .fitContent();


        console.log(
            "🟢 Delta chart loaded:",
            symbol,
            interval
        );

    } catch (error) {

        console.error(
            "🔴 Delta chart error:",
            error
        );
    }
}


// ==================================================
// TIMEFRAME BUTTONS
// ==================================================

const timeframeMap = {

    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1H": "1h",
    "4H": "4h"

};


const timeframeButtons =
    document.querySelectorAll(
        ".timeframes button"
    );


timeframeButtons.forEach(
    button => {

        button.addEventListener(
            "click",
            () => {

                const selected =
                    timeframeMap[
                        button.textContent.trim()
                    ];


                if (!selected) {
                    return;
                }


                currentInterval =
                    selected;


                loadCryptoChart(
                    currentSymbol,
                    selected
                );


                startLiveDeltaChart(
                    currentSymbol,
                    selected
                );


                timeframeButtons.forEach(
                    btn => {

                        btn.classList.remove(
                            "active"
                        );

                    }
                );


                button.classList.add(
                    "active"
                );


                console.log(
                    "⏱️ Timeframe changed:",
                    currentSymbol,
                    selected
                );

            }
        );

    }
);


// ==================================================
// BTC / ETH BUTTONS
// ==================================================

const btcChartBtn =
    document.getElementById(
        "btc-chart-btn"
    );


const ethChartBtn =
    document.getElementById(
        "eth-chart-btn"
    );


if (
    btcChartBtn &&
    ethChartBtn
) {

    btcChartBtn.addEventListener(
        "click",
        () => {

            btcChartBtn.classList.add(
                "active"
            );

            ethChartBtn.classList.remove(
                "active"
            );


            loadCryptoChart(
                "BTCUSD",
                currentInterval
            );


            startLiveDeltaChart(
                "BTCUSD",
                currentInterval
            );


            console.log(
                "₿ BTC selected:",
                currentInterval
            );

        }
    );


    ethChartBtn.addEventListener(
        "click",
        () => {

            ethChartBtn.classList.add(
                "active"
            );

            btcChartBtn.classList.remove(
                "active"
            );


            loadCryptoChart(
                "ETHUSD",
                currentInterval
            );


            startLiveDeltaChart(
                "ETHUSD",
                currentInterval
            );


            console.log(
                "Ξ ETH selected:",
                currentInterval
            );

        }
    );

}


// ==================================================
// START CHART
// ==================================================

loadCryptoChart(
    "BTCUSD",
    "1h"
);


startLiveDeltaChart(
    "BTCUSD",
    "1h"
);


// ==================