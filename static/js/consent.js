/* Згода на cookie: Consent Mode denied за замовчуванням, GTM лише після «Прийняти всі». */
(function () {
  var STORAGE_KEY = "soliron_consent";
  var DISMISS_KEY = "soliron_consent_dismissed";
  var MAX_AGE_SECONDS = 60 * 60 * 24 * 365; /* 12 місяців */
  var GTM_ID = "GTM-MDSC9NQL";
  var GRANTED = "granted";
  var DENIED = "denied";

  var gtmInjected = false;

  window.dataLayer = window.dataLayer || [];
  window.gtag = function gtag() {
    window.dataLayer.push(arguments);
  };

  window.gtag("consent", "default", {
    ad_storage: "denied",
    analytics_storage: "denied",
    ad_user_data: "denied",
    ad_personalization: "denied",
    security_storage: "granted",
    functionality_storage: "granted",
    wait_for_update: 500,
  });

  function readCookie() {
    var parts = document.cookie ? document.cookie.split("; ") : [];
    var prefix = STORAGE_KEY + "=";
    var i;
    for (i = 0; i < parts.length; i += 1) {
      if (parts[i].indexOf(prefix) === 0) {
        try {
          return decodeURIComponent(parts[i].slice(prefix.length));
        } catch (err) {
          return "";
        }
      }
    }
    return "";
  }

  function readStored() {
    var fromStorage = "";
    try {
      fromStorage = window.localStorage.getItem(STORAGE_KEY) || "";
    } catch (err) {
      fromStorage = "";
    }
    if (fromStorage === GRANTED || fromStorage === DENIED) {
      return fromStorage;
    }
    var fromCookie = readCookie();
    if (fromCookie === GRANTED || fromCookie === DENIED) {
      return fromCookie;
    }
    return "";
  }

  function persist(value) {
    try {
      window.localStorage.setItem(STORAGE_KEY, value);
    } catch (err) {
      /* Safari private mode */
    }
    var secure = window.location.protocol === "https:" ? "; Secure" : "";
    document.cookie =
      STORAGE_KEY +
      "=" +
      encodeURIComponent(value) +
      "; Path=/; Max-Age=" +
      String(MAX_AGE_SECONDS) +
      "; SameSite=Lax" +
      secure;
  }

  function clearDismiss() {
    try {
      window.sessionStorage.removeItem(DISMISS_KEY);
    } catch (err) {
      /* ignore */
    }
  }

  function grantConsent() {
    window.gtag("consent", "update", {
      ad_storage: "granted",
      analytics_storage: "granted",
      ad_user_data: "granted",
      ad_personalization: "granted",
    });
  }

  function denyConsent() {
    window.gtag("consent", "update", {
      ad_storage: "denied",
      analytics_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied",
    });
  }

  function notifyClarity(done) {
    var tries = 0;
    function tick() {
      if (typeof window.clarity === "function") {
        window.clarity("consent");
        if (done) done();
        return;
      }
      tries += 1;
      if (tries >= 24) {
        if (done) done();
        return;
      }
      window.setTimeout(tick, 250);
    }
    tick();
  }

  function loadGtm() {
    if (gtmInjected) {
      notifyClarity();
      return;
    }
    gtmInjected = true;
    window.dataLayer.push({
      "gtm.start": new Date().getTime(),
      event: "gtm.js",
    });
    var script = document.createElement("script");
    script.async = true;
    script.src = "https://www.googletagmanager.com/gtm.js?id=" + GTM_ID;
    script.addEventListener("load", function () {
      notifyClarity();
    });
    var first = document.getElementsByTagName("script")[0];
    if (first && first.parentNode) {
      first.parentNode.insertBefore(script, first);
    } else if (document.head) {
      document.head.appendChild(script);
    }
  }

  function bannerEl() {
    return document.getElementById("cookie-banner");
  }

  function hideBanner() {
    var banner = bannerEl();
    if (!banner) return;
    banner.hidden = true;
  }

  function showBanner() {
    var banner = bannerEl();
    if (!banner) return;
    banner.hidden = false;
    var firstButton = banner.querySelector("[data-cookie-accept]");
    if (!firstButton) return;
    window.requestAnimationFrame(function () {
      try {
        firstButton.focus({ preventScroll: true });
      } catch (err) {
        firstButton.focus();
      }
    });
  }

  function acceptAll() {
    var previous = readStored();
    persist(GRANTED);
    clearDismiss();
    grantConsent();
    if (previous !== GRANTED) {
      window.dataLayer.push({ event: "consent_granted" });
    }
    hideBanner();
    loadGtm();
  }

  function necessaryOnly() {
    var previous = readStored();
    persist(DENIED);
    clearDismiss();
    denyConsent();
    if (previous === GRANTED) {
      window.location.reload();
      return;
    }
    hideBanner();
  }

  function dismissForSession() {
    try {
      window.sessionStorage.setItem(DISMISS_KEY, "1");
    } catch (err) {
      /* ignore */
    }
    hideBanner();
  }

  function elementFrom(node) {
    if (!node) return null;
    if (node.nodeType === 1) return node;
    return node.parentElement || null;
  }

  document.addEventListener("click", function (event) {
    var el = elementFrom(event.target);
    if (!el || !el.closest) return;
    if (el.closest("[data-cookie-accept]")) {
      event.preventDefault();
      acceptAll();
      return;
    }
    if (el.closest("[data-cookie-necessary]")) {
      event.preventDefault();
      necessaryOnly();
      return;
    }
    if (el.closest("[data-cookie-settings]")) {
      event.preventDefault();
      showBanner();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    var banner = bannerEl();
    if (!banner || banner.hidden) return;
    event.preventDefault();
    dismissForSession();
  });

  if (readStored() === GRANTED) {
    grantConsent();
    loadGtm();
  }

  function bootBanner() {
    if (readStored()) return;
    var dismissed = false;
    try {
      dismissed = window.sessionStorage.getItem(DISMISS_KEY) === "1";
    } catch (err) {
      dismissed = false;
    }
    if (!dismissed) showBanner();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootBanner);
  } else {
    bootBanner();
  }
})();
