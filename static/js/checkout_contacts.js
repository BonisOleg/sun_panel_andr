(function () {
  "use strict";

  var form = document.querySelector("form.checkout-card");
  if (!form) return;

  var nameInput = form.querySelector("#customer-name");
  var phoneRest = form.querySelector("[data-phone-rest]");
  var phoneFull = form.querySelector("[data-phone-full]");
  var emailInput = form.querySelector("#customer-email");
  if (!nameInput || !phoneRest || !phoneFull) return;

  var NAME_RE = /^[A-Za-zА-Яа-яЁёІіЇїЄєҐґʼ'`’\-\s]+$/u;
  var EMAIL_RE = /^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$/;

  function digitsOnly(value) {
    return String(value || "").replace(/\D/g, "");
  }

  function phoneRestFromFull(full) {
    var digits = digitsOnly(full);
    if (digits.indexOf("380") === 0) digits = digits.slice(3);
    else if (digits.charAt(0) === "0") digits = digits.slice(1);
    return digits.slice(0, 9);
  }

  function syncPhoneFull() {
    var rest = digitsOnly(phoneRest.value).slice(0, 9);
    if (phoneRest.value !== rest) phoneRest.value = rest;
    phoneFull.value = "+380" + rest;
  }

  function setError(fieldKey, message) {
    var wrap = form.querySelector('[data-field="' + fieldKey + '"]');
    var err = form.querySelector('[data-error-for="' + fieldKey + '"]');
    var input =
      fieldKey === "customer_phone"
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
      if (showEmpty) setError("customer_name", "Вкажіть ПІБ");
      else setError("customer_name", "");
      return false;
    }
    if (/\d/.test(value)) {
      setError("customer_name", "ПІБ не може містити цифри — лише літери");
      return false;
    }
    if (!NAME_RE.test(value)) {
      setError(
        "customer_name",
        "ПІБ: лише літери, пробіли, дефіс або апостроф"
      );
      return false;
    }
    setError("customer_name", "");
    return true;
  }

  function validatePhone(showEmpty) {
    syncPhoneFull();
    var rest = digitsOnly(phoneRest.value);
    if (!rest) {
      if (showEmpty) {
        setError("customer_phone", "Вкажіть номер телефону після +380");
      } else {
        setError("customer_phone", "");
      }
      return false;
    }
    if (rest.length < 9) {
      setError(
        "customer_phone",
        "Після +380 має бути рівно 9 цифр (зараз " + rest.length + ")"
      );
      return false;
    }
    if (rest.length > 9) {
      setError("customer_phone", "Забагато цифр — потрібно рівно 9 після +380");
      return false;
    }
    setError("customer_phone", "");
    return true;
  }

  function validateEmail(showEmpty) {
    var value = emailInput ? emailInput.value.trim() : "";
    if (!value) {
      setError("customer_email", "");
      return true;
    }
    if (!EMAIL_RE.test(value)) {
      setError(
        "customer_email",
        "Некоректний email — приклад: name@example.com"
      );
      return false;
    }
    setError("customer_email", "");
    return true;
  }

  function validateAll(showEmpty) {
    var okName = validateName(showEmpty);
    var okPhone = validatePhone(showEmpty);
    var okEmail = validateEmail(showEmpty);
    return okName && okPhone && okEmail;
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

  form.addEventListener("submit", function (event) {
    syncPhoneFull();
    if (!validateAll(true)) {
      event.preventDefault();
      var firstInvalid = form.querySelector(".form-field.is-invalid input");
      if (firstInvalid) firstInvalid.focus();
    }
  });
})();
