document.addEventListener('DOMContentLoaded', function () {
  var input = document.getElementById("sendData");
  if (input) {
    input.addEventListener("keypress", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        input.closest("form").submit();
      }
    });
  }
});