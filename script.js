// script.js
window.lastEvent = null;

document.addEventListener("DOMContentLoaded", () => {
    const inputBox = document.getElementById("customInput");
    const sendBtn = document.getElementById("sendBtn");
    const micBtn = document.getElementById("micBtn");

    if (inputBox && sendBtn) {
        inputBox.addEventListener("keydown", function (event) {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                sendBtn.click();
            }
        });

        sendBtn.addEventListener("click", () => {
            window.lastEvent = {
                type: "send-message",
                text: inputBox.value
            };
            inputBox.value = ""; // clear input after sending
            Streamlit.setComponentValue(window.lastEvent);
        });
    }

    if (micBtn) {
        micBtn.addEventListener("click", () => {
            window.lastEvent = {
                type: "mic-click"
            };
            Streamlit.setComponentValue(window.lastEvent);
        });
    }
});
