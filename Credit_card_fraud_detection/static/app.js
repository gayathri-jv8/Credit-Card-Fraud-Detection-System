// Run after page loads
document.addEventListener("DOMContentLoaded", function () {

    const form = document.querySelector("form");
    const amountInput = document.querySelector("input[name='amount']");

    if (form && amountInput) {
        form.addEventListener("submit", function (e) {

            const amount = parseFloat(amountInput.value);

            // Validate transaction amount
            if (isNaN(amount) || amount <= 0) {
                alert("Please enter a valid transaction amount");
                e.preventDefault();
                return;
            }

            // Show loading message
            let loadingMsg = document.createElement("p");
            loadingMsg.innerText = "🔍 Analyzing transaction...";
            loadingMsg.style.marginTop = "10px";
            loadingMsg.style.color = "#555";
            form.appendChild(loadingMsg);

        });
    }
});
