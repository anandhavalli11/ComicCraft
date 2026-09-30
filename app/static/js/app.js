```javascript
document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("comicForm");
    const button = document.getElementById("generateButton");
    const loading = document.getElementById("loading");

    if (!form || !button || !loading) {
        return;
    }


    form.addEventListener("submit", function (event) {

        // Prevent accidental double submission
        if (button.disabled) {
            event.preventDefault();
            return;
        }


        // Disable button
        button.disabled = true;


        // Change button text
        button.innerHTML = `
            <span>⏳</span>
            Creating Comic...
        `;


        // Hide the form while processing
        form.style.display = "none";


        // Show loading section
        loading.style.display = "block";
        loading.classList.add("active");

    });

});
```
