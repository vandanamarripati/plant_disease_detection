// Handles city search, geolocation, and rendering the weather dashboard
// returned by /api/weather.

document.addEventListener("DOMContentLoaded", () => {
  const cityInput = document.getElementById("cityInput");
  const searchBtn = document.getElementById("searchBtn");
  const locateBtn = document.getElementById("locateBtn");
  const resultsEl = document.getElementById("weatherResults");

  function setLoading() {
    resultsEl.innerHTML = `<div class="weather-empty"><span class="spinner"></span> Fetching live conditions...</div>`;
  }

  function setError(message) {
    resultsEl.innerHTML = `<div class="weather-empty">${message}</div>`;
  }

  async function fetchWeather(params) {
    setLoading();
    try {
      const query = new URLSearchParams(params).toString();
      const res = await fetch(`/api/weather?${query}`);
      const data = await res.json();

      if (data.error === "no_api_key") {
        setError(data.message);
        return;
      }
      if (data.error) {
        setError(data.message || "Could not fetch weather for that location.");
        return;
      }
      renderWeather(data);
    } catch (err) {
      setError("Network error — could not reach the weather service.");
    }
  }

  searchBtn.addEventListener("click", () => {
    const city = cityInput.value.trim();
    if (!city) return;
    fetchWeather({ city });
  });

  cityInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") searchBtn.click();
  });

  locateBtn.addEventListener("click", () => {
    if (!navigator.geolocation) {
      setError("Geolocation isn't supported by your browser. Try searching a city instead.");
      return;
    }
    setLoading();
    navigator.geolocation.getCurrentPosition(
      (pos) => fetchWeather({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
      () => setError("Couldn't access your location. Try searching a city instead.")
    );
  });

  function iconUrl(icon) {
    return `https://openweathermap.org/img/wn/${icon}@2x.png`;
  }

  function formatDay(dateStr) {
    const d = new Date(dateStr + "T00:00:00");
    return d.toLocaleDateString(undefined, { weekday: "short" });
  }

  function renderWeather(data) {
    const c = data.current;
    const loc = data.location;

    const forecastHtml = data.daily_forecast
      .map(
        (day) => `
        <div class="forecast-day">
          <div class="d">${formatDay(day.date)}</div>
          <img src="${iconUrl(day.icon)}" alt="${day.condition}" width="40" height="40" style="margin:0 auto;">
          <div class="t">${day.temp_max}&deg;/${day.temp_min}&deg;</div>
          <div class="rain">&#128167; ${day.rain_chance}%</div>
        </div>`
      )
      .join("");

    const tipsHtml = data.farming_tips
      .map(
        (tip) => `
        <div class="tip-item">
          <span class="tip-dot ${tip.type}"></span>
          <span>${tip.text}</span>
        </div>`
      )
      .join("");

    resultsEl.innerHTML = `
      <div class="weather-grid fade-in">
        <div class="weather-hero-card">
          <div class="weather-hero-top">
            <div>
              <div class="weather-loc">${loc.name}${loc.country ? ", " + loc.country : ""}</div>
              <div class="weather-desc">${c.description}</div>
            </div>
            <img src="${iconUrl(c.icon)}" alt="${c.condition}" width="64" height="64">
          </div>
          <div class="weather-temp">${Math.round(c.temp)}&deg;C</div>
          <div class="weather-meta">
            <div>Feels like<strong>${Math.round(c.feels_like)}&deg;C</strong></div>
            <div>Humidity<strong>${c.humidity}%</strong></div>
            <div>Wind<strong>${c.wind_speed} m/s</strong></div>
            <div>Clouds<strong>${c.clouds ?? "-"}%</strong></div>
          </div>
          <div class="forecast-row">${forecastHtml}</div>
        </div>

        <div class="tips-card">
          <h3>Farming advisory</h3>
          ${tipsHtml}
        </div>
      </div>
    `;
  }
});
