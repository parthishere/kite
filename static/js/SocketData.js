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
    let stockPrices = JSON.parse(event.data)
    for (stock in stockPrices){
        let stock_ltp = document.getElementById(stock+"ltp");
        if (stock_ltp == null){
            continue
        }  
        let stock_ltp_price = stockPrices[stock]['LTP'];
        stock_ltp.innerText = stock_ltp_price;
    }
})

socket.addEventListener('close', (event)=>{
    console.log("Websocket Closed ...........", event);
})