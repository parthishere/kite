// const tokenValue = JSON.parse(document.getElementById('fetchToken').textContent);
// console.log(tokenValue,"+++++++++++++++++++++++")
        
// Websocket starts Here
// var socket = new WebSocket('ws://'+ window.location.host +'/ws/stock/'+tokenValue)
var socket = new WebSocket('ws://'+ window.location.host +'/ws/stock/')
socket.addEventListener('open',()=>{
    console.log("Websocket Connection Open............");
    /*let message = tokenValue;
    socket.send(JSON.stringify({
    'msg': message
    }))*/
})

socket.addEventListener('message',(event)=>{
    //console.log(event.data)
    let stockPrices = (JSON.parse(event.data)).liveData
    for (stock in stockPrices){
        //let stock_ltp = document.getElementById(stock+"ltp");
        let stock_ltp = document.querySelectorAll(`[id=${stock+"ltp"}]`);
        // console.log(stock_ltp,")___________________+++++++++++++++")
        
        if (stock_ltp.length == 0){
            continue
        }  
        for(let i = 0; i < stock_ltp.length; i++){
            let stock_ltp_price = stockPrices[stock]['LTP'];
            stock_ltp[i].innerText = stock_ltp_price;
        }
    }
    
    let allPosition = (JSON.parse(event.data)).position.net
    for (position in allPosition){
        let stock_qty = document.getElementById(allPosition[position]['tradingsymbol']+"qty");
    
        if (stock_qty == null){
            continue
        } 
        let stock_main_qty = allPosition[position]['quantity'];
        stock_qty.innerText = stock_main_qty;

        // =========================================
        let stock_avgTrde = document.getElementById(allPosition[position]['tradingsymbol']+"avgTrde");
    
        if (stock_avgTrde == null){
            continue
        } 
        let stock_main_avgTrde = allPosition[position]['average_price'];
        stock_avgTrde.innerText = stock_main_avgTrde;

        // =========================================
        let stock_pnl = document.getElementById(allPosition[position]['tradingsymbol']+"pnl");
    
        if (stock_pnl == null){
            continue
        } 
        let stock_main_pnl = allPosition[position]['pnl'];
        stock_pnl.innerText = stock_main_pnl;

    }
})

socket.addEventListener('close', (event)=>{
    console.log("Websocket Closed ...........", event);
})