/* Custom dropdown — sr-only select + htmx.ajax (ERR-82) */
(function () {
  "use strict";

  var OPEN_CLASS = "is-open";
  var SELECTED_CLASS = "is-selected";
  var ACTIVE_CLASS = "is-active";

  function closestDropdown(node) {
    return node && node.closest ? node.closest("[data-custom-dropdown]") : null;
  }

  function getParts(root) {
    return {
      trigger: root.querySelector("[data-dropdown-trigger]"),
      menu: root.querySelector("[data-dropdown-menu]"),
      label: root.querySelector("[data-dropdown-label]"),
      input: root.querySelector("[data-dropdown-input]"),
      options: root.querySelectorAll("[data-dropdown-option]"),
    };
  }

  function closeDropdown(root) {
    if (!root) return;
    var parts = getParts(root);
    root.classList.remove(OPEN_CLASS);
    if (parts.trigger) {
      parts.trigger.setAttribute("aria-expanded", "false");
    }
    if (parts.menu) {
      parts.menu.setAttribute("hidden", "");
    }
    parts.options.forEach(function (opt) {
      opt.classList.remove(ACTIVE_CLASS);
    });
  }

  function closeAll(except) {
    document.querySelectorAll("[data-custom-dropdown]." + OPEN_CLASS).forEach(function (el) {
      if (el !== except) closeDropdown(el);
    });
  }

  function openDropdown(root) {
    var parts = getParts(root);
    closeAll(root);
    root.classList.add(OPEN_CLASS);
    if (parts.trigger) {
      parts.trigger.setAttribute("aria-expanded", "true");
    }
    if (parts.menu) {
      parts.menu.removeAttribute("hidden");
    }
    var selected = root.querySelector("[data-dropdown-option]." + SELECTED_CLASS);
    if (selected) {
      selected.classList.add(ACTIVE_CLASS);
      selected.focus({ preventScroll: true });
    }
  }

  function syncLinkedTarget(root, value) {
    var selector = root.getAttribute("data-sync-target");
    if (!selector) return;
    var target = document.querySelector(selector);
    if (!target) return;
    target.value = value;
  }

  function setSelected(root, value, text) {
    var parts = getParts(root);
    if (parts.input) {
      parts.input.value = value;
    }
    if (parts.label && typeof text === "string") {
      parts.label.textContent = text;
    }
    parts.options.forEach(function (opt) {
      var isMatch = (opt.getAttribute("data-value") || "") === value;
      opt.classList.toggle(SELECTED_CLASS, isMatch);
      opt.setAttribute("aria-selected", isMatch ? "true" : "false");
    });
    syncLinkedTarget(root, value);
  }

  function submitViaHtmx(root) {
    var form = root.closest("form");
    if (!form || !window.htmx) return;

    var url = form.getAttribute("hx-get") || form.getAttribute("action") || window.location.pathname;
    var target = form.getAttribute("hx-target");
    var swap = form.getAttribute("hx-swap") || "innerHTML";
    var pushAttr = form.getAttribute("hx-push-url");
    var opts = {
      source: form,
      swap: swap,
    };

    if (target) opts.target = target;
    if (pushAttr === "true") opts.pushUrl = true;
    else if (pushAttr && pushAttr !== "false") opts.pushUrl = pushAttr;

    window.htmx.ajax("GET", url, opts);
  }

  function selectOption(root, option, shouldSubmit) {
    if (!option) return;
    var value = option.getAttribute("data-value") || "";
    var text = (option.getAttribute("data-label") || option.textContent || "").trim();
    setSelected(root, value, text);
    closeDropdown(root);
    var parts = getParts(root);
    if (parts.trigger) parts.trigger.focus({ preventScroll: true });
    if (shouldSubmit) submitViaHtmx(root);
  }

  function bindDropdown(root) {
    if (!root || root.dataset.dropdownBound === "1") return;
    var parts = getParts(root);
    if (!parts.trigger || !parts.menu || !parts.input) return;
    root.dataset.dropdownBound = "1";

    parts.trigger.setAttribute("aria-expanded", "false");
    parts.trigger.setAttribute("aria-haspopup", "listbox");
    parts.menu.setAttribute("role", "listbox");
    parts.menu.setAttribute("hidden", "");

    var current = parts.input.value || "";
    var currentOpt = null;
    parts.options.forEach(function (opt) {
      if ((opt.getAttribute("data-value") || "") === current) currentOpt = opt;
    });
    if (currentOpt) {
      setSelected(root, current, (currentOpt.getAttribute("data-label") || currentOpt.textContent || "").trim());
    }

    parts.trigger.addEventListener("click", function (event) {
      event.preventDefault();
      if (root.classList.contains(OPEN_CLASS)) closeDropdown(root);
      else openDropdown(root);
    });

    parts.menu.addEventListener("click", function (event) {
      var option = event.target.closest("[data-dropdown-option]");
      if (!option || !parts.menu.contains(option)) return;
      event.preventDefault();
      selectOption(root, option, true);
    });

    parts.trigger.addEventListener("keydown", function (event) {
      if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        if (!root.classList.contains(OPEN_CLASS)) openDropdown(root);
      } else if (event.key === "Escape") {
        closeDropdown(root);
      }
    });

    parts.menu.addEventListener("keydown", function (event) {
      var opts = Array.prototype.slice.call(parts.options);
      var active = parts.menu.querySelector("[data-dropdown-option]." + ACTIVE_CLASS) ||
        parts.menu.querySelector("[data-dropdown-option]." + SELECTED_CLASS);
      var idx = opts.indexOf(active);

      if (event.key === "Escape") {
        event.preventDefault();
        closeDropdown(root);
        parts.trigger.focus({ preventScroll: true });
        return;
      }

      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        if (!opts.length) return;
        var next = event.key === "ArrowDown"
          ? (idx + 1) % opts.length
          : (idx <= 0 ? opts.length - 1 : idx - 1);
        opts.forEach(function (opt) { opt.classList.remove(ACTIVE_CLASS); });
        opts[next].classList.add(ACTIVE_CLASS);
        opts[next].focus({ preventScroll: true });
        return;
      }

      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectOption(root, active || opts[0], true);
      }
    });

    parts.options.forEach(function (opt) {
      if (!opt.hasAttribute("tabindex")) opt.setAttribute("tabindex", "-1");
      if (!opt.hasAttribute("role")) opt.setAttribute("role", "option");
    });
  }

  function initCustomDropdown(scope) {
    var root = scope && scope.querySelectorAll ? scope : document;
    root.querySelectorAll("[data-custom-dropdown]").forEach(bindDropdown);
  }

  document.addEventListener("DOMContentLoaded", function () {
    initCustomDropdown(document);

    document.addEventListener("click", function (event) {
      if (closestDropdown(event.target)) return;
      closeAll(null);
    });

    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") return;
      closeAll(null);
    });

    document.body.addEventListener("htmx:afterSwap", function (event) {
      initCustomDropdown(event.detail && event.detail.target ? event.detail.target : document);
    });
  });

  window.initCustomDropdown = initCustomDropdown;
})();
