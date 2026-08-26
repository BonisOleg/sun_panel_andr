(function () {
  const header = document.querySelector("[data-site-header]");
  const toggle = document.querySelector("[data-nav-toggle]");
  const searchToggle = document.querySelector("[data-search-toggle]");
  const searchRoot = document.querySelector("[data-header-search]");
  const searchInput = searchRoot
    ? searchRoot.querySelector(".header-search__input")
    : null;
  const mobileMq = window.matchMedia("(max-width: 1023px)");
  const reduceMotionMq = window.matchMedia("(prefers-reduced-motion: reduce)");
  const NAV_ANIM_MS = 480;
  let navScrollY = 0;
  let navScrollLocked = false;
  let navCloseTimer = 0;

  function isMobile() {
    return mobileMq.matches;
  }

  function lockBodyScroll() {
    if (navScrollLocked) return;
    navScrollY = window.scrollY || window.pageYOffset || 0;
    navScrollLocked = true;
    document.documentElement.classList.add("is-nav-locked");
    /* iOS Safari: overflow:hidden alone jumps sticky header off-screen when scrolled.
       Freeze body at the current offset so the viewport stays put. */
    document.body.style.overflowY = "hidden";
    document.body.style.position = "fixed";
    document.body.style.top = "-" + navScrollY + "px";
    document.body.style.left = "0";
    document.body.style.right = "0";
    document.body.style.width = "100%";
  }

  function unlockBodyScroll() {
    if (!navScrollLocked) return;
    const y = navScrollY;
    navScrollLocked = false;
    document.documentElement.classList.remove("is-nav-locked");
    document.body.style.overflowY = "";
    document.body.style.position = "";
    document.body.style.top = "";
    document.body.style.left = "";
    document.body.style.right = "";
    document.body.style.width = "";
    /* html { scroll-behavior: smooth } can drop or delay restore after position:fixed */
    const html = document.documentElement;
    const prevBehavior = html.style.scrollBehavior;
    html.style.scrollBehavior = "auto";
    window.scrollTo(0, y);
    html.style.scrollBehavior = prevBehavior;
  }

  if (header) {
    function syncScroll() {
      if (navScrollLocked) return;
      header.classList.toggle("is-scrolled", window.scrollY > 8);
    }
    syncScroll();
    window.addEventListener("scroll", syncScroll, { passive: true });
  }

  function setNavOpen(open) {
    if (!header || !toggle) return;
    if (navCloseTimer) {
      window.clearTimeout(navCloseTimer);
      navCloseTimer = 0;
    }

    if (open) {
      /* Lock first while sticky header is still in place, then pin header fixed. */
      lockBodyScroll();
      if (navScrollY > 8) {
        header.classList.add("is-scrolled");
      }
      header.classList.add("is-open");
      toggle.setAttribute("aria-expanded", "true");

      if (reduceMotionMq.matches) {
        header.classList.add("is-nav-shown");
        return;
      }

      /*
        Sticky→fixed on the same frame as the open styles can skip CSS transitions.
        Paint the closed menu first, then flip is-nav-shown on the next frame.
      */
      header.classList.remove("is-nav-shown");
      void header.offsetWidth;
      window.requestAnimationFrame(function () {
        header.classList.add("is-nav-shown");
      });
    } else {
      header.classList.remove("is-nav-shown");
      toggle.setAttribute("aria-expanded", "false");
      const delay = reduceMotionMq.matches ? 0 : NAV_ANIM_MS;
      navCloseTimer = window.setTimeout(function () {
        navCloseTimer = 0;
        header.classList.remove("is-open");
        unlockBodyScroll();
      }, delay);
    }
  }

  function clearHeaderSearchResults() {
    window.dispatchEvent(new Event("header-search:clear"));
  }

  function setSearchOpen(open) {
    if (!header || !searchToggle) return;
    header.classList.toggle("is-search-open", open);
    searchToggle.setAttribute("aria-expanded", open ? "true" : "false");
    searchToggle.setAttribute(
      "aria-label",
      open ? "Закрити пошук" : "Відкрити пошук"
    );
    if (open && searchInput) {
      window.setTimeout(function () {
        searchInput.focus();
      }, 10);
    } else {
      clearHeaderSearchResults();
    }
  }

  if (header && toggle) {
    toggle.addEventListener("click", function () {
      const next = !header.classList.contains("is-nav-shown");
      if (next) setSearchOpen(false);
      setNavOpen(next);
    });

    header.querySelectorAll(".site-nav a, .site-nav button").forEach(function (el) {
      el.addEventListener("click", function () {
        if (isMobile()) setNavOpen(false);
      });
    });
  }

  if (header && searchToggle && searchRoot) {
    searchToggle.addEventListener("click", function () {
      if (!isMobile()) return;
      const next = !header.classList.contains("is-search-open");
      if (next) setNavOpen(false);
      setSearchOpen(next);
    });

    document.addEventListener(
      "pointerdown",
      function (event) {
        if (!isMobile() || !header.classList.contains("is-search-open")) return;
        const t = event.target;
        if (searchRoot.contains(t) || searchToggle.contains(t)) return;
        setSearchOpen(false);
      },
      true
    );

    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") return;
      if (!header.classList.contains("is-search-open")) return;
      setSearchOpen(false);
      searchToggle.focus();
    });
  }

  window.addEventListener("resize", function () {
    if (!isMobile()) {
      setNavOpen(false);
      setSearchOpen(false);
    }
  });

  document.addEventListener("click", function (event) {
    const btn = event.target.closest("[data-filter-btn]");
    if (!btn) return;
    const group = btn.closest(".category-filters, .filter-tabs");
    if (!group) return;
    group.querySelectorAll("[data-filter-btn]").forEach(function (el) {
      el.classList.toggle("is-active", el === btn);
      el.classList.toggle("active", el === btn);
    });
  });

  initHeroTilt();

  function initHeroTilt() {
    const card = document.querySelector("[data-hero-tilt]");
    if (!card) return;

    const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

    function canTilt() {
      return finePointer.matches && !reduceMotion.matches;
    }

    function reset() {
      card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)";
    }

    card.addEventListener("mousemove", function (e) {
      if (!canTilt()) return;
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      card.style.transform =
        "perspective(1000px) rotateX(" +
        -y / 25 +
        "deg) rotateY(" +
        x / 25 +
        "deg) scale3d(1.01, 1.01, 1.01)";
    });

    card.addEventListener("mouseleave", function () {
      reset();
    });

    function onCapabilityChange() {
      if (!canTilt()) reset();
    }

    if (finePointer.addEventListener) {
      finePointer.addEventListener("change", onCapabilityChange);
      reduceMotion.addEventListener("change", onCapabilityChange);
    } else if (finePointer.addListener) {
      finePointer.addListener(onCapabilityChange);
      reduceMotion.addListener(onCapabilityChange);
    }
  }
})();
