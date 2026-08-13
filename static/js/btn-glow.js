(function () {
  "use strict";

  var SELECTOR =
    ".btn:not(.btn--ghost):not(.btn--brand), .btn-primary, .btn-sun, .btn-glow";
  var FLASH_MS = 520;
  var FLASH_MS_REDUCED = 220;

  function wrapLabel(btn) {
    if (btn.querySelector(":scope > .btn__label")) return;
    var label = document.createElement("span");
    label.className = "btn__label";
    while (btn.firstChild) {
      label.appendChild(btn.firstChild);
    }
    btn.appendChild(label);
  }

  function enhance(root) {
    var scope = root && root.querySelectorAll ? root : document;
    scope.querySelectorAll(SELECTOR).forEach(wrapLabel);
  }

  function needsTouchFlash() {
    return window.matchMedia("(hover: none)").matches;
  }

  function flashDuration() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ? FLASH_MS_REDUCED
      : FLASH_MS;
  }

  function isPlainNavigationLink(btn) {
    if (btn.tagName !== "A" || !btn.href) return false;
    if (btn.getAttribute("target") === "_blank") return false;
    if (btn.hasAttribute("download")) return false;
    if (btn.hasAttribute("hx-get") || btn.hasAttribute("hx-post") || btn.hasAttribute("hx-put") || btn.hasAttribute("hx-delete") || btn.hasAttribute("hx-patch")) {
      return false;
    }
    var href = btn.getAttribute("href") || "";
    if (!href || href.charAt(0) === "#") return false;
    return true;
  }

  function clearFlash(btn) {
    btn.classList.remove("is-sun-active");
    btn.removeAttribute("data-sun-flashing");
    if (btn._sunFlashTimer) {
      window.clearTimeout(btn._sunFlashTimer);
      btn._sunFlashTimer = null;
    }
  }

  function runFlash(btn, after) {
    if (btn.getAttribute("data-sun-flashing") === "1") return;
    btn.setAttribute("data-sun-flashing", "1");
    btn.classList.add("is-sun-active");
    btn._sunFlashTimer = window.setTimeout(function () {
      clearFlash(btn);
      if (typeof after === "function") after();
    }, flashDuration());
  }

  function onPointerDown(event) {
    if (!needsTouchFlash()) return;
    if (event.pointerType === "mouse") return;
    if (event.button != null && event.button !== 0) return;

    var btn = event.target.closest(SELECTOR);
    if (!btn || btn.disabled || btn.getAttribute("aria-disabled") === "true") return;
    if (btn.getAttribute("data-sun-flashing") === "1") return;

    /* Start sun immediately — before UA tap-highlight / focus flash */
    btn.classList.add("is-sun-active");
  }

  function onClickCapture(event) {
    if (!needsTouchFlash()) return;
    if (event.defaultPrevented) return;
    if (event.button != null && event.button !== 0) return;

    var btn = event.target.closest(SELECTOR);
    if (!btn || btn.disabled || btn.getAttribute("aria-disabled") === "true") return;
    if (btn.getAttribute("data-sun-flashing") === "1") return;

    if (isPlainNavigationLink(btn)) {
      event.preventDefault();
      event.stopPropagation();
      runFlash(btn, function () {
        window.location.assign(btn.href);
      });
      return;
    }

    runFlash(btn);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      enhance(document);
    });
  } else {
    enhance(document);
  }

  document.addEventListener("pointerdown", onPointerDown, true);
  document.addEventListener("click", onClickCapture, true);

  document.body.addEventListener("htmx:afterSwap", function (event) {
    enhance(event.detail && event.detail.target ? event.detail.target : document);
  });
})();
