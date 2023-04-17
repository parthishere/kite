function autocomplete(inp, arr) {
  /*the autocomplete function takes two arguments,
  the text field element and an array of possible autocompleted values:*/
  var currentFocus;
  /*execute a function when someone writes in the text field:*/
  inp.addEventListener("input", function (e) {
    var a, b, i, val = this.value;
    /*close any already open lists of autocompleted values*/
    closeAllLists();
    if (!val) { return false; }
    currentFocus = -1;
    /*create a DIV element that will contain the items (values):*/
    a = document.createElement("DIV");
    a.setAttribute("id", this.id + "autocomplete-list");
    a.setAttribute("class", "autocomplete-items");
    /*append the DIV element as a child of the autocomplete container:*/
    this.parentNode.appendChild(a);
    /*for each item in the array...*/
    for (i = 0; i < arr.length; i++) {
      /*check if the item starts with the same letters as the text field value:*/
      if (arr[i].substr(0, val.length).toUpperCase() == val.toUpperCase()) {
        /*create a DIV element for each matching element:*/
        b = document.createElement("DIV");
        /*make the matching letters bold:*/
        b.innerHTML = "<strong>" + arr[i].substr(0, val.length) + "</strong>";
        b.innerHTML += arr[i].substr(val.length);
        /*insert a input field that will hold the current array item's value:*/
        b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";
        /*execute a function when someone clicks on the item value (DIV element):*/
        b.addEventListener("click", function (e) {
          let searchElement = document.getElementById('myInput');
          let watchFlag = searchElement.className;
          /*insert the value for the autocomplete text field:*/
          inp.value = this.getElementsByTagName("input")[0].value;
          if (watchFlag == "AlgoWatch") {
            $.ajax({
              type: "POST",
              url: 'addInstrument',
              data: { csrfmiddlewaretoken: '{{ csrf_token }}', script: inp.value, flag: watchFlag },
              success: function (response) {
                console.log((response.instrument)[0], "____________________hello world");
                let instrument = (response.instrument)[0];
                //                                 socket.send(JSON.stringify({
                //                                   'msg':instrument.instruments,
                // //                                  'instrument_token': instrument.instrumentsToken
                //                                 }));
                let row = ``;
                if (instrument.startAlgo != false) {
                  row = `<tr id="${instrument.instruments}_main">
                            <td id="${instrument.instruments}time">${instrument.algoStartTime ? instrument.algoStartTime : '-'}</td>
                            <td>${instrument.instruments}</td>
                            <td id='${instrument.instruments}op'>0</td>
                            <td >${instrument.entryprice}</td>
                            <td id='${instrument.instruments}ltp'>2</td>
                            <td id='${instrument.instruments}slhit'>${instrument.slHitCount}</td>
                            <td><input type="number" onchange="onQtyChange(this, '${instrument.instruments}')" oninput="this.value=(parseInt(this.value)||1)" pattern="[0-9]" name='qty[]' id="${instrument.instruments}"  placeholder='Enter Qty' class="form-control" value = "${instrument.qty}"/></td>
                            <td><a href="#" class="btn btn-info"  title="Click to scale up qty" onclick="ScaleUpQty('${instrument.instruments}')"><span> Scale Up</span></a></td>
                            <td><a href="#" class="btn btn-warning" title="Click to scale down qty" onclick="ScaleDownQty('${instrument.instruments}')"><span> Scale Down</span></a></td>
                            <td style="color: green; font-weight:bold">Algo Started</td>
                            <td><a href="#" class="delete" onclick="deleteInstrument('${instrument.instruments}');"><i class="material-icons" data-toggle="tooltip" title="Delete">&#xe872;</i></a></td>
                        </tr>`
                } else {
                  row = `<tr id="${instrument.instruments}_main">
                            <td id="${instrument.instruments}time">${instrument.algoStartTime ? instrument.algoStartTime : '-'}</td>
                            <td>${instrument.instruments}</td>
                            <td id='${instrument.instruments}op'>0</td>
                            <td >${instrument.entryprice}</td>
                            <td id='${instrument.instruments}ltp'>2</td>
                            <td id='${instrument.instruments}slhit'>${instrument.slHitCount}</td>
                            <td><input type="number" onchange="onQtyChange(this, '${instrument.instruments}')" oninput="this.value=(parseInt(this.value)||1)" pattern="[0-9]" name='qty[]' id="${instrument.instruments}"  placeholder='Enter Qty' class="form-control" value = "${instrument.qty}"/></td>
                            <td style="text-align: center;"><a href="#" class="btn btn-info"  title="Click to scale up qty" onclick="ScaleUpQty('${instrument.instruments}')"><span> Scale Up</span></a></td>
                            <td style="text-align: center;"><a href="#" class="btn btn-warning" title="Click to scale down qty" onclick="ScaleDownQty('${instrument.instruments}')"><span> Scale Down</span></a></td>
                            <td style="color: green; font-weight:bold;text-align: center;" id="startalgobtn-${instrument.instruments}"><a href="#" class="btn btn-success" onclick="startAlgo('${instrument.instruments}')"><span> Start Algo</span></a></td>
                            <td><a href="#" class="delete" onclick="deleteInstrument('${instrument.instruments}');"><i class="material-icons" data-toggle="tooltip" title="Delete">&#xe872;</i></a></td>
                        </tr>`
                }

                let instrumentDivData = document.getElementById('instrumentDiv').innerHTML + row;
                document.getElementById('instrumentDiv').innerHTML = instrumentDivData
                //instrumentDiv.innerHtml += 

              }
            });
          }
          else if (watchFlag == "ManualWatch") {
           
            $.ajax({
              type: "POST",
              url: 'addInstrument',
              data: { csrfmiddlewaretoken: '{{ csrf_token }}', script: inp.value, flag: watchFlag },
              success: function (response) {
                console.log((response.instrument)[0], "__________________+++++++---------------=++++++++");
                let instrument = (response.instrument)[0];
                let row = ``;
                if (instrument.openPostion != false) {
                  if (instrument.positionType == "BUY") {
                    row = `<tr id="${instrument.instruments}_main">
                              <td id="${instrument.instruments}time">${instrument.algoStartTime ? instrument.algoStartTime : '-'}</td>
                              <td>${instrument.instruments}</td>
                              <td id='${instrument.instruments}op'>0</td>
                              <td id='${instrument.instruments}ltp'>2</td>
                              <td id='${instrument.instruments}slhit'>${instrument.slHitCount}</td>
                              <td><input type="number" onchange="onQtyChange(this, '${instrument.instruments}')" oninput="this.value=(parseInt(this.value)||1)" pattern="[0-9]" name='qty[]' id="${instrument.instruments}"  placeholder='Enter Qty' class="form-control" value = "${instrument.qty}"/></td>
                              <td><a href="#" class="btn btn-info"  title="Click to scale up qty" onclick="ScaleUpQty('${instrument.instruments}')"><span> Scale Up</span></a></td>
                              <td><a href="#" class="btn btn-warning" title="Click to scale down qty" onclick="ScaleDownQty('${instrument.instruments}')"><span> Scale Down</span></a></td>
                              <td style="color: green; font-weight:bold">Open Position</td>
                              <td style="color: green; font-weight:bold">-</td>
                              <td><a href="#" class="btn btn-danger" title="Click to Sell" onclick="SellOrder('${instrument.instruments}')"><span> Sell</span></a></td>
                              <td><a href="#" class="delete" onclick="deleteInstrument('${instrument.instruments}');"><i class="material-icons" data-toggle="tooltip" title="Delete">&#xe872;</i></a></td>
                            </tr>`
                  } else if (instrument.positionType == "SELL") {
                    row = `<tr id="${instrument.instruments}_main">
                              <td id="${instrument.instruments}time">${instrument.algoStartTime ? instrument.algoStartTime : '-'}</td>
                              <td>${instrument.instruments}</td>
                              <td id='${instrument.instruments}op'>0</td>
                              <td id='${instrument.instruments}ltp'>2</td>
                              <td id='${instrument.instruments}slhit'>${instrument.slHitCount}</td>
                              <td><input type="number" onchange="onQtyChange(this, '${instrument.instruments}')" oninput="this.value=(parseInt(this.value)||1)" pattern="[0-9]" name='qty[]' id="${instrument.instruments}"  placeholder='Enter Qty' class="form-control" value = "${instrument.qty}"/></td>
                              <td><a href="#" class="btn btn-info"  title="Click to scale up qty" onclick="ScaleUpQty('${instrument.instruments}')"><span> Scale Up</span></a></td>
                              <td><a href="#" class="btn btn-warning" title="Click to scale down qty" onclick="ScaleDownQty('${instrument.instruments}')"><span> Scale Down</span></a></td>
                              <td style="color: green; font-weight:bold">-</td>
                              <td style="color: green; font-weight:bold">Open Position</td>
                              <td><a href="#" class="btn btn-danger" title="Click to Sell" onclick="SellOrder('${instrument.instruments}')"><span> Sell</span></a></td>
                              <td><a href="#" class="delete" onclick="deleteInstrument('${instrument.instruments}');"><i class="material-icons" data-toggle="tooltip" title="Delete">&#xe872;</i></a></td>
                          </tr>`
                  }
                  else {
                    row = `<tr id="${instrument.instruments}_main">
                              <td id="${instrument.instruments}time">${instrument.algoStartTime ? instrument.algoStartTime : '-'}</td>
                              <td>${instrument.instruments}</td>
                              <td id='${instrument.instruments}op'>0</td>
                              <td id='${instrument.instruments}ltp'>2</td>
                              <td id='${instrument.instruments}slhit'>${instrument.slHitCount}</td>
                              <td><input type="number" onchange="onQtyChange(this, '${instrument.instruments}')" oninput="this.value=(parseInt(this.value)||1)" pattern="[0-9]" name='qty[]' id="${instrument.instruments}"  placeholder='Enter Qty' class="form-control" value = "${instrument.qty}"/></td>
                              <td><a href="#" class="btn btn-info"  title="Click to scale up qty" onclick="ScaleUpQty('${instrument.instruments}')"><span> Scale Up</span></a></td>
                              <td><a href="#" class="btn btn-warning" title="Click to scale down qty" onclick="ScaleDownQty('${instrument.instruments}')"><span> Scale Down</span></a></td>
                              <td style="color: green; font-weight:bold">-</td>
                              <td style="color: green; font-weight:bold">-</td>
                              <td><a href="#" class="btn btn-danger" title="Click to Sell" onclick="SellOrder('${instrument.instruments}')"><span> Sell</span></a></td>
                              <td><a href="#" class="delete" onclick="deleteInstrument('${instrument.instruments}');"><i class="material-icons" data-toggle="tooltip" title="Delete">&#xe872;</i></a></td>
                          </tr>`
                  }
                } else {
                  row = `<tr id="${instrument.instruments}_main">
                            <td id="${instrument.instruments}time">${instrument.algoStartTime ? instrument.algoStartTime : '-'}</td>
                            <td>${instrument.instruments}</td>
                            <td id='${instrument.instruments}op'>0</td>
                            <td id='${instrument.instruments}ltp'>2</td>
                            <td id='${instrument.instruments}slhit'>${instrument.slHitCount}</td>
                            <td><input type="number" onchange="onQtyChange(this, '${instrument.instruments}')" oninput="this.value=(parseInt(this.value)||1)" pattern="[0-9]" name='qty[]' id="${instrument.instruments}"  placeholder='Enter Qty' class="form-control" value = "${instrument.qty}"/></td>
                            <td><a href="#" class="btn btn-info"  title="Click to scale up qty" onclick="ScaleUpQty('${instrument.instruments}')"><span> Scale Up</span></a></td>
                            <td><a href="#" class="btn btn-warning" title="Click to scale down qty" onclick="ScaleDownQty('${instrument.instruments}')"><span> Scale Down</span></a></td>
                            <td><a href="#" class="btn btn-success" title="Click to buy" onclick="BuyOrder('${instrument.instruments}')"><span> Buy</span></a></td>
                            <td><a href="#" class="btn btn-danger" title="Click to Sell" onclick="SellOrder('${instrument.instruments}')"><span> Sell</span></a></td>
                            <td><a href="#" class="delete" onclick="deleteInstrument('${instrument.instruments}');""><i class="material-icons" data-toggle="tooltip" title="Delete">&#xe872;</i></a></td>
                        </tr>`
                }

                let instrumentDivData = document.getElementById('instrumentDiv').innerHTML + row;
                document.getElementById('instrumentDiv').innerHTML = instrumentDivData
                //instrumentDiv.innerHtml += 
              }
            });
          }

          /*close the list of autocompleted values,
          (or any other open lists of autocompleted values:*/
          closeAllLists();
        });
        a.appendChild(b);
      }
    }
  });
  /*execute a function presses a key on the keyboard:*/
  inp.addEventListener("keydown", function (e) {
    var x = document.getElementById(this.id + "autocomplete-list");
    if (x) x = x.getElementsByTagName("div");
    if (e.keyCode == 40) {
      /*If the arrow DOWN key is pressed,
      increase the currentFocus variable:*/
      currentFocus++;
      /*and and make the current item more visible:*/
      addActive(x);
    } else if (e.keyCode == 38) { //up
      /*If the arrow UP key is pressed,
      decrease the currentFocus variable:*/
      currentFocus--;
      /*and and make the current item more visible:*/
      addActive(x);
    } else if (e.keyCode == 13) {
      /*If the ENTER key is pressed, prevent the form from being submitted,*/
      e.preventDefault();
      if (currentFocus > -1) {
        /*and simulate a click on the "active" item:*/
        if (x) x[currentFocus].click();
      }
    }
  });
  function addActive(x) {
    /*a function to classify an item as "active":*/
    if (!x) return false;
    /*start by removing the "active" class on all items:*/
    removeActive(x);
    if (currentFocus >= x.length) currentFocus = 0;
    if (currentFocus < 0) currentFocus = (x.length - 1);
    /*add class "autocomplete-active":*/
    x[currentFocus].classList.add("autocomplete-active");
  }
  function removeActive(x) {
    /*a function to remove the "active" class from all autocomplete items:*/
    for (var i = 0; i < x.length; i++) {
      x[i].classList.remove("autocomplete-active");
    }
  }
  function closeAllLists(elmnt) {
    /*close all autocomplete lists in the document,
    except the one passed as an argument:*/
    var x = document.getElementsByClassName("autocomplete-items");
    for (var i = 0; i < x.length; i++) {
      if (elmnt != x[i] && elmnt != inp) {
        x[i].parentNode.removeChild(x[i]);
      }
    }
  }
  /*execute a function when someone clicks in the document:*/
  document.addEventListener("click", function (e) {

    closeAllLists(e.target);
  });
}
const instruments = JSON.parse(document.getElementById('allInstrumentsList').textContent);
/*An array containing all the country names in the world:*/
/*initiate the autocomplete function on the "myInput" element, and pass along the countries array as possible autocomplete values:*/
autocomplete(document.getElementById("myInput"), instruments);


