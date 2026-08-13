/* TinyMCE upload handler for Soliron admin (django-tinymce + Unfold). */
(function () {
  "use strict";

  function csrfToken() {
    var match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  window.appTinyMceUploadHandler = function (blobInfo, progress) {
    return new Promise(function (resolve, reject) {
      var xhr = new XMLHttpRequest();
      xhr.open("POST", "/api/content/tinymce-upload/");
      xhr.withCredentials = true;
      var token = csrfToken();
      if (token) {
        xhr.setRequestHeader("X-CSRFToken", token);
      }
      xhr.upload.onprogress = function (e) {
        if (e.lengthComputable && typeof progress === "function") {
          progress((e.loaded / e.total) * 100);
        }
      };
      xhr.onload = function () {
        if (xhr.status < 200 || xhr.status >= 300) {
          reject("HTTP Error: " + xhr.status);
          return;
        }
        var json;
        try {
          json = JSON.parse(xhr.responseText);
        } catch (err) {
          reject("Invalid JSON");
          return;
        }
        if (!json || typeof json.location !== "string") {
          reject((json && json.error) || "Invalid JSON");
          return;
        }
        resolve(json.location);
      };
      xhr.onerror = function () {
        reject("Image upload failed");
      };
      var formData = new FormData();
      formData.append("file", blobInfo.blob(), blobInfo.filename());
      xhr.send(formData);
    });
  };
})();
