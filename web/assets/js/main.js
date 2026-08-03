/* ==========================================================================
   ESP32 MicroPython Tutorial — main.js
   ฟังก์ชัน: ธีม dark/light, sidebar mobile, ค้นหา, ปุ่มคัดลอกโค้ด
   ========================================================================== */
(function () {
  "use strict";

  var ROOT = window.ROOT_PREFIX || "";

  /* ------------------------------------------------------------- theme */
  var themeToggle = document.getElementById("theme-toggle");
  var savedTheme = localStorage.getItem("esp32theme") || "dark";

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    if (themeToggle) themeToggle.textContent = theme === "dark" ? "🌙" : "☀️";
  }

  applyTheme(savedTheme);

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      var next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      localStorage.setItem("esp32theme", next);
      applyTheme(next);
    });
  }

  /* ------------------------------------------------------------ sidebar */
  var navToggle = document.getElementById("nav-toggle");
  var sidebar = document.getElementById("sidebar");

  if (navToggle && sidebar) {
    navToggle.addEventListener("click", function () {
      sidebar.classList.toggle("open");
    });
    document.addEventListener("click", function (e) {
      if (sidebar.classList.contains("open") && !sidebar.contains(e.target) && e.target !== navToggle) {
        sidebar.classList.remove("open");
      }
    });
  }

  /* -------------------------------------------------------------- copy */
  window.copyCode = function (btn) {
    var pre = btn.closest(".code-block").querySelector("pre");
    var text = pre.innerText;
    function done() {
      btn.textContent = "คัดลอกแล้ว";
      btn.classList.add("copied");
      setTimeout(function () {
        btn.textContent = "คัดลอก";
        btn.classList.remove("copied");
      }, 1600);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { fallbackCopy(text); done(); });
    } else {
      fallbackCopy(text);
      done();
    }
  };

  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); } catch (e) { /* ignore */ }
    document.body.removeChild(ta);
  }

  /* ------------------------------------------------------------ search */
  var searchInput = document.getElementById("site-search");
  var searchResults = document.getElementById("search-results");

  if (searchInput && searchResults && typeof SEARCH_INDEX !== "undefined") {
    searchInput.addEventListener("input", function () {
      var q = searchInput.value.trim().toLowerCase();
      if (q.length < 1) {
        searchResults.hidden = true;
        return;
      }
      var hits = SEARCH_INDEX
        .map(function (item, idx) {
          var score = 0;
          var hay = (item.t + " " + item.c + " " + item.k).toLowerCase();
          if (hay.indexOf(q) !== -1) score += 10;
          if (item.t.toLowerCase().indexOf(q) !== -1) score += 30;
          var kw = (item.k || "").toLowerCase().split(/[\s,;]+/);
          for (var i = 0; i < kw.length; i++) {
            if (kw[i] && kw[i].indexOf(q) !== -1) score += 5;
          }
          return { item: item, score: score, idx: idx };
        })
        .filter(function (h) { return h.score > 0; })
        .sort(function (a, b) { return b.score - a.score || a.idx - b.idx; })
        .slice(0, 12);

      if (!hits.length) {
        searchResults.innerHTML = '<li><a style="pointer-events:none;color:var(--muted)">ไม่พบผลการค้นหา</a></li>';
        searchResults.hidden = false;
        return;
      }
      searchResults.innerHTML = hits
        .map(function (h) {
          return (
            '<li><a href="' + ROOT + h.item.h + '">' +
            '<span class="sr-title">' + h.item.t + '</span><br>' +
            '<span class="sr-cat">' + h.item.c + "</span></a></li>"
          );
        })
        .join("");
      searchResults.hidden = false;
    });

    document.addEventListener("click", function (e) {
      if (!searchResults.contains(e.target) && e.target !== searchInput) {
        searchResults.hidden = true;
      }
    });
    searchInput.addEventListener("keydown", function (e) {
      if (e.key === "Escape") searchResults.hidden = true;
    });
  }

  /* ------------------------------------------------------- active scroll */
  var currentLink = document.querySelector(".nav-link.active");
  if (currentLink && "scrollIntoView" in currentLink) {
    currentLink.scrollIntoView({ block: "center" });
  }
})();
