/* Оформлення: блокування кнопок + спінер одразу після першого кліку.
 * Кнопки вимикаються в setTimeout(0) — після того, як браузер уже зібрав дані
 * форми (інакше name="action" натиснутої кнопки не потрапить у POST) і лише
 * якщо інша валідація не скасувала submit. Сервер додатково ідемпотентний.
 */
(function () {
  "use strict";

  function lock(form, submitter) {
    form.dataset.submitting = "1";
    form.setAttribute("aria-busy", "true");
    form.querySelectorAll('button[type="submit"]').forEach(function (btn) {
      btn.disabled = true;
    });
    if (submitter) {
      submitter.classList.add("is-loading");
      var label = submitter.querySelector(".btn__label");
      if (label && submitter.dataset.loadingText) label.textContent = submitter.dataset.loadingText;
    }
  }

  function unlock(form) {
    delete form.dataset.submitting;
    form.removeAttribute("aria-busy");
    form.querySelectorAll('button[type="submit"]').forEach(function (btn) {
      btn.disabled = false;
      btn.classList.remove("is-loading");
      var label = btn.querySelector(".btn__label");
      if (label && btn.dataset.idleText) label.textContent = btn.dataset.idleText;
    });
  }

  function bind(form) {
    form.querySelectorAll("button[data-loading-text] .btn__label").forEach(function (label) {
      label.parentElement.dataset.idleText = label.textContent;
    });
    form.addEventListener("submit", function (event) {
      if (form.dataset.submitting === "1") {
        event.preventDefault();
        return;
      }
      var submitter = event.submitter || document.activeElement;
      window.setTimeout(function () {
        if (event.defaultPrevented) return;
        lock(form, submitter && submitter.tagName === "BUTTON" ? submitter : null);
      }, 0);
    });
  }

  function init() {
    document.querySelectorAll("form[data-checkout-form]").forEach(bind);
  }

  /* Повернення «Назад» з bfcache — кнопки знову активні */
  window.addEventListener("pageshow", function (event) {
    if (!event.persisted) return;
    document.querySelectorAll("form[data-checkout-form]").forEach(unlock);
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
