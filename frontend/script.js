async function confirmDetails() {
    // Get form data
    const plate_license = document.getElementById('plate_license').value;
    const paymentMethod = document.querySelector('input[name="paymentMethod"]:checked')?.value;

    // Validate form data
    if (!plate_license || !paymentMethod) {
        alert("Please fill in all fields.");
        return;
    }
    // Prepare the request payload
    const payload = {
        plate_license: plate_license,
        payment_method: paymentMethod
    };

    const paymentAmount = document.getElementById('paymentAmount');
    const messageElement = document.getElementById('responseMessage');
    try {
        // Display "Processing Payment" message
        messageElement.style.color = 'blue';
        messageElement.textContent = 'Checking details...';

        // Send the data to the backend
        const response = await fetch('/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        // Handle the response
        const result = await response.json();
        if (response.ok) {
            if (result.chareged) {
                paymentAmount.textContent = result.amount;
                document.getElementById('paymentForm').style.display = 'none';
                const paymentDetails = document.getElementById('paymentDetails');
                paymentDetails.style.display = 'block';
                }
            else {
                messageElement.style.color = 'red';
                messageElement.textContent = result.message;
            }
        } else {
            messageElement.style.color = 'red';
            messageElement.textContent = `Error: ${result.message}`;
        }
    } catch (error) {
        console.error('Error processing payment:', error);
        alert('An error occurred while processing the payment.');
    }
    // Hide the current form and show the new interface

}

function goBack() {
    // Hide the paymentDetails and show the form again
    document.getElementById('paymentDetails').style.display = 'none';
    document.getElementById('paymentForm').style.display = 'block';
}        

async function processPayment() {
    const plate_license = document.getElementById('plate_license').value;
    // Prepare the request payload
    const payload = {
        plate_license: plate_license
    };

    const messageElement = document.getElementById('responseMessage');
    try {
        // Display "Processing Payment" message
        messageElement.style.color = 'blue';
        messageElement.textContent = 'Processing Payment...';

        // Send the data to the backend
        const response = await fetch('/process_payment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        // Handle the response
        const result = await response.json();
        messageElement.style.color = 'green';
        messageElement.textContent = result.message;
    } catch (error) {
        console.error('Error processing payment:', error);
        alert('An error occurred while processing the payment.');
    }
}