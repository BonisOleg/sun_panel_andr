(function () {
  "use strict";

  var NAME_RE = /^[A-Za-zА-Яа-яЁёІіЇїЄєҐґʼ'`’\-\s]+$/u;
  var EMAIL_RE = /^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$/;
  var MESSAGE_MAX = 800;

  function digitsOnly(value) {
    return String(value || "").replace(/\D/g, "");
  }

  function phoneRestFromFull(full) {
    var digits = digitsOnly(full);
    if (digits.indexOf("380") === 0) digits = digits.slice(3);
    else if (digits.charAt(0) === "0") digits = digits.slice(1);
    return digits.slice(0, 9);
  }

  function bindForm(form) {
    if (!form || form.dataset.contactsBound === "1") return;
    form.dataset.contactsBound = "1";

    var nameInput = form.querySelector("#contact-name");
    var phoneRest = form.querySelector("[data-phone-rest]");
    var phoneFull = form.querySelector("[data-phone-full]");
    var emailInput = form.querySelector("#contact-email");
    var messageInput = form.querySelector("#contact-message");
    if (!nameInput || !phoneRest || !phoneFull || !messageInput) return;

    function syncPhoneFull() {
      var rest = digitsOnly(phoneRest.value).slice(0, 9);
      if (phoneRest.value !== rest) phoneRest.value = rest;
      phoneFull.value = "+380" + rest;
    }

    function setError(fieldKey, message) {
      var wrap = form.querySelector('[data-field="' + fieldKey + '"]');
      var err = form.querySelector('[data-error-for="' + fieldKey + '"]');
      var input =
        fieldKey === "phone"
          ? phoneRest
          : form.querySelector('[name="' + fieldKey + '"]');

      if (wrap) wrap.classList.toggle("is-invalid", Boolean(message));
      if (input) {
        if (message) input.setAttribute("aria-invalid", "true");
        else input.removeAttribute("aria-invalid");
      }
      if (err) {
        err.textContent = message || "";
        err.hidden = !message;
      }
    }

    function validateName(showEmpty) {
      var value = nameInput.value.trim();
      if (!value) {
        if (showEmpty) setError("name", "Вкажіть імʼя");
        else setError("name", "");
        return false;
      }
      if (/\d/.test(value)) {
        setError("name", "Імʼя не може містити цифри — лише літери");
        return false;
      }
      if (!NAME_RE.test(value)) {
        setError(
          "name",
          "Імʼя: лише літери, пробіли, дефіс або апостроф"
        );
        return false;
      }
      setError("name", "");
      return true;
    }

    function validatePhone(showEmpty) {
      syncPhoneFull();
      var rest = digitsOnly(phoneRest.value);
      if (!rest) {
        if (showEmpty) {
          setError("phone", "Вкажіть номер телефону після +380");
        } else {
          setError("phone", "");
        }
        return false;
      }
      if (rest.length < 9) {
        setError(
          "phone",
          "Після +380 має бути рівно 9 цифр (зараз " + rest.length + ")"
        );
        return false;
      }
      if (rest.length > 9) {
        setError("phone", "Забагато цифр — потрібно рівно 9 після +380");
        return false;
      }
      setError("phone", "");
      return true;
    }

    function validateEmail(showEmpty) {
      var value = emailInput ? emailInput.value.trim() : "";
      if (!value) {
        setError("email", "");
        return true;
      }
      if (!EMAIL_RE.test(value)) {
        setError(
          "email",
          "Некоректний email — приклад: name@example.com"
        );
        return false;
      }
      setError("email", "");
      return true;
    }

    function validateMessage(showEmpty) {
      var value = messageInput.value.trim();
      if (!value) {
        if (showEmpty) setError("message", "Вкажіть повідомлення");
        else setError("message", "");
        return false;
      }
      if (value.length > MESSAGE_MAX) {
        setError(
          "message",
          "Максимум " + MESSAGE_MAX + " символів (зараз " + value.length + ")"
        );
        return false;
      }
      setError("message", "");
      return true;
    }

    function validateAll(showEmpty) {
      var okName = validateName(showEmpty);
      var okPhone = validatePhone(showEmpty);
      var okEmail = validateEmail(showEmpty);
      var okMessage = validateMessage(showEmpty);
      return okName && okPhone && okEmail && okMessage;
    }

    phoneRest.value = phoneRestFromFull(phoneFull.value || "+380");
    syncPhoneFull();

    nameInput.addEventListener("input", function () {
      validateName(false);
    });
    nameInput.addEventListener("blur", function () {
      validateName(true);
    });

    phoneRest.addEventListener("input", function () {
      validatePhone(false);
    });
    phoneRest.addEventListener("blur", function () {
      validatePhone(true);
    });

    if (emailInput) {
      emailInput.addEventListener("input", function () {
        validateEmail(false);
      });
      emailInput.addEventListener("blur", function () {
        validateEmail(true);
      });
    }

    messageInput.addEventListener("input", function () {
      validateMessage(false);
    });
    messageInput.addEventListener("blur", function () {
      validateMessage(true);
    });

    function blockIfInvalid(event) {
      syncPhoneFull();
      if (validateAll(true)) return false;
      event.preventDefault();
      if (typeof event.stopPropagation === "function") {
        event.stopPropagation();
      }
      var btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.removeAttribute("disabled");
        btn.classList.remove("htmx-request");
      }
      form.classList.remove("htmx-request");
      var firstInvalid = form.querySelector(
        ".contacts-form__field.is-invalid input, .contacts-form__field.is-invalid textarea"
      );
      if (firstInvalid) firstInvalid.focus();
      return true;
    }

    // capture: до HTMX, щоб не стартував запит і не блокував кнопку
    form.addEventListener(
      "submit",
      function (event) {
        blockIfInvalid(event);
      },
      true
    );

    form.addEventListener("htmx:beforeRequest", function (event) {
      blockIfInvalid(event);
    });
  }

  function init(root) {
    var scope = root && root.querySelectorAll ? root : document;
    if (scope.matches && scope.matches("[data-contacts-form]")) {
      bindForm(scope);
    }
    scope.querySelectorAll("[data-contacts-form]").forEach(bindForm);
  }

  document.addEventListener("DOMContentLoaded", function () {
    init(document);
  });

  document.body.addEventListener("htmx:afterSwap", function (event) {
    init(event.target);
  });
})();
