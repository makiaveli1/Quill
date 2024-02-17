// stripe_elements.js

document.addEventListener("DOMContentLoaded", function () {
  var stripePublicKeyElement = document.getElementById("id_stripe_public_key");

  if (!stripePublicKeyElement) {
    console.error("Stripe Public Key element not found!");
    return;
  }

  var stripePublicKey = stripePublicKeyElement.textContent.trim();

  if (!stripePublicKey) {
    console.error("Stripe Public Key is empty!");
    return;
  }

  var stripe = Stripe(stripePublicKey);
  var elements = stripe.elements();

  // Custom styling for Stripe elements
  var style = {
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

  // Create an instance of the card element
  var card = elements.create("card", { style: style });

  // Add an instance of the card element into the `card-element` div
  card.mount("#card-element");

  // Handle real-time validation errors from the card element
  card.on("change", function (event) {
    var displayError = document.getElementById("card-errors");
    if (event.error) {
      displayError.textContent = event.error.message;
    } else {
      displayError.textContent = "";
    }
  });

  // Handle form submission
  var form = document.getElementById("payment-form");
  if (!form) {
    console.error("Payment form not found!");
    return;
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();

    // Disable the submit button to prevent repeated clicks
    var submitButton = document.getElementById("submit-button");
    submitButton.disabled = true;

    var saveInfo = document.getElementById("id-save-info").checked;
    var csrfTokenElement = document.getElementsByName("csrfmiddlewaretoken")[0];

    if (!csrfTokenElement) {
      console.error("CSRF token input not found!");
      submitButton.disabled = false;
      return;
    }

    var csrfToken = csrfTokenElement.value;
    var clientSecret = form.dataset.secret;

    if (!clientSecret) {
      console.error("Client secret not found in form dataset!");
      submitButton.disabled = false;
      return;
    }

    var postData = {
      csrfmiddlewaretoken: csrfToken,
      client_secret: clientSecret,
      save_info: saveInfo,
    };
    var url = "/checkout/cache_checkout_data/";

    // Post data to cache_checkout_data view
    fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(postData),
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Network response was not ok.");
        }
        return response.json();
      })
      .then(function (data) {
        // Confirm the card payment
        stripe
          .confirmCardPayment(clientSecret, {
            payment_method: {
              card: card,
              billing_details: {
                name: form.full_name.value,
                email: form.email.value,
              },
            },
          })
          .then(function (result) {
            if (result.error) {
              // Show error to your customer
              var errorElement = document.getElementById("card-errors");
              errorElement.textContent = result.error.message;
              submitButton.disabled = false;
            } else {
              // The payment has been processed!
              if (result.paymentIntent.status === "succeeded") {
                // Submit the form
                form.submit();
              }
            }
          });
      })
      .catch(function (error) {
        // Display error to the customer
        var errorElement = document.getElementById("card-errors");
        errorElement.textContent = error.message;
        submitButton.disabled = false;
      });
  });
});
