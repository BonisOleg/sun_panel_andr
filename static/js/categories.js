(function () {
  "use strict";

  var section = document.querySelector(".categories-section");
  if (!section) return;

  var layers = section.querySelectorAll(".categories-clouds__layer[data-parallax]");
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var narrowQuery = window.matchMedia("(max-width: 768px)");
  var ticking = false;
  var parallaxBound = false;

  function reveal() {
    section.classList.add("is-visible");
  }

  function clearParallax() {
    layers.forEach(function (layer) {
      layer.style.removeProperty("--cloud-shift");
    });
  }

  function parallaxAmplitude() {
    /* Slightly softer shift on narrow viewports for iOS Safari stability */
    return narrowQuery.matches ? 44 : 56;
  }

  function updateParallax() {
    ticking = false;
    if (reduceMotion.matches || !section.classList.contains("is-visible")) {
      clearParallax();
      return;
    }

    var rect = section.getBoundingClientRect();
    var viewH = window.innerHeight || document.documentElement.clientHeight;
    var total = rect.height + viewH;
    if (total <= 0) return;

    var progress = (viewH - rect.top) / total;
    progress = Math.max(0, Math.min(1, progress));
    var shift = (progress - 0.5) * 2;
    var amplitude = parallaxAmplitude();

    layers.forEach(function (layer) {
      var speed = parseFloat(layer.getAttribute("data-parallax")) || 0.2;
      var y = Math.round(shift * speed * -amplitude);
      layer.style.setProperty("--cloud-shift", y + "px");
    });
  }

  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(updateParallax);
  }

  function bindParallax() {
    if (parallaxBound) {
      window.removeEventListener("scroll", onScroll, { passive: true });
      window.removeEventListener("resize", onScroll);
      parallaxBound = false;
    }

    if (reduceMotion.matches) {
      clearParallax();
      return;
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    parallaxBound = true;
    updateParallax();
  }

  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            reveal();
            bindParallax();
            io.disconnect();
          }
        });
      },
      { threshold: 0.18, rootMargin: "0px 0px -6% 0px" }
    );
    io.observe(section);
  } else {
    reveal();
    bindParallax();
  }

  function onModeChange() {
    bindParallax();
  }

  if (typeof reduceMotion.addEventListener === "function") {
    reduceMotion.addEventListener("change", onModeChange);
  } else if (typeof reduceMotion.addListener === "function") {
    reduceMotion.addListener(onModeChange);
  }

  if (typeof narrowQuery.addEventListener === "function") {
    narrowQuery.addEventListener("change", onModeChange);
  } else if (typeof narrowQuery.addListener === "function") {
    narrowQuery.addListener(onModeChange);
  }
})();
