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
            let open = document.getElementById(defaultStockSymbol + 'defaultopen');
            if (!ltp) {
                continue;
            }
            ltp.innerText = stockData.LTP;
            open.innerText = stockData.Open;
            ltp.style.color = stockData.LTP > stockData.Open ? 'green': 'red';
        }
    }

    for (stock in stockPrices) {
        //let stock_ltp = document.getElementById(stock+"ltp");
        let stock_ltp = document.querySelectorAll(`[id="${stock + "ltp"}"]`);
        let stock_op = document.querySelectorAll(`[id="${stock + "op"}"]`);
        let stock_hi = document.querySelectorAll(`[id="${stock + "hi"}"]`);
        let stock_lo = document.querySelectorAll(`[id="${stock + "lo"}"]`);
        let stock_cl = document.querySelectorAll(`[id="${stock + "cl"}"]`);

        // console.log(stock_ltp,")___________________+++++++++++++++")

        if (stock_ltp.length == 0 || stock_op.length == 0 || stock_hi.length == 0 || stock_lo.length == 0 || stock_cl.length == 0 ) {
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

        for (let i = 0; i < stock_hi.length; i++) {
            let stock_hi_price = stockPrices[stock]['High'];
            stock_hi[i].innerText = stock_hi_price;
        }

        for (let i = 0; i < stock_lo.length; i++) {
            let stock_lo_price = stockPrices[stock]['Low'];
            stock_lo[i].innerText = stock_lo_price;
        }

        for (let i = 0; i < stock_cl.length; i++) {
            let stock_cl_price = stockPrices[stock]['Close'];
            stock_cl[i].innerText = stock_cl_price;
        }

    }

    let allPosition = (JSON.parse(event.data)).position.net
    for (position in allPosition) {
        let tradingSymbol = allPosition[position]['tradingsymbol'];
        let stock_qty = document.getElementById(`${tradingSymbol}qty`);
        let stock_type = document.getElementById(`${tradingSymbol}ordertype`);

        if (stock_qty == null || stock_type == null) {
            continue
        }
        let stock_main_qty = allPosition[position]['quantity'];
        stock_qty.innerText = stock_main_qty;

        if (stock_main_qty < 0) {
            stock_type.innerText = 'SELL';
        } else if (stock_main_qty > 0) {
            stock_type.innerText = 'BUY';
        }

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
        console.log(allPosition[position]['pnl']);
        stock_pnl.innerText = stock_main_pnl;
        stock_pnl.style.color = stock_main_pnl > 0 ? 'green' : 'red';

        // // =========================================

        let stock_pnlpr = document.getElementById(`${tradingSymbol}last_price`);   // document.querySelectorAll(`[id="${stock + "last_price"}"]`);
        if (stock_pnlpr == null) {
            continue
        }
        let stock_pnlpr_main =  ( allPosition[position]['last_price']) ;
        stock_pnlpr.innerText = roundToTwo( stock_pnlpr_main ) + " %";
        stock_pnlpr.style.color = stock_main_pnl > 0 ? 'green' : 'red';


        // if ( allPosition[position]['quantity'] != 0 ) {
        //     let stock_pnlpr_main =  ( allPosition[position]['last_price']) / allPosition[position]['quantity']*allPosition[position]['quantity'];
        //     stock_pnlpr.innerText = roundToTwo( stock_pnlpr_main ) + " %";
        //     stock_pnlpr.style.color = stock_main_pnl > 0 ? 'green' : 'red';
        // }
        // else {
        //     let stock_pnlpr_main =  allPosition[position]['qty'];
        //     stock_pnlpr.innerText = roundToTwo( stock_pnlpr_main ) ;
        //     stock_pnlpr.style.color = stock_main_pnl > 0 ? 'green' : 'red';
        // }
    }

    let totalPNL = (JSON.parse(event.data)).totalpnl;
    console.log(totalPNL)
    let stockPNL = document.getElementById("totalpnl");
    if (stockPNL) {
        stockPNL.innerText = totalPNL;
        stockPNL.style.color = totalPNL > 0 ? 'green' : 'red';
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