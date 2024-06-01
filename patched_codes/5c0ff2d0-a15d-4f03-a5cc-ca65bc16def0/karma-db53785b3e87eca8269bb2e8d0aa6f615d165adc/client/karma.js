// Predefined allowed URLs for redirection
const allowedUrls = ["https://trusted.example.com", "https://another-trusted.example.com"];

if (returnUrl) {
  // Validate the returnUrl against the allowed URLs
  if (allowedUrls.includes(returnUrl)) {
    location.href = returnUrl;
  } else {
    console.error("Blocked potential untrusted URL redirection to: ", returnUrl);
  }
}
