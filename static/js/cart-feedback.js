(function () {
  "use strict";

  var IN_CART_LABEL = "У кошику";
  var MSG_HIDE_MS = 3000;
  var hideTimers = typeof WeakMap === "function" ? new WeakMap() : null;

  function clampQtyInput(input) {
    var value = parseInt(input.value, 10);
    if (isNaN(value) || value < 1) value = 1;
    if (value > 999) value = 999;
    input.value = String(value);
  }

  function triggerQtyChange(input) {
    clampQtyInput(input);
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }

  /* Степер кількості на сторінці кошика / checkout (HTMX change) */
  document.addEventListener("click", function (event) {
    var btn = event.target.closest("[data-qty-minus], [data-qty-plus]");
    if (!btn || btn.disabled) return;

    var picker = btn.closest("[data-cart-qty-picker]");
    if (!picker) return;

    var input = picker.querySelector("[data-qty-input]");
    if (!input || input.disabled) return;

    event.preventDefault();
    var prev = input.value;
    if (btn.hasAttribute("data-qty-minus")) {
      input.stepDown();
    } else {
      input.stepUp();
    }
    clampQtyInput(input);
    if (input.value !== prev) {
      triggerQtyChange(input);
    }
  });

  function markFormAdded(form) {
    if (!form || form.getAttribute("data-cart-added") === "1") return;

    var btn = form.querySelector("[data-cart-add-btn]");
    var msg = form.querySelector("[data-cart-add-msg]");
    var label = btn ? btn.querySelector(".btn__label") : null;

    form.setAttribute("data-cart-added", "1");

    if (btn) {
      btn.disabled = true;
      btn.setAttribute("aria-disabled", "true");
      btn.classList.add("is-in-cart");
      if (label) {
        label.textContent = IN_CART_LABEL;
      } else {
        btn.textContent = IN_CART_LABEL;
      }
    }

    if (msg) {
      var card = form.closest(".product-card");
      msg.hidden = false;
      if (card) card.classList.add("has-cart-toast");

      if (hideTimers) {
        var prev = hideTimers.get(form);
        if (prev) clearTimeout(prev);
      }

      var timer = setTimeout(function () {
        msg.hidden = true;
        if (card) card.classList.remove("has-cart-toast");
        if (hideTimers) hideTimers.delete(form);
      }, MSG_HIDE_MS);

      if (hideTimers) hideTimers.set(form, timer);
    }

    var qtyInput = form.querySelector("[data-qty-input]");
    var qtyBtns = form.querySelectorAll("[data-qty-minus], [data-qty-plus]");
    if (qtyInput) {
      qtyInput.disabled = true;
    }
    qtyBtns.forEach(function (item) {
      item.disabled = true;
    });
  }

  function resolveForm(elt) {
    if (!elt) return null;
    if (elt.matches && elt.matches("[data-cart-add-form]")) return elt;
    if (elt.closest) return elt.closest("[data-cart-add-form]");
    return null;
  }

  document.body.addEventListener("htmx:afterRequest", function (event) {
    var detail = event.detail || {};
    if (!detail.successful) return;
    var form = resolveForm(detail.elt);
    if (!form) return;
    markFormAdded(form);
  });
})();
