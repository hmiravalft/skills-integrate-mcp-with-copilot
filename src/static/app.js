document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const logoutBtn = document.getElementById("logout-btn");
  const userInfo = document.getElementById("user-info");
  const signupSection = document.getElementById("signup-container");
  const messageDiv = document.getElementById("message");

  let authToken = null;
  let currentUser = null;

  const setMessage = (text, type = "info") => {
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.classList.remove("hidden");

    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  };

  const getAuthHeaders = () => {
    const headers = { "Content-Type": "application/json" };
    if (authToken) {
      headers.Authorization = `Bearer ${authToken}`;
    }
    return headers;
  };

  const updateAuthUI = () => {
    if (currentUser) {
      userInfo.textContent = `Signed in as ${currentUser.name || currentUser.email} (${currentUser.role})`;
      logoutBtn.classList.remove("hidden");
      signupSection.classList.remove("hidden");
    } else {
      userInfo.textContent = "Not signed in.";
      logoutBtn.classList.add("hidden");
      signupSection.classList.add("hidden");
    }
  };

  const saveAuthState = (user, token) => {
    currentUser = user;
    authToken = token;
    localStorage.setItem("authToken", token);
    localStorage.setItem("currentUser", JSON.stringify(user));
    updateAuthUI();
  };

  const clearAuthState = () => {
    currentUser = null;
    authToken = null;
    localStorage.removeItem("authToken");
    localStorage.removeItem("currentUser");
    updateAuthUI();
  };

  const loadAuthState = () => {
    const savedToken = localStorage.getItem("authToken");
    const savedUser = localStorage.getItem("currentUser");

    if (savedToken && savedUser) {
      authToken = savedToken;
      currentUser = JSON.parse(savedUser);
    }
    updateAuthUI();
  };

  const fetchActivities = async () => {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      activitiesList.innerHTML = "";
      activitySelect.innerHTML = "<option value=\"\">-- Select an activity --</option>";

      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        const participantsHTML = details.participants.length > 0
          ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants.map((email) =>
                  `<li><span class="participant-email">${email}</span><button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button></li>`
                ).join("")}
              </ul>
            </div>`
          : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  };

  const handleUnregister = async (event) => {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
          headers: getAuthHeaders(),
        }
      );

      const result = await response.json();
      if (response.ok) {
        setMessage(result.message, "success");
        fetchActivities();
      } else {
        setMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      setMessage("Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  };

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const activity = activitySelect.value;
    if (!activity) {
      setMessage("Please choose an activity to sign up for.", "error");
      return;
    }

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup`,
        {
          method: "POST",
          headers: getAuthHeaders(),
        }
      );
      const result = await response.json();
      if (response.ok) {
        setMessage(result.message, "success");
        signupForm.reset();
        fetchActivities();
      } else {
        setMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      setMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;

    try {
      const response = await fetch("/users/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const result = await response.json();
      if (response.ok) {
        saveAuthState(result.user, result.token);
        setMessage(`Logged in as ${result.user.email}`, "success");
        loginForm.reset();
      } else {
        setMessage(result.detail || "Login failed.", "error");
      }
    } catch (error) {
      setMessage("Login request failed. Please try again.", "error");
      console.error("Login error:", error);
    }
  });

  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("register-email").value;
    const password = document.getElementById("register-password").value;

    try {
      const response = await fetch("/users/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const result = await response.json();
      if (response.ok) {
        saveAuthState(result.user, result.token);
        setMessage(`Registered and signed in as ${result.user.email}`, "success");
        registerForm.reset();
      } else {
        setMessage(result.detail || "Registration failed.", "error");
      }
    } catch (error) {
      setMessage("Registration request failed. Please try again.", "error");
      console.error("Registration error:", error);
    }
  });

  logoutBtn.addEventListener("click", () => {
    clearAuthState();
    setMessage("You have been logged out.", "info");
  });

  loadAuthState();
  fetchActivities();
});
