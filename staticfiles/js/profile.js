// Toggle Edit Profile Form
document.addEventListener("DOMContentLoaded", () => {
  console.log("Profile script loaded.");
  const editProfileBtn = document.getElementById("edit-profile-btn");
  const editProfileForm = document.getElementById("edit-profile-form");

  // Initial setup for button text based on form visibility
  if (editProfileForm.style.display === "none" || editProfileForm.style.display === "") {
    editProfileBtn.textContent = "Edit Profile"; // Default text when form is hidden or display style not set
  } else {
    editProfileBtn.textContent = "Hide Form"; // If somehow the form is initially visible
  }

  // Function to toggle the form visibility
  function toggleFormVisibility() {
    // Check if the form is currently hidden
    const isFormHidden = editProfileForm.style.display === "none" || editProfileForm.style.display === "";

    // Toggle form visibility
    editProfileForm.style.display = isFormHidden ? "block" : "none";

    // Update button text based on the form's visibility state
    editProfileBtn.textContent = isFormHidden ? "Hide Form" : "Edit Profile";
  }

  // Check if both elements are found
  if (editProfileBtn && editProfileForm) {
    editProfileBtn.addEventListener("click", toggleFormVisibility);
  } else {
    // Log error if elements are not found
    console.error("Edit profile button or form not found");
  }
});
