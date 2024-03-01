// Toggle Edit Profile Form
document.addEventListener("DOMContentLoaded", () => {
  const editProfileBtn = document.getElementById("edit-profile-btn");
  const editProfileForm = document.getElementById("edit-profile-form");

  // Log to check if elements are found
  console.log("Edit Profile Button:", editProfileBtn);
  console.log("Edit Profile Form:", editProfileForm);

  if (editProfileBtn && editProfileForm) {
    editProfileBtn.addEventListener("click", function () {
      console.log("Edit profile button clicked"); // Log button click
      const isFormHidden = editProfileForm.style.display === "none";
      console.log("Is form hidden before toggle:", isFormHidden); // Log current display state of form

      editProfileForm.style.display = isFormHidden ? "block" : "none";
      editProfileBtn.textContent = isFormHidden ? "Hide Form" : "Edit Profile";

      // Log the action taken
      console.log("New display style for form:", editProfileForm.style.display);
      console.log("New button text:", editProfileBtn.textContent);
    });
  } else {
    console.error("Edit profile button or form not found"); // Log if elements are not found
  }
});
