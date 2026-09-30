const fileInput = document.getElementById("file");
const dropzone = document.getElementById("dropzone");
const filenameEl = document.getElementById("filename");
const manufacturerEl = document.getElementById("manufacturer");
const newManufacturerEl = document.getElementById("new-manufacturer");
const fixtureNameEl = document.getElementById("fixture-name");
const generateBtn = document.getElementById("generate");
const previewEl = document.getElementById("preview");
const errorsEl = document.getElementById("errors");
const extractInfoEl = document.getElementById("extract-info");
const statusEl = document.getElementById("status");

function selectedManufacturer() {
  const created = newManufacturerEl.value.trim();
  if (created) return created;
  return manufacturerEl.value.trim();
}

function showErrors(errors, ok) {
  errorsEl.innerHTML = "";
  if (ok && (!errors || errors.length === 0)) {
    const li = document.createElement("li");
    li.className = "ok";
    li.textContent = "Syntax OK";
    errorsEl.appendChild(li);
    return;
  }
  for (const error of errors || []) {
    const li = document.createElement("li");
    li.textContent = `Line ${error.line}: ${error.message}`;
    errorsEl.appendChild(li);
  }
}

async function api(path, options) {
  const response = await fetch(path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail;
    if (typeof detail === "string") throw new Error(detail);
    if (detail && detail.message) throw new Error(detail.message);
    throw new Error(data.message || `Request failed (${response.status})`);
  }
  return data;
}

async function loadManufacturers() {
  const data = await api("api/manufacturers");
  manufacturerEl.innerHTML = '<option value="">Detect from PDF</option>';
  for (const name of data.manufacturers) {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    manufacturerEl.appendChild(option);
  }
}

async function loadHealth() {
  try {
    const data = await api("api/health");
    statusEl.textContent = data.has_openai_key
      ? `OpenAI ready · ${data.model}`
      : "Set openai_api_key in add-on options";
  } catch (error) {
    statusEl.textContent = error.message;
  }
}

fileInput.addEventListener("change", () => {
  filenameEl.textContent = fileInput.files[0]?.name || "No file selected";
});

["dragenter", "dragover"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.add("drag");
  });
});
["dragleave", "drop"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.remove("drag");
  });
});
dropzone.addEventListener("drop", (event) => {
  const file = event.dataTransfer.files[0];
  if (!file) return;
  const transfer = new DataTransfer();
  transfer.items.add(file);
  fileInput.files = transfer.files;
  filenameEl.textContent = file.name;
});

generateBtn.addEventListener("click", async () => {
  const file = fileInput.files[0];
  if (!file) {
    showErrors([{ line: 0, message: "Choose a PDF or image first." }], false);
    return;
  }
  generateBtn.disabled = true;
  extractInfoEl.textContent = "Reading DMX table…";
  try {
    const body = new FormData();
    body.append("file", file);
    body.append("manufacturer", selectedManufacturer());
    body.append("fixture_name", fixtureNameEl.value.trim());
    const data = await api("api/convert", { method: "POST", body });
    previewEl.value = data.text || "";
    showErrors(data.errors, data.ok);
    extractInfoEl.textContent = data.extraction || "";
    if (data.notes?.length) {
      extractInfoEl.textContent += "\n" + data.notes.join(" ");
    }
  } catch (error) {
    showErrors([{ line: 0, message: error.message }], false);
  } finally {
    generateBtn.disabled = false;
  }
});

document.getElementById("revalidate").addEventListener("click", async () => {
  const data = await api("api/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: previewEl.value }),
  });
  showErrors(data.errors, data.ok);
});

document.getElementById("download").addEventListener("click", () => {
  const manufacturer = selectedManufacturer() || "fixture";
  const blob = new Blob([previewEl.value], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${manufacturer}.txt`;
  link.click();
  URL.revokeObjectURL(url);
});

document.getElementById("append").addEventListener("click", async () => {
  const manufacturer = selectedManufacturer();
  if (!manufacturer) {
    showErrors([{ line: 0, message: "Choose or type a manufacturer before writing." }], false);
    return;
  }
  try {
    const data = await api("api/append", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ manufacturer, text: previewEl.value }),
    });
    showErrors([], true);
    extractInfoEl.textContent = `${data.action}: ${data.filename}`;
    await loadManufacturers();
  } catch (error) {
    showErrors([{ line: 0, message: error.message }], false);
  }
});

loadHealth();
loadManufacturers();
