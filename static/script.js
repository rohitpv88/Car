function displayFileName(inputId) {
  const input = document.getElementById(inputId);
  const fileName = input.files[0] ? input.files[0].name : "No File Chosen";
  const fileNameElement = document.getElementById(inputId + "-file-name");
  fileNameElement.textContent = fileName;
}

function validateImage(inputId) {
  const input = document.getElementById(inputId);
  if (!input.files.length) {
    alert("Upload an Image");
    return false;
  }
  return true;
}

function validateVideo(inputId) {
  const input = document.getElementById(inputId);
  if (!input.files.length) {
    alert("Select Parking Slots or Upload a Video");
    return false;
  }
  return true;
}

function closePage() {
  fetch("/delete", { method: "POST" }).then((response) => {
    if (response.ok) {
      window.location.href = "/";
      availablePage.close();
    }
  });
}

function updateAvailableSlot() {
  fetch("/get_available_slot")
    .then((response) => response.json())
    .then((data) => {
      const availableSlotDiv = document.getElementById("available-slot");
      const totalAvailableSlot = data.totalAvailableSlot;
      const availableSlotListDiv = document.getElementById(
        "available-slot-list"
      );
      availableSlotListDiv.innerHTML = `Available Slot: ${data.availableSlot.join(
        ", "
      )}`;
      availableSlotDiv.innerHTML = `Total Available Slot: ${totalAvailableSlot}`;
    })
    .catch((error) => {
      console.error("Error Fetching Available Slot:", error);
    });
}
setInterval(updateAvailableSlot, 10000);

let availablePage = null;
function openAvailablePage() {
  availablePage = window.open("/available", "_blank");
}
