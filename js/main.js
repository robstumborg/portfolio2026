(function () {
  // ── config ──────────────────────────────────────────────
  const SUPPORTED_LANGS = ["en", "es"];

  const I18N_BINDINGS = [
    { attr: "data-i18n", apply: (el, val) => (el.textContent = val) },
    { attr: "data-i18n-html", apply: (el, val) => (el.innerHTML = val) },
    { attr: "data-i18n-title", apply: (el, val) => (el.title = val) },
    {
      attr: "data-i18n-featured",
      apply: (el, val) => el.setAttribute("data-featured-label", val),
    },
  ];

  // ── dom refs ────────────────────────────────────────────
  const html = document.documentElement;
  const themeToggle = document.querySelector(".theme-toggle");
  const langToggle = document.querySelector(".lang-toggle");
  const themeButtons = {
    light: document.getElementById("btn-light"),
    dark: document.getElementById("btn-dark"),
  };
  const langButtons = {
    en: document.getElementById("btn-en"),
    es: document.getElementById("btn-es"),
  };

  // ── theme ───────────────────────────────────────────────
  function setTheme(theme) {
    html.setAttribute("data-theme", theme);
    themeButtons.light.classList.toggle("active", theme === "light");
    themeButtons.dark.classList.toggle("active", theme === "dark");
    localStorage.setItem("theme", theme);
  }

  function toggleTheme() {
    const current = html.getAttribute("data-theme");
    setTheme(current === "dark" ? "light" : "dark");
  }

  // ── scroll-based nav active state ───────────────────────
  function initNavObserver() {
    const sections = document.querySelectorAll("section[id]");
    const navLinks = document.querySelectorAll(".nav-links a");

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const id = entry.target.id;
            navLinks.forEach((link) => {
              link.classList.toggle(
                "active",
                link.getAttribute("href") === "#" + id,
              );
            });
          }
        });
      },
      { rootMargin: "-40% 0px -50% 0px" },
    );

    sections.forEach((section) => observer.observe(section));
  }

  // ── fade-in on scroll ───────────────────────────────────
  function initFadeObserver() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    });

    document.querySelectorAll(".fade-in").forEach((el) => observer.observe(el));
  }

  // ── i18n ────────────────────────────────────────────────
  const localeCache = {};
  let currentLang = "en";

  async function loadLocale(lang) {
    if (localeCache[lang]) return localeCache[lang];

    const resp = await fetch(`locales/${lang}.json`);
    if (!resp.ok) throw new Error(`failed to load locale: ${lang}`);

    const strings = await resp.json();
    localeCache[lang] = strings;
    return strings;
  }

  function applyLocale(strings) {
    // apply all data-i18n-* bindings
    I18N_BINDINGS.forEach(({ attr, apply }) => {
      document.querySelectorAll(`[${attr}]`).forEach((el) => {
        const val = strings[el.getAttribute(attr)];
        if (val !== undefined) apply(el, val);
      });
    });

    // page title and lang attribute
    if (strings["meta.title"]) document.title = strings["meta.title"];
    html.setAttribute("lang", currentLang);
  }

  function updateLangButtons() {
    langButtons.en.classList.toggle("active", currentLang === "en");
    langButtons.es.classList.toggle("active", currentLang === "es");
  }

  async function setLang(lang) {
    currentLang = lang;
    localStorage.setItem("lang", lang);
    updateLangButtons();
    try {
      const strings = await loadLocale(lang);
      applyLocale(strings);
    } catch (err) {
      console.error("i18n: failed to apply locale", err);
    }
  }

  function detectLang() {
    // check localstorage first
    const saved = localStorage.getItem("lang");
    if (saved && SUPPORTED_LANGS.includes(saved)) return saved;

    // then browser language
    if (navigator.language.toLowerCase().startsWith("es")) return "es";

    // default
    return "en";
  }

  // ── init ────────────────────────────────────────────────
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme) setTheme(savedTheme);

  themeToggle.addEventListener("click", toggleTheme);
  langToggle.addEventListener("click", () =>
    setLang(currentLang === "en" ? "es" : "en"),
  );

  initNavObserver();
  initFadeObserver();
  setLang(detectLang());
})();
