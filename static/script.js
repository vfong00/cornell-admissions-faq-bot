document.getElementById("search-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const question = document.getElementById("question").value;
    const resultDiv = document.getElementById("result");

    // Clear previous result
    resultDiv.textContent = "Searching...";

    try {
        const response = await fetch("/search", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question }),
        });

        if (!response.ok) {
            throw new Error("Error: " + response.statusText);
        }

        const data = await response.json();

        // Redirect to response page
        if (data.redirect_url) {
            window.location.href = data.redirect_url;
        } else {
            resultDiv.textContent = "Unexpected error occurred.";
        }
    } catch (error) {
        resultDiv.textContent = "An error occurred. Please try again.";
        console.error(error);
    }
});