/* Header live search — suggest UI + catalog filter-q sync (600d10 / §41) */
(function () {
  "use strict";

  var MIN_CHARS = 2;
  var DEBOUNCE_MS = 300;

  var searchRoot = document.querySelector("[data-header-search]");
  var searchInput = searchRoot
    ? searchRoot.querySelector(".header-search__input")
    : null;
  var resultsBox = document.querySelector("[data-header-search-results]");
  var syncTimer = null;

  if (!searchRoot || !searchInput || !resultsBox) return;

  function clearResults() {
    resultsBox.innerHTML = "";
    resultsBox.hidden = true;
  }

  function refreshResultsVisibility() {
    var hasContent = !!resultsBox.querySelector(
      ".header-search__list, .header-search__empty"
    );
    resultsBox.hidden = !hasContent;
  }

  function catalogFilterForm() {
    return document.getElementById("catalog-filters");
  }

  function syncCatalogQ(q) {
    var form = catalogFilterForm();
    var hidden = form ? form.querySelector("[data-filter-q]") : null;
    if (!form || !hidden || !window.htmx) return;

    hidden.value = q;

    var url =
      form.getAttribute("hx-get") ||
      form.getAttribute("action") ||
      window.location.pathname;
    var opts = {
      source: form,
      target: form.getAttribute("hx-target") || "#catalog-grid",
      swap: form.getAttribute("hx-swap") || "innerHTML",
    };
    if (form.getAttribute("hx-push-url") === "true") {
      opts.pushUrl = true;
    }
    window.htmx.ajax("GET", url, opts);
  }

  function scheduleCatalogSync() {
    if (!catalogFilterForm()) return;
    window.clearTimeout(syncTimer);
    syncTimer = window.setTimeout(function () {
      syncCatalogQ(searchInput.value.trim());
    }, DEBOUNCE_MS);
  }

  searchRoot.addEventListener("submit", function (event) {
    if (!catalogFilterForm()) return;
    event.preventDefault();
    window.clearTimeout(syncTimer);
    syncCatalogQ(searchInput.value.trim());
    clearResults();
    var header = document.querySelector("[data-site-header]");
    if (header) header.classList.remove("is-search-open");
  });

  searchInput.addEventListener("input", function () {
    var q = searchInput.value.trim();
    if (q.length < MIN_CHARS) clearResults();
    scheduleCatalogSync();
  });

  document.body.addEventListener("htmx:afterSwap", function (event) {
    var target = event.detail && event.detail.target;
    if (!target || target.id !== "header-search-results") return;
    refreshResultsVisibility();
  });

  document.addEventListener(
    "pointerdown",
    function (event) {
      var t = event.target;
      if (searchRoot.contains(t)) return;
      clearResults();
    },
    true
  );

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    clearResults();
  });

  window.addEventListener("header-search:clear", clearResults);
})();
