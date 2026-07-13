// Handles the leaf-photo upload widget, the "scanning" preview animation,
// and rendering the diagnosis returned by /api/predict.

document.addEventListener("DOMContentLoaded", () => {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const previewWrap = document.getElementById("previewWrap");
  const previewImg = document.getElementById("previewImg");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const resetBtn = document.getElementById("resetBtn");
  const resultEmpty = document.getElementById("resultEmpty");
  const resultContent = document.getElementById("resultContent");

  let selectedFile = null;

  function showPreview(file) {
    const url = URL.createObjectURL(file);
    previewImg.src = url;
    previewWrap.style.display = "block";
    analyzeBtn.disabled = false;
  }

  function resetAll() {
    selectedFile = null;
    fileInput.value = "";
    previewWrap.style.display = "none";
    previewWrap.classList.remove("scanning");
    analyzeBtn.disabled = true;
    resultEmpty.style.display = "flex";
    resultContent.style.display = "none";
    resultContent.innerHTML = "";
  }

  // --- File selection (click) ---
  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files[0]) {
      selectedFile = fileInput.files[0];
      showPreview(selectedFile);
    }
  });

  // --- Drag & drop ---
  ["dragenter", "dragover"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("drag-over");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("drag-over");
    })
  );
  dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) {
      selectedFile = file;
      fileInput.files = e.dataTransfer.files;
      showPreview(file);
    }
  });

  resetBtn.addEventListener("click", resetAll);

  // --- Analyze ---
  analyzeBtn.addEventListener("click", async () => {
    if (!selectedFile) return;

    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '<span class="spinner"></span> Analyzing...';
    previewWrap.classList.add("scanning");

    const formData = new FormData();
    formData.append("image", selectedFile);

    try {
      const res = await fetch("/api/predict", { method: "POST", body: formData });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Something went wrong.");
      }
      renderResult(data);
    } catch (err) {
      resultEmpty.style.display = "none";
      resultContent.style.display = "block";
      resultContent.innerHTML = `
        <div class="result-badge high">Error</div>
        <p>${err.message || "Could not analyze the image. Please try another photo."}</p>
      `;
    } finally {
      previewWrap.classList.remove("scanning");
      analyzeBtn.disabled = false;
      analyzeBtn.textContent = "Analyze photo";
    }
  });

  function severityClass(status, severity) {
    if (status === "healthy") return "healthy";
    if (severity === "high") return "high";
    return "moderate";
  }

  function renderResult(data) {
    resultEmpty.style.display = "none";
    resultContent.style.display = "block";
    resultContent.classList.add("fade-in");

    const badgeClass = severityClass(data.status, data.severity);
    const badgeText = data.status === "healthy" ? "Healthy" : `${data.severity} severity`;

    const demoBanner = data.demo_mode
      ? `<div class="demo-banner">&#9888; Demo mode: no trained model file found, so this result comes from a
         simplified heuristic classifier — see the README to train the real CNN.</div>`
      : "";

    const top3Html = data.top3
      .map(
        (t) => `<div class="top3-row"><span>${t.label}</span><span>${t.confidence}%</span></div>`
      )
      .join("");

    resultContent.innerHTML = `
      ${demoBanner}
      <div class="result-badge ${badgeClass}">${badgeText}</div>
      <h3 class="result-title">${data.label}</h3>
      <div class="result-plant">${data.plant} &middot; scanned in ${data.inference_ms}ms</div>

      <div class="confidence-bar-track">
        <div class="confidence-bar-fill" style="width:${data.confidence}%"></div>
      </div>
      <div class="confidence-label">${data.confidence}% confidence</div>

      <div class="result-section">
        <h4>Recommended treatment</h4>
        <p>${data.remedy}</p>
      </div>
      <div class="result-section">
        <h4>Prevention</h4>
        <p>${data.prevention}</p>
      </div>
      <div class="result-section">
        <h4>Other possibilities</h4>
        <div class="top3-list">${top3Html}</div>
      </div>
    `;
  }
});
