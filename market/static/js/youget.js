var useramount = document.getElementById('usdamount');
useramount.addEventListener('change', btcamount);

function btcamount() {
    var amount = 0;
    amount = document.getElementById('usdamount').value;
    btcamount = amount / btcprice;
    var show = btcamount + "BTC"; 
    document.getElementById("btc-buy").innerHTML = "Buying: " + show;
    document.getElementById("btc-sell").innerHTML = "Selling: " + show;
}