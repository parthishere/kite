// const tokenValue = JSON.parse(document.getElementById('fetchToken').textContent);
// console.log(tokenValue,"+++++++++++++++++++++++")
// Websocket starts Here
// var socket = new WebSocket('ws://'+ window.location.host +'/ws/stock/'+tokenValue)
var socket = new WebSocket('ws://' + window.location.host + '/ws/stock')
// var socket = new WebSocket('wss://www.tradingwithalgo.in:8001/ws/stock')
socket.addEventListener('open', () => {
    console.log("Websocket Connection Open............");
    // let message = "2342424";
    // socket.send(JSON.stringify({
    // 'msg': message
    // }))
})

socket.addEventListener('message', (event) => {
    // console.log(event.data)
    let stockPrices = (JSON.parse(event.data)).liveData;
    let defaultStockPrices = stockPrices.default_instruments;

    if (defaultStockPrices) {
        for (let defaultStockSymbol in defaultStockPrices) {
            let stockData = defaultStockPrices[defaultStockSymbol];
            let ltp = document.getElementById(defaultStockSymbol + 'defaultltp');
            if (!ltp) {
                continue;
            }
            ltp.innerText = stockData.LTP;
        }
    }

    for (stock in stockPrices) {
        //let stock_ltp = document.getElementById(stock+"ltp");
        let stock_ltp = document.querySelectorAll(`[id="${stock + "ltp"}"]`);
        let stock_op = document.querySelectorAll(`[id="${stock + "op"}"]`);
        // console.log(stock_ltp,")___________________+++++++++++++++")

        if (stock_ltp.length == 0 || stock_op.length == 0) {
            continue
        }
        for (let i = 0; i < stock_ltp.length; i++) {
            let stock_ltp_price = stockPrices[stock]['LTP'];
            stock_ltp[i].innerText = stock_ltp_price;
        }

        for (let i = 0; i < stock_op.length; i++) {
            let stock_op_price = stockPrices[stock]['Open'];
            stock_op[i].innerText = stock_op_price;
        }
    }

    let allPosition = (JSON.parse(event.data)).position.net
    for (position in allPosition) {
        let tradingSymbol = allPosition[position]['tradingsymbol'];
        let stock_qty = document.getElementById(`${tradingSymbol}qty`);

        if (stock_qty == null) {
            continue
        }
        let stock_main_qty = allPosition[position]['quantity'];
        stock_qty.innerText = stock_main_qty;

        // =========================================
        let stock_avgTrde = document.getElementById(`${tradingSymbol}avgTrde`);

        if (stock_avgTrde == null) {
            continue
        }
        let stock_main_avgTrde = allPosition[position]['average_price'];
        stock_avgTrde.innerText = roundToTwo(stock_main_avgTrde);

        // =========================================
        let stock_pnl = document.getElementById(`${tradingSymbol}pnl`);

        if (stock_pnl == null) {
            continue
        }
        let stock_main_pnl = allPosition[position]['pnl'];
        stock_pnl.innerText = stock_main_pnl.toFixed(2);
    }

    let totalPNL = (JSON.parse(event.data)).totalpnl;
    let stockPNL = document.getElementById("totalpnl");
    if (stockPNL) {
        stockPNL.innerText = totalPNL.toFixed(2);
    }

    function roundToTwo(num) {
        return +(Math.round(num + "e+2") + "e-2");
    }

    let slHits = (JSON.parse(event.data)).slHits;
    let searchElement = document.getElementById('myInput');
    if (searchElement) {
        let watchFlag = searchElement.className;
        if (slHits[watchFlag]) {
            for (let instrumentSymbol in slHits[watchFlag]) {
                let sl_hit_counts = document.querySelectorAll(`[id="${instrumentSymbol + "slhit"}"]`);
                for (let sl_hit_count of sl_hit_counts) {
                    sl_hit_count.innerText = slHits[watchFlag][instrumentSymbol];
                }
            }
        }
    }

})

socket.addEventListener('close', (event) => {
    console.log("Websocket Closed ...........", event);
})