(function () {
  "use strict";

  var root = document.querySelector("[data-product-page]");
  if (!root) return;

  var mainImg = root.querySelector("[data-gallery-image]");
  var thumbs = Array.prototype.slice.call(root.querySelectorAll("[data-gallery-thumb]"));
  var zoomBtn = root.querySelector("[data-gallery-zoom]");
  var lightbox = document.querySelector("[data-product-lightbox]");
  var lightboxImg = lightbox ? lightbox.querySelector("[data-lightbox-img]") : null;
  var lightboxClose = lightbox ? lightbox.querySelector("[data-lightbox-close]") : null;
  var lightboxStage = lightbox ? lightbox.querySelector("[data-lightbox-stage]") : null;
  var lightboxPrev = lightbox ? lightbox.querySelector("[data-lightbox-prev]") : null;
  var lightboxNext = lightbox ? lightbox.querySelector("[data-lightbox-next]") : null;
  var lightboxCounter = lightbox ? lightbox.querySelector("[data-lightbox-counter]") : null;
  var lightboxThumbs = lightbox ? lightbox.querySelector("[data-lightbox-thumbs]") : null;
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var activeIndex = 0;
  var images = [];
  var touchStartX = 0;
  var touchStartY = 0;
  var touchActive = false;

  function collectImages() {
    images = thumbs
      .map(function (btn) {
        return {
          src: btn.getAttribute("data-src") || "",
          alt: btn.getAttribute("data-alt") || "",
        };
      })
      .filter(function (item) {
        return Boolean(item.src);
      });

    if (!images.length && mainImg && mainImg.src) {
      images = [{ src: mainImg.currentSrc || mainImg.src, alt: mainImg.alt || "" }];
    }
  }

  function findIndexBySrc(src) {
    if (!src) return 0;
    var clean = src.split("?")[0];
    for (var i = 0; i < images.length; i += 1) {
      if (images[i].src === src || images[i].src.split("?")[0] === clean) {
        return i;
      }
    }
    return 0;
  }

  function setMain(src, alt, withFade) {
    if (!mainImg || !src) return;
    if (!withFade || reduceMotion.matches) {
      mainImg.src = src;
      if (alt != null) mainImg.alt = alt;
      return;
    }
    mainImg.classList.add("is-fading");
    window.setTimeout(function () {
      mainImg.src = src;
      if (alt != null) mainImg.alt = alt;
      mainImg.classList.remove("is-fading");
    }, 160);
  }

  function syncPageThumbs(index) {
    thumbs.forEach(function (item, i) {
      item.classList.toggle("is-active", i === index);
    });
  }

  function syncLightboxThumbs(index) {
    if (!lightboxThumbs) return;
    var buttons = lightboxThumbs.querySelectorAll("[data-lightbox-thumb]");
    buttons.forEach(function (item, i) {
      item.classList.toggle("is-active", i === index);
      if (i === index && typeof item.scrollIntoView === "function") {
        item.scrollIntoView({
          block: "nearest",
          inline: "center",
          behavior: reduceMotion.matches ? "auto" : "smooth",
        });
      }
    });
  }

  function updateCounter(index) {
    if (!lightboxCounter) return;
    if (images.length < 2) {
      lightboxCounter.hidden = true;
      lightboxCounter.textContent = "";
      return;
    }
    lightboxCounter.hidden = false;
    lightboxCounter.textContent = index + 1 + " / " + images.length;
  }

  function updateNavVisibility() {
    var multi = images.length > 1;
    if (lightboxPrev) lightboxPrev.hidden = !multi;
    if (lightboxNext) lightboxNext.hidden = !multi;
    if (lightboxThumbs) lightboxThumbs.hidden = !multi;
  }

  function renderLightboxThumbs() {
    if (!lightboxThumbs) return;
    lightboxThumbs.innerHTML = "";
    if (images.length < 2) {
      lightboxThumbs.hidden = true;
      return;
    }
    images.forEach(function (item, index) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "product-lightbox__thumb";
      btn.setAttribute("data-lightbox-thumb", "");
      btn.setAttribute("data-index", String(index));
      btn.setAttribute("aria-label", "Фото " + (index + 1));
      btn.setAttribute("role", "listitem");
      var img = document.createElement("img");
      img.src = item.src;
      img.alt = "";
      img.loading = "lazy";
      img.width = 80;
      img.height = 80;
      btn.appendChild(img);
      btn.addEventListener("click", function () {
        showImage(index, true);
      });
      lightboxThumbs.appendChild(btn);
    });
  }

  function showImage(index, syncMain) {
    if (!images.length) return;
    var next = ((index % images.length) + images.length) % images.length;
    var item = images[next];
    activeIndex = next;

    if (lightboxImg) {
      lightboxImg.src = item.src;
      lightboxImg.alt = item.alt || "";
    }

    updateCounter(next);
    syncLightboxThumbs(next);

    if (syncMain) {
      setMain(item.src, item.alt || "", true);
      syncPageThumbs(next);
    }
  }

  function step(delta) {
    if (images.length < 2) return;
    showImage(activeIndex + delta, true);
  }

  function openLightbox() {
    if (!lightbox || !lightboxImg || !images.length) return;
    activeIndex = findIndexBySrc(mainImg ? mainImg.currentSrc || mainImg.src : "");
    updateNavVisibility();
    renderLightboxThumbs();
    showImage(activeIndex, false);
    if (typeof lightbox.showModal === "function") {
      lightbox.showModal();
    }
  }

  function closeLightbox() {
    if (!lightbox) return;
    if (typeof lightbox.close === "function" && lightbox.open) {
      lightbox.close();
    }
  }

  function onKeydown(event) {
    if (!lightbox || !lightbox.open) return;
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      step(-1);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      step(1);
    }
  }

  function onTouchStart(event) {
    if (!event.touches || event.touches.length !== 1) return;
    touchActive = true;
    touchStartX = event.touches[0].clientX;
    touchStartY = event.touches[0].clientY;
  }

  function onTouchEnd(event) {
    if (!touchActive || !event.changedTouches || !event.changedTouches.length) {
      touchActive = false;
      return;
    }
    touchActive = false;
    if (images.length < 2) return;

    var dx = event.changedTouches[0].clientX - touchStartX;
    var dy = event.changedTouches[0].clientY - touchStartY;
    if (Math.abs(dx) < 48 || Math.abs(dx) < Math.abs(dy)) return;
    step(dx < 0 ? 1 : -1);
  }

  collectImages();

  thumbs.forEach(function (btn, index) {
    btn.addEventListener("click", function () {
      activeIndex = index;
      syncPageThumbs(index);
      setMain(btn.getAttribute("data-src"), btn.getAttribute("data-alt") || "", true);
    });
  });

  if (zoomBtn) {
    zoomBtn.addEventListener("click", openLightbox);
  }
  if (mainImg) {
    mainImg.addEventListener("click", openLightbox);
    mainImg.style.cursor = "zoom-in";
  }
  if (lightboxClose) {
    lightboxClose.addEventListener("click", closeLightbox);
  }
  if (lightboxPrev) {
    lightboxPrev.addEventListener("click", function () {
      step(-1);
    });
  }
  if (lightboxNext) {
    lightboxNext.addEventListener("click", function () {
      step(1);
    });
  }
  if (lightbox) {
    lightbox.addEventListener("click", function (event) {
      if (event.target === lightbox) closeLightbox();
    });
  }
  if (lightboxStage) {
    lightboxStage.addEventListener("touchstart", onTouchStart, { passive: true });
    lightboxStage.addEventListener("touchend", onTouchEnd, { passive: true });
  }
  document.addEventListener("keydown", onKeydown);

  var picker = root.querySelector("[data-qty-picker]");
  if (picker) {
    var input = picker.querySelector("[data-qty-input]");
    var minus = picker.querySelector("[data-qty-minus]");
    var plus = picker.querySelector("[data-qty-plus]");

    function clampQty() {
      var value = parseInt(input.value, 10);
      if (isNaN(value) || value < 1) value = 1;
      if (value > 999) value = 999;
      input.value = String(value);
    }

    if (minus) {
      minus.addEventListener("click", function () {
        input.stepDown();
        clampQty();
      });
    }
    if (plus) {
      plus.addEventListener("click", function () {
        input.stepUp();
        clampQty();
      });
    }
    if (input) {
      input.addEventListener("change", clampQty);
      input.addEventListener("blur", clampQty);
    }
  }

  var tabs = root.querySelector("[data-product-tabs]");
  if (tabs) {
    var buttons = tabs.querySelectorAll("[data-tab]");
    var panels = tabs.querySelectorAll("[data-tab-panel]");

    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-tab");
        buttons.forEach(function (item) {
          var on = item === btn;
          item.classList.toggle("is-active", on);
          item.setAttribute("aria-selected", on ? "true" : "false");
        });
        panels.forEach(function (panel) {
          var on = panel.getAttribute("data-tab-panel") === id;
          panel.classList.toggle("is-active", on);
          if (on) {
            panel.removeAttribute("hidden");
          } else {
            panel.setAttribute("hidden", "");
          }
        });
      });
    });
  }
})();
