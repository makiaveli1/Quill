document.addEventListener("DOMContentLoaded", function () {
  if (!stripePublicKey || stripePublicKey === "") {
      console.error("Stripe Public Key is not found or is empty.");
      return;
  }
  console.log("Stripe Public Key:", stripePublicKey);

  if (!clientSecret || clientSecret === "") {
      console.error("Client Secret is not found or is empty.");
      return;
  }
  console.log("Client Secret:", clientSecret);

  // Initialize Stripe with the directly available public key
  const stripe = Stripe(stripePublicKey);
  const elements = stripe.elements();
 
  // Configuration for Stripe card element...
  const card = elements.create("card", { /* card style configuration */ });
  card.mount("#card-element");

  // Handling form submission...
  let form = document.getElementById("checkout-form");
  form.addEventListener("submit", function (event) {
      event.preventDefault();
      document.getElementById("submit-button").disabled = true;

      stripe.confirmCardPayment(clientSecret, {
          payment_method: {
              card: card,
              billing_details: {
                  name: form.querySelector('input[name="full_name"]').value,
                  email: form.querySelector('input[name="email"]').value,
              },
          },
      }).then(function (result) {
          if (result.error) {
              console.error(result.error.message);
              document.getElementById("card-errors").textContent = result.error.message;
              document.getElementById("submit-button").disabled = false;
          } else {
              if (result.paymentIntent.status === "succeeded") {
                  console.log("Payment succeeded:", result.paymentIntent);
                  form.submit(); // Or other action upon success
              }
          }
      });
  });
});
