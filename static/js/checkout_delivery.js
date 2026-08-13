(function () {
  "use strict";

  const panel = document.getElementById("delivery-fields");
  if (!panel) return;

  const modeInputs = panel.querySelectorAll('input[name="delivery_mode"]');
  const whBlock = document.getElementById("da-warehouse-block");
  const doorsBlock = document.getElementById("da-doors-block");
  const cityQ = document.getElementById("da-city-q");
  const cityResults = document.getElementById("da-city-results");
  const cityId = document.getElementById("da-city-id");
  const cityName = document.getElementById("da-city-name");
  const citySelected = document.getElementById("da-city-selected");
  const whQ = document.getElementById("da-wh-q");
  const whResults = document.getElementById("da-wh-results");
  const whId = document.getElementById("da-wh-id");
  const whName = document.getElementById("da-wh-name");
  const whSelected = document.getElementById("da-wh-selected");

  function escapeAttr(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;");
  }

  function currentMode() {
    const checked = panel.querySelector('input[name="delivery_mode"]:checked');
    return checked ? checked.value : "warehouse";
  }

  function toggleModeBlocks() {
    const mode = currentMode();
    const isWarehouse = mode === "warehouse";
    if (whBlock) whBlock.hidden = !isWarehouse;
    if (doorsBlock) doorsBlock.hidden = isWarehouse;
  }

  modeInputs.forEach(function (input) {
    input.addEventListener("change", toggleModeBlocks);
  });
  toggleModeBlocks();

  function clearWarehouse() {
    if (whId) whId.value = "";
    if (whName) whName.value = "";
    if (whSelected) whSelected.textContent = "";
    if (whResults) whResults.innerHTML = "";
    if (whQ) whQ.value = "";
  }

  let cityTimer;
  if (cityQ) {
    cityQ.addEventListener("input", function () {
      clearTimeout(cityTimer);
      const q = cityQ.value.trim();
      cityTimer = setTimeout(async function () {
        if (q.length < 2) {
          if (cityResults) cityResults.innerHTML = "";
          return;
        }
        try {
          const res = await fetch(
            "/api/delivery/cities/?q=" + encodeURIComponent(q)
          );
          const data = await res.json();
          if (!cityResults) return;
          cityResults.innerHTML = (data.results || [])
            .map(function (row) {
              return (
                '<button type="button" class="np-item" data-id="' +
                escapeAttr(row.id) +
                '" data-name="' +
                escapeAttr(row.name) +
                '">' +
                escapeAttr(row.name) +
                (row.region ? " (" + escapeAttr(row.region) + ")" : "") +
                "</button>"
              );
            })
            .join("");
        } catch (_err) {
          if (cityResults) {
            cityResults.innerHTML =
              '<p class="np-selected">Не вдалося завантажити міста</p>';
          }
        }
      }, 250);
    });
  }

  if (cityResults) {
    cityResults.addEventListener("click", function (e) {
      const btn = e.target.closest(".np-item");
      if (!btn) return;
      const name = btn.dataset.name || "";
      if (cityId) cityId.value = btn.dataset.id || "";
      if (cityName) cityName.value = name;
      if (cityQ) cityQ.value = name;
      if (citySelected) {
        citySelected.textContent = name ? "Обрано: " + name : "";
      }
      cityResults.innerHTML = "";
      clearWarehouse();
      if (whQ && currentMode() === "warehouse") whQ.focus();
    });
  }

  let whTimer;
  if (whQ) {
    whQ.addEventListener("input", function () {
      clearTimeout(whTimer);
      const q = whQ.value.trim();
      whTimer = setTimeout(async function () {
        if (!cityId || !cityId.value) return;
        try {
          const res = await fetch(
            "/api/delivery/warehouses/?city_id=" +
              encodeURIComponent(cityId.value) +
              "&q=" +
              encodeURIComponent(q)
          );
          const data = await res.json();
          if (!whResults) return;
          whResults.innerHTML = (data.results || [])
            .map(function (row) {
              const label = row.address
                ? row.name + " — " + row.address
                : row.name;
              return (
                '<button type="button" class="np-item" data-id="' +
                escapeAttr(row.id) +
                '" data-name="' +
                escapeAttr(row.name) +
                '">' +
                escapeAttr(label) +
                "</button>"
              );
            })
            .join("");
        } catch (_err) {
          if (whResults) {
            whResults.innerHTML =
              '<p class="np-selected">Не вдалося завантажити склади</p>';
          }
        }
      }, 250);
    });

    // iOS Safari: показати склади після фокусу, якщо місто вже обране
    whQ.addEventListener("focus", function () {
      if (cityId && cityId.value && !whResults.innerHTML) {
        whQ.dispatchEvent(new Event("input"));
      }
    });
  }

  if (whResults) {
    whResults.addEventListener("click", function (e) {
      const btn = e.target.closest(".np-item");
      if (!btn) return;
      const name = btn.dataset.name || "";
      if (whId) whId.value = btn.dataset.id || "";
      if (whName) whName.value = name;
      if (whQ) whQ.value = name;
      if (whSelected) {
        whSelected.textContent = name ? "Обрано: " + name : "";
      }
      whResults.innerHTML = "";
    });
  }

  // Відновлення після повернення на крок / reload
  if (cityQ && cityName && cityName.value) {
    cityQ.value = cityName.value;
  }
  if (whQ && whName && whName.value) {
    whQ.value = whName.value;
  }
})();
