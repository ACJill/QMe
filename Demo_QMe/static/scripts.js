function getMenuSuggestion() {
    const userInput = document.getElementById("user_input").value;
    $.ajax({
	url: "http://127.0.0.1:5000/",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({ "user_input": userInput }),
        success: function (response) {
            document.getElementById("menu_suggestion").innerText = response.suggestion;
        },
        error: function (error) {
            console.error("Error:", error);
        }
    });
}

