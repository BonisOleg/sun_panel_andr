/* GTM dataLayer: purchase (сторінка «Дякуємо») і generate_lead (форма контактів).
 * Підключається в <head> після consent.js, БЕЗ defer — purchase потрапляє в
 * dataLayer ще до рендеру <body>. Push робиться завжди; чи передавати дані в
 * Google, вирішує GTM + Consent Mode (consent.js). Без inline-скриптів (CSP).
 */
(function () {
  "use strict";

  var TX_KEY = "soliron_gtm_tx";
  window.dataLayer = window.dataLayer || [];

  function readTx() {
    try {
      return JSON.parse(window.localStorage.getItem(TX_KEY) || "[]") || [];
    } catch (err) {
      return [];
    }
  }

  function rememberTx(id) {
    try {
      var list = readTx();
      list.push(id);
      window.localStorage.setItem(TX_KEY, JSON.stringify(list.slice(-20)));
    } catch (err) {
      /* Safari private mode — сервер однаково віддає подію один раз */
    }
  }

  function pushPurchase() {
    var el = document.getElementById("gtm-purchase-data");
    if (!el || el.dataset.pushed === "1") return;
    el.dataset.pushed = "1";
    var payload;
    try {
      payload = JSON.parse(el.textContent || "null");
    } catch (err) {
      return;
    }
    if (!payload || payload.event !== "purchase" || !payload.ecommerce) return;
    var tx = String(payload.ecommerce.transaction_id || "");
    if (tx && readTx().indexOf(tx) !== -1) return; /* страховка від дубля */
    window.dataLayer.push({ ecommerce: null }); /* очистка попереднього ecommerce (рекомендація Google) */
    window.dataLayer.push(payload);
    if (tx) rememberTx(tx);
  }

  function pushLead(formId) {
    window.dataLayer.push({
      event: "generate_lead",
      form_id: formId || "contact_form",
    });
  }

  /* HTMX: сервер після збереження ліда шле заголовок HX-Trigger: solironLead */
  document.addEventListener("solironLead", function (event) {
    var detail = (event && event.detail) || {};
    pushLead(detail.form_id);
  });

  /* Без HTMX (звичайний POST): маркер у відповіді успіху */
  function pushLeadMarker() {
    var marker = document.querySelector("[data-gtm-lead]");
    if (!marker || marker.dataset.pushed === "1") return;
    marker.dataset.pushed = "1";
    pushLead(marker.getAttribute("data-gtm-lead"));
  }

  pushPurchase();
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      pushPurchase();
      pushLeadMarker();
    });
  } else {
    pushLeadMarker();
  }
})();
