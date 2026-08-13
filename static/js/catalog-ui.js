/* Catalog UI — filter tab glider + keep filter form on current path */
(function () {
  "use strict";

  function syncGlider(tabs) {
    if (!tabs) return;
    var glider = tabs.querySelector(".tab-glider");
    var active = tabs.querySelector(".filter-btn.is-active, .filter-btn.active");
    if (!glider || !active) return;
    glider.style.width = active.offsetWidth + "px";
    glider.style.transform = "translateX(" + active.offsetLeft + "px)";
  }

  function syncFilterFormPath() {
    var form = document.getElementById("catalog-filters");
    if (!form || !window.htmx) return;
    form.setAttribute("hx-get", window.location.pathname);
    window.htmx.process(form);
  }

  function initFilterTabs(root) {
    var scope = root || document;
    scope.querySelectorAll(".filter-tabs").forEach(function (tabs) {
      syncGlider(tabs);
      if (tabs.dataset.gliderBound) return;
      tabs.dataset.gliderBound = "1";

      tabs.addEventListener("click", function (event) {
        var btn = event.target.closest(".filter-btn");
        if (!btn || !tabs.contains(btn)) return;
        tabs.querySelectorAll(".filter-btn").forEach(function (el) {
          el.classList.toggle("is-active", el === btn);
          el.classList.toggle("active", el === btn);
        });
        syncGlider(tabs);
      });
    });
  }

  function isCatalogFilterRequest(elt) {
    if (!elt) return false;
    if (elt.id === "catalog-filters" || elt.closest("#catalog-filters")) return true;
    return elt.hasAttribute("data-filter-btn");
  }

  function isCatalogPagerRequest(elt) {
    return !!(elt && elt.closest && elt.closest(".catalog-grid__pager"));
  }

  var pendingCatalogPagerScroll = false;

  function scrollCatalogToTop() {
    var target = document.getElementById("catalog") || document.getElementById("catalog-grid");
    if (!target) return;

    var header = document.querySelector(".site-header");
    var offset = header ? header.getBoundingClientRect().height : 0;
    var top = window.pageYOffset + target.getBoundingClientRect().top - offset - 8;

    window.scrollTo(0, Math.max(0, top));
  }

  function scheduleCatalogScroll() {
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(scrollCatalogToTop);
    });
    // Retry after layout/history updates (iOS Safari / late paint).
    window.setTimeout(scrollCatalogToTop, 50);
    window.setTimeout(scrollCatalogToTop, 200);
  }

  document.addEventListener("DOMContentLoaded", function () {
    initFilterTabs(document);
    syncFilterFormPath();

    window.addEventListener("resize", function () {
      document.querySelectorAll(".filter-tabs").forEach(syncGlider);
    });

    document.body.addEventListener("htmx:configRequest", function (event) {
      if (!isCatalogFilterRequest(event.detail.elt)) return;
      delete event.detail.parameters.page;
    });

    // Flag before swap: pager links live inside #catalog-grid and are destroyed on replace.
    document.body.addEventListener("htmx:beforeRequest", function (event) {
      var detail = event.detail || {};
      if (!isCatalogPagerRequest(detail.elt)) return;
      pendingCatalogPagerScroll = true;
    });

    document.body.addEventListener("htmx:afterSwap", function () {
      initFilterTabs(document);
      document.querySelectorAll(".filter-tabs").forEach(syncGlider);
      syncFilterFormPath();
    });

    document.body.addEventListener("htmx:afterSettle", function (event) {
      var detail = event.detail || {};
      var target = detail.target;
      if (!pendingCatalogPagerScroll) return;
      if (!target || target.id !== "catalog-grid") return;
      pendingCatalogPagerScroll = false;
      scheduleCatalogScroll();
    });

    document.body.addEventListener("htmx:pushedIntoHistory", function () {
      syncFilterFormPath();
    });
  });
})();
