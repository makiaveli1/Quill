document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM fully loaded and parsed");

  const stripePublicKeyElement = document.getElementById(
    "id_stripe_public_key"
  );
  if (!stripePublicKeyElement) {
    console.error("Stripe Public Key element not found.");
    return;
  }

  const stripePublicKey = stripePublicKeyElement.textContent.trim();
  console.log("Stripe Public Key:", stripePublicKey);

  if (!stripePublicKey) {
    console.error("Stripe Public Key is empty.");
    return;
  }

  const stripe = Stripe(stripePublicKey);
  const elements = stripe.elements();
  console.log("Stripe and elements initialized");

  const style = {
    base: {
      color: "#32325d",
      fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
      fontSmoothing: "antialiased",
      fontSize: "16px",
      "::placeholder": {
        color: "#aab7c4",
      },
    },
    invalid: {
      color: "#fa755a",
      iconColor: "#fa755a",
    },
  };

  const card = elements.create("card", { style: style });
  card.mount("#card-element");
  console.log("Card element mounted");

  card.on("change", function (event) {
    const displayError = document.getElementById("card-errors");
    if (event.error) {
      console.error("Card element error:", event.error.message);
      displayError.textContent = event.error.message;
    } else {
      displayError.textContent = "";
    }
  });

  const form = document.getElementById("checkout-form");
  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    document.getElementById("submit-button").disabled = true;
    const clientSecret = document.getElementById("id_client_secret").value;
    console.log("Client Secret on submit:", clientSecret);

    if (!clientSecret) {
      console.error("Client Secret is missing.");
      return;
    }

    const formData = new FormData(form);
    const url = "/checkout/cache_checkout_data/";

    console.log("Sending data to server...");
    fetch(url, {
      method: "POST",
      body: formData,
      credentials: "same-origin",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Network response was not ok: ${response.status}`);
        }
        return response.json();
      })
      .then((jsonResponse) => {
        console.log("Response from server:", jsonResponse);
        if (jsonResponse.error) {
          throw new Error(`Server-side error: ${jsonResponse.error}`);
        }
        return stripe.confirmCardPayment(clientSecret, {
          payment_method: {
            card: card,
            billing_details: {
              name: form.querySelector('input[name="full_name"]').value,
              email: form.querySelector('input[name="email"]').value,
            },
          },
        });
      })
      .then((result) => {
        console.log("PaymentIntent confirmation result:", result);
        if (result.error) {
          throw new Error(
            `Payment confirmation error: ${result.error.message}`
          );
        }
        if (
          result.paymentIntent &&
          result.paymentIntent.status === "succeeded"
        ) {
          console.log("Payment succeeded:", result.paymentIntent);
          form.submit();
        }
      })
      .catch((error) => {
        console.error("Error encountered:", error);
        document.getElementById("card-errors").textContent =
          error.message || "An error occurred";
        document.getElementById("submit-button").disabled = false;
      });
  });
});
