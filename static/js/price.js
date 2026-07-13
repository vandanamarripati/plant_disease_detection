// Handles the price prediction form and renders the result
// returned by /api/price-predict.

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("priceForm");
  const btn = document.getElementById("priceBtn");
  const resultEmpty = document.getElementById("priceResultEmpty");
  const resultContent = document.getElementById("priceResultContent");

  if (!form) return;

  const MONTH_NAMES = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      crop: document.getElementById("priceCrop").value,
      month: document.getElementById("priceMonth").value,
      year: document.getElementById("priceYear").value,
    };

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Predicting...';

    try {
      const res = await fetch("/api/price-predict", {
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
      btn.textContent = "Predict price";
    }
  });

  function renderResult(data) {
    resultEmpty.style.display = "none";
    resultContent.style.display = "block";
    resultContent.classList.add("fade-in");

    const demoBanner = data.demo_mode
      ? `<div class="demo-banner">&#9888; Seasonal-average estimate: no trained regression model found yet —
         run <code>model/train_price_model.py</code> for a more precise, trend-aware prediction.</div>`
      : "";

    const trendRows = data.trend
      .map((t) => `<div class="top3-row"><span>${MONTH_NAMES[t.month]}${t.year ? " " + t.year : ""}</span><span>Rs. ${t.price.toLocaleString("en-IN")}</span></div>`)
      .join("");

    resultContent.innerHTML = `
      ${demoBanner}
      <div class="result-badge moderate">Prediction</div>
      <h3 class="result-title">${data.crop}</h3>
      <div class="result-plant">Predicted market price</div>

      <div style="font-family: var(--font-mono); font-size: 2.4rem; color: var(--ink); margin-bottom: 6px;">
        Rs. ${data.predicted_price.toLocaleString("en-IN")}
      </div>
      <div class="confidence-label" style="margin-bottom: 22px;">${data.unit}</div>

      <div class="result-section">
        <h4>Next few months (seasonal trend)</h4>
        <div class="top3-list">${trendRows}</div>
      </div>
    `;
  }
});