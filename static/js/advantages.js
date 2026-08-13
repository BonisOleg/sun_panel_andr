(function () {
  "use strict";

  var section = document.querySelector(".advantages-section");
  if (!section) return;

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");

  function reveal() {
    section.classList.add("is-visible");
    var cards = section.querySelectorAll(".advantage-card");
    var maxStagger = 1;
    cards.forEach(function (card) {
      var value = parseInt(card.style.getPropertyValue("--stagger"), 10);
      if (value > maxStagger) maxStagger = value;
    });
    window.setTimeout(function () {
      cards.forEach(function (card) {
        card.classList.add("is-settled");
      });
    }, maxStagger * 100 + 550);
  }

  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            reveal();
            io.disconnect();
          }
        });
      },
      { threshold: 0.2, rootMargin: "0px 0px -8% 0px" }
    );
    io.observe(section);
  } else {
    reveal();
  }

  function onMove(event) {
    if (reduceMotion.matches || !finePointer.matches) return;
    var card = event.currentTarget;
    var rect = card.getBoundingClientRect();
    card.style.setProperty("--mouse-x", event.clientX - rect.left + "px");
    card.style.setProperty("--mouse-y", event.clientY - rect.top + "px");
  }

  function bindSpotlight() {
    var cards = section.querySelectorAll(".advantage-card");
    cards.forEach(function (card) {
      card.removeEventListener("mousemove", onMove);
      if (reduceMotion.matches || !finePointer.matches) return;
      card.addEventListener("mousemove", onMove);
    });
  }

  bindSpotlight();

  if (typeof reduceMotion.addEventListener === "function") {
    reduceMotion.addEventListener("change", bindSpotlight);
  } else if (typeof reduceMotion.addListener === "function") {
    reduceMotion.addListener(bindSpotlight);
  }

  if (typeof finePointer.addEventListener === "function") {
    finePointer.addEventListener("change", bindSpotlight);
  } else if (typeof finePointer.addListener === "function") {
    finePointer.addListener(bindSpotlight);
  }
})();