function deleteInstrument(script) {
  let searchElement = document.getElementById('myInput');
  let watchFlag = searchElement.className;
  $.ajax({
    type: "POST",
    url: 'deleteInstrument',
    data: { csrfmiddlewaretoken: '{{ csrf_token }}', script, flag: watchFlag },
    success: function (response) {
      if (response === "success") {
        document.getElementById(script + '_main').innerHTML = "";
      }
    }
  });
}


var baseQty = {};

function getBaseQty(instrument) {
  if (baseQty[instrument]) {
    return baseQty[instrument];
  }
  let qty = parseInt(document.getElementById(instrument).value);
  baseQty[instrument] = qty;
  return qty;
}

function updateQty(script, qty) {
  let searchElement = document.getElementById('myInput');
  let isFromAlgoTest = searchElement.className === 'AlgoWatch' ? "True" : "False";
  $.ajax({
    type: "POST",
    url: 'scaleUpQty',
    data: { csrfmiddlewaretoken: getCSRFToken(), script: script, scriptQty: qty, isFromAlgoTest },
    success: function callback(response) {
      console.log(response);
    }
  });
}

function onQtyChange(element, instrument) {
  baseQty[instrument] = parseInt(element.value);
  updateQty(instrument, baseQty[instrument]);
}

function ScaleUpQty(clicked) {
  var qty = parseInt(document.getElementById(clicked).value);
  var multipleQty = qty + getBaseQty(clicked);
  document.getElementById(clicked).value = multipleQty;
  updateQty(clicked, multipleQty);
}

function ScaleDownQty(clicked) {
  let qty = parseInt(document.getElementById(clicked).value);
  if (qty > 1) {
    var multipleQty = parseInt(qty - getBaseQty(clicked));
    document.getElementById(clicked).value = multipleQty;
  } else {
    return;
  }
  updateQty(clicked, multipleQty);
}