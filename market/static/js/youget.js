var useramount = document.getElementById('usdamount');
useramount.addEventListener('change', btcamount);

    function btcamount() {
        var amount = 0;
        amount = document.getElementById('usdamount').value;
        btcamount = amount / btcprice;
        document.getElementById("btcamount").innerHTML = "You Get: " + btcamount + "BTC"; 
    }