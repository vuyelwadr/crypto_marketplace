// BTC pages
var useramount_crypto = document.getElementById('usdamount_crypto');
if (useramount_crypto != null)
    useramount_crypto.addEventListener('change', btc_calculator);

function btc_calculator() {
    var amount = 0;
    amount = useramount_crypto.value;
    if (amount <= 0){
        document.getElementById("btc-buy").innerHTML = "Enter a valid Amount";
        document.getElementById("btc-sell").innerHTML = "Enter a valid Amount";
    }
    else{
        btcamount = amount / btcprice;
        var show = btcamount.toFixed(8) + "BTC"; 
        document.getElementById("btc-buy").innerHTML = "Buying: " + show;
        document.getElementById("btc-sell").innerHTML = "Selling: " + show;
        document.getElementById("btc-withdraw").innerHTML = "Withdraw: " + show;
    }
    
}

//USD pages
var useramount_fiat = document.getElementById('usdamount_fiat');
if (useramount_fiat != null)
    useramount_fiat.addEventListener('change', usd_calculator);

function usd_calculator(){
    var amount = 0;
    amount = useramount_fiat.value
    if (amount <= 0){
        document.getElementById("usd-deposit").innerHTML = "Enter a valid Amount";
        document.getElementById("usd-withdraw").innerHTML = "Enter a valid Amount";
    }
    else{
        document.getElementById("usd-deposit").innerHTML = "Ballance will be: $" + (parseInt(usdbalance) + parseInt(amount));
        document.getElementById("usd-withdraw").innerHTML = "Ballance will be: $" + (parseInt(usdbalance) - parseInt(amount));
    }
}

//help section
// var help = document.getElementById('gethelp').addEventListener("click", showhelp);
// function showhelp(){
//     document.getElementById('help').style.display="contents"
// }


function openPersonalDetails() {
    document.getElementById("personal_details").style.display = "block";
}
  
function closePersonalDetails() {
    document.getElementById("personal_details").style.display = "none";
} 

function openFinancialDetails() {
    document.getElementById("financial_details").style.display = "block";
}
  
function closeFinancialDetails() {
    document.getElementById("financial_details").style.display = "none";
} 

function openPasswordReset() {
    document.getElementById("password_reset").style.display = "block";
}
  
function closePasswordReset() {
    document.getElementById("password_reset").style.display = "none";
} 