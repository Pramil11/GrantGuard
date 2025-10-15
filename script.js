const openSignup = document.getElementById("showSignup");
const closeSignup = document.getElementById("closeSignup");
const signupOverlay = document.getElementById("signupOverlay");

openSignup.addEventListener("click", () => {
  signupOverlay.style.display = "flex";
});

closeSignup.addEventListener("click", (e) => {
  e.preventDefault();
  signupOverlay.style.display = "none";
});

document.getElementById("loginForm").addEventListener("submit", (e) => {
  e.preventDefault();
  alert(`Welcome back to GrandGuard, ${loginEmail.value}!`);
});

document.getElementById("signupForm").addEventListener("submit", (e) => {
  e.preventDefault();
  alert(`Account created for ${firstName.value} ${lastName.value}!`);
});
