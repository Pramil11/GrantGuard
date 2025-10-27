document.querySelector("#loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.querySelector("#loginEmail").value;
  const password = document.querySelector("#loginPassword").value;

  const response = await fetch("/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
  });

  if (response.redirected) {
    window.location.href = response.url;
  } else {
    const text = await response.text();
    if (text.includes("Welcome") || text.includes("Dashboard")) {
      window.location.href = "/dashboard";
    } else {
      alert("Invalid email or password. Please try again.");
    }
  }
});
