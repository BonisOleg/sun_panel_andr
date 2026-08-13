(function () {
  "use strict";

  const methodInputs = document.querySelectorAll('input[name="shipping_method"]');
  if (!methodInputs.length) return;

  const delivery = document.getElementById("delivery-fields");
  const np = document.getElementById("np-fields");
  const cityQ = document.getElementById("np-city-q");
  const cityResults = document.getElementById("np-city-results");
  const cityRef = document.getElementById("np-city-ref");
  const cityName = document.getElementById("np-city-name");
  const citySelected = document.getElementById("np-city-selected");
  const whQ = document.getElementById("np-wh-q");
  const whResults = document.getElementById("np-wh-results");
  const whRef = document.getElementById("np-wh-ref");
  const whName = document.getElementById("np-wh-name");
  const whSelected = document.getElementById("np-wh-selected");

  function currentMethod() {
    const checked = document.querySelector('input[name="shipping_method"]:checked');
    return checked ? checked.value : "";
  }

  function togglePanels() {
    const v = currentMethod();
    if (delivery) delivery.hidden = v !== "delivery";
    if (np) np.hidden = v !== "nova_poshta";
  }

  methodInputs.forEach(function (input) {
    input.addEventListener("change", togglePanels);
  });
  togglePanels();

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
          const res = await fetch("/api/np/cities/?q=" + encodeURIComponent(q));
          const data = await res.json();
          if (!cityResults) return;
          cityResults.innerHTML = (data.results || [])
            .map(function (row) {
              return (
                '<button type="button" class="np-item" data-ref="' +
                row.ref +
                '" data-name="' +
                String(row.name).replace(/"/g, "&quot;") +
                '">' +
                row.name +
                (row.area ? " (" + row.area + ")" : "") +
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
      if (cityRef) cityRef.value = btn.dataset.ref || "";
      if (cityName) cityName.value = name;
      if (cityQ) cityQ.value = name;
      if (citySelected) citySelected.textContent = name ? "Обрано: " + name : "";
      cityResults.innerHTML = "";
      if (whRef) whRef.value = "";
      if (whName) whName.value = "";
      if (whSelected) whSelected.textContent = "";
      if (whQ) {
        whQ.value = "";
        whQ.focus();
      }
    });
  }

  let whTimer;
  if (whQ) {
    whQ.addEventListener("input", function () {
      clearTimeout(whTimer);
      const q = whQ.value.trim();
      whTimer = setTimeout(async function () {
        if (!cityRef || !cityRef.value) return;
        try {
          const res = await fetch(
            "/api/np/warehouses/?city=" +
              encodeURIComponent(cityRef.value) +
              "&q=" +
              encodeURIComponent(q)
          );
          const data = await res.json();
          if (!whResults) return;
          whResults.innerHTML = (data.results || [])
            .map(function (row) {
              return (
                '<button type="button" class="np-item" data-ref="' +
                row.ref +
                '" data-name="' +
                String(row.description).replace(/"/g, "&quot;") +
                '">' +
                row.description +
                "</button>"
              );
            })
            .join("");
        } catch (_err) {
          if (whResults) {
            whResults.innerHTML =
              '<p class="np-selected">Не вдалося завантажити відділення</p>';
          }
        }
      }, 250);
    });
  }

  if (whResults) {
    whResults.addEventListener("click", function (e) {
      const btn = e.target.closest(".np-item");
      if (!btn) return;
      const name = btn.dataset.name || "";
      if (whRef) whRef.value = btn.dataset.ref || "";
      if (whName) whName.value = name;
      if (whQ) whQ.value = name;
      if (whSelected) whSelected.textContent = name ? "Обрано: " + name : "";
      whResults.innerHTML = "";
    });
  }

  if (cityQ && cityName && cityName.value) {
    cityQ.value = cityName.value;
  }
  if (whQ && whName && whName.value) {
    whQ.value = whName.value;
  }
})();
