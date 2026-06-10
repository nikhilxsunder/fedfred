function updateGtagConsent() {
  const granted = CookieConsent.acceptedCategory("analytics");
  gtag("consent", "update", {
    analytics_storage: granted ? "granted" : "denied",
  });
}

CookieConsent.run({
  guiOptions: {
    consentModal: { layout: "box", position: "bottom right" },
    preferencesModal: { layout: "bar", position: "right" }, // PyTorch-style side panel
  },
  categories: {
    necessary: { enabled: true, readOnly: true },
    analytics: {},
  },
  onConsent: updateGtagConsent,
  onChange: updateGtagConsent,
  language: {
    default: "en",
    translations: {
      en: {
        consentModal: {
          title: "Cookies on fedfred docs",
          description:
            "We use Google Analytics to understand how the documentation is used. No advertising, no data sales.",
          acceptAllBtn: "Accept",
          acceptNecessaryBtn: "Decline",
          showPreferencesBtn: "Manage preferences",
        },
        preferencesModal: {
          title: "Storage preferences",
          acceptAllBtn: "Accept all",
          acceptNecessaryBtn: "Decline all",
          savePreferencesBtn: "Save",
          sections: [
            {
              title: "Essential",
              description:
                "Required for basic site functionality (e.g. remembering this choice and your light/dark theme).",
              linkedCategory: "necessary",
            },
            {
              title: "Analytics",
              description:
                "Google Analytics — anonymous usage statistics that help prioritize documentation improvements.",
              linkedCategory: "analytics",
            },
          ],
        },
      },
    },
  },
});

// Floating cookie button (bottom-right) to reopen preferences
const btn = document.createElement("button");
btn.id = "cc-float-btn";
btn.setAttribute("aria-label", "Cookie preferences");
btn.innerHTML = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22"
     fill="none" stroke="currentColor" stroke-width="2"
     stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M12 2a10 10 0 1 0 10 10 4 4 0 0 1-5-5 4 4 0 0 1-5-5"/>
  <path d="M8.5 8.5v.01"/><path d="M16 15.5v.01"/><path d="M12 12v.01"/>
  <path d="M11 17v.01"/><path d="M7 14v.01"/>
</svg>`;
btn.onclick = () => CookieConsent.showPreferences();
document.body.appendChild(btn);

function syncCcTheme() {
  document.documentElement.classList.toggle(
    "cc--darkmode",
    document.documentElement.dataset.theme === "dark",
  );
}
syncCcTheme();
new MutationObserver(syncCcTheme).observe(document.documentElement, {
  attributes: true,
  attributeFilter: ["data-theme"],
});
