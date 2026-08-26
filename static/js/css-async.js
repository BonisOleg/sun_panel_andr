(function () {
  function activate(link) {
    if (!link || link.media === "all") return;
    link.media = "all";
    link.removeAttribute("data-async-css");
  }

  function boot() {
    document.querySelectorAll("link[data-async-css]").forEach(function (link) {
      if (link.sheet) {
        activate(link);
        return;
      }
      link.addEventListener("load", function () {
        activate(link);
      });
      // Safari / cached: load may have fired before listener
      requestAnimationFrame(function () {
        if (link.sheet) activate(link);
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
