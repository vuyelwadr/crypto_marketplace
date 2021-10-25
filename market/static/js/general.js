// BTC pages
var useramount_crypto = document.getElementById('usdamount_crypto');
if (useramount_crypto != null)
    useramount_crypto.addEventListener('change', btc_calculator);

function btc_calculator() {
    var amount = 0;
    amount = useramount_crypto.value;
    btcamount = amount / btcprice;
    var show = btcamount.toFixed(8) + "BTC"; 
    document.getElementById("btc-buy").innerHTML = "Buying: " + show;
    document.getElementById("btc-sell").innerHTML = "Selling: " + show;
}

//USD pages
var useramount_fiat = document.getElementById('usdamount_fiat');
if (useramount_fiat != null)
    useramount_fiat.addEventListener('change', usd_calculator);

function usd_calculator(){
    var amount = 0;
    amount = useramount_fiat.value
    document.getElementById("usd-deposit").innerHTML = "Ballance will be: $" + (parseInt(usdbalance) + parseInt(amount));
    document.getElementById("usd-withdraw").innerHTML = "Ballance will be: $" + (parseInt(usdbalance) - parseInt(amount));
}

//help section
var help = document.getElementById('gethelp').addEventListener("click", showhelp);
function showhelp(){
    document.getElementById('help').style.display="contents"
}
