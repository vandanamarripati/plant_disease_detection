// Handles the fertilizer recommendation form and renders the result
// returned by /api/fertilizer-recommend.

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("fertilizerForm");
  const btn = document.getElementById("fertBtn");
  const resultEmpty = document.getElementById("fertResultEmpty");
  const resultContent = document.getElementById("fertResultContent");

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      crop: document.getElementById("crop").value,
      n: document.getElementById("n").value,
      p: document.getElementById("p").value,
      k: document.getElementById("k").value,
      ph: document.getElementById("ph").value,
    };

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Calculating...';

    try {
      const res = await fetch("/api/fertilizer-recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (!res.ok) throw new Error(data.error || "Something went wrong.");
      renderResult(data);
    } catch (err) {
      resultEmpty.style.display = "none";
      resultContent.style.display = "block";
      resultContent.innerHTML = `<div class="result-badge high">Error</div><p>${err.message}</p>`;
    } finally {
      btn.disabled = false;
      btn.textContent = "Get recommendation";
    }
  });

  function statusRow(nutrient, value, status) {
    return `
      <div class="nutrient-row">
        <span class="nutrient-name">${nutrient}: ${value}</span>
        <span class="nutrient-status ${status}">${status}</span>
      </div>`;
  }

  function fertilizerList(fertilizers) {
    if (!fertilizers || fertilizers.length === 0) return "";
    return fertilizers
      .map(
        (f) => `
        <div class="fert-suggestion">
          <div class="fname">${f.name}</div>
          <p class="fnote">${f.note}</p>
        </div>`
      )
      .join("");
  }

  function renderResult(data) {
    resultEmpty.style.display = "none";
    resultContent.style.display = "block";
    resultContent.classList.add("fade-in");

    const badgeClass = data.all_optimal ? "healthy" : "moderate";
    const badgeText = data.all_optimal ? "Balanced soil" : "Action needed";

    const statusRows =
      statusRow("Nitrogen (N)", data.soil_values.N, data.status.N) +
      statusRow("Phosphorus (P)", data.soil_values.P, data.status.P) +
      statusRow("Potassium (K)", data.soil_values.K, data.status.K) +
      statusRow("Soil pH", data.soil_values.ph, data.status.ph);

    let recsHtml = "";
    data.recommendations.forEach((rec) => {
      if (rec.issue === "deficient") {
        recsHtml += `<div class="result-section">
          <h4>${rec.nutrient} deficiency — recommended fertilizers</h4>
          ${fertilizerList(rec.fertilizers)}
        </div>`;
      } else if (rec.issue === "excess") {
        recsHtml += `<div class="result-section">
          <h4>${rec.nutrient} excess</h4>
          <p>${rec.note}</p>
        </div>`;
      }
    });

    const phHtml = data.ph_note
      ? `<div class="result-section"><h4>Soil pH</h4><p>${data.ph_note}</p></div>`
      : "";

    resultContent.innerHTML = `
      <div class="result-badge ${badgeClass}">${badgeText}</div>
      <h3 class="result-title">${data.crop}</h3>
      <div class="result-plant">Based on your soil test values</div>

      <div class="result-section">
        <h4>Nutrient status</h4>
        ${statusRows}
      </div>

      ${recsHtml}
      ${phHtml}

      <div class="result-section">
        <h4>Summary</h4>
        <p>${data.summary}</p>
      </div>
    `;
  }
});
