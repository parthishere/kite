console.log("hello home")

const spinnerBox1 = document.getElementById('spinner-box')
const databox = document.getElementById('data-box')

$.ajax({
    type: "GET",
    url: 'home',
    success: function(response){
        setTimeout(()=>{
            spinnerBox1.classList.add('not-visible')
            databox.innerHTML = "Downloading complete, please for to Algowatch"
        }, 5000)
    },
    error:  function(error){
        console.log(error)
    }

})