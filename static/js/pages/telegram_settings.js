document.addEventListener("DOMContentLoaded", function () {
  const generateBtn = document.getElementById("generateLinkBtn");
  const linkContainer = document.getElementById("linkContainer");
  const telegramLink = document.getElementById("telegramLink");

  if (generateBtn) {
    generateBtn.addEventListener("click", function () {
      const url = generateBtn.getAttribute("data-url");
      if (!url) return;

      generateBtn.disabled = true;
      generateBtn.textContent = "Generating...";

      fetch(url)
        .then((response) => response.json())
        .then((data) => {
          if (data.status === "success") {
            telegramLink.href = data.link;
            telegramLink.textContent = "👉 Open Telegram Bot";
            linkContainer.style.display = "block";
            generateBtn.textContent = "Regenerate Link";
          } else {
            alert("Error generating Telegram link. Please try again.");
            generateBtn.textContent = "Generate Link";
          }
          generateBtn.disabled = false;
        })
        .catch((err) => {
          console.error(err);
          alert("An error occurred. Please try again.");
          generateBtn.textContent = "Generate Link";
          generateBtn.disabled = false;
        });
    });
  }

  const sendTestBtn = document.getElementById("sendTestBtn");
  const testMessageStatus = document.getElementById("testMessageStatus");

  if (sendTestBtn && testMessageStatus) {
    sendTestBtn.addEventListener("click", function () {
      const url = sendTestBtn.getAttribute("data-url");
      if (!url) return;

      sendTestBtn.disabled = true;
      sendTestBtn.textContent = "Sending...";
      testMessageStatus.style.display = "none";
      testMessageStatus.className = "alert"; // Reset classes

      // Get CSRF token from the form
      const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
      const csrfToken = csrfInput ? csrfInput.value : '';

      fetch(url, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
          "Content-Type": "application/json"
        }
      })
        .then((response) => response.json())
        .then((data) => {
          testMessageStatus.textContent = data.message;
          if (data.status === "success") {
            testMessageStatus.classList.add("alert--success");
          } else {
            testMessageStatus.classList.add("alert--error");
          }
          testMessageStatus.style.display = "flex";
          sendTestBtn.textContent = "Send Test Message";
          sendTestBtn.disabled = false;
        })
        .catch((err) => {
          console.error(err);
          testMessageStatus.textContent = "An error occurred while sending the test message.";
          testMessageStatus.classList.add("alert--error");
          testMessageStatus.style.display = "flex";
          sendTestBtn.textContent = "Send Test Message";
          sendTestBtn.disabled = false;
        });
    });
  }
});
