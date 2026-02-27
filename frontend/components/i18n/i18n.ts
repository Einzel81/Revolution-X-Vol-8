export type Lang = "en" | "ar" | "fr";

type Dict = Record<string, string>;

// IMPORTANT: Keep this file ASCII-only to avoid non-UTF8 build issues in some environments.
// Arabic/French are stored as unicode escapes.
export const dictionaries: Record<Lang, Dict> = {
  en: {
    "dashboard.title": "Dashboard",
    "app.tagline": "Advanced Trading System",
    "user.label": "User",
    "user.status": "Connected",
    "lang": "Language",

    "nav.overview": "Overview",
    "nav.charts": "Charts",
    "nav.scanner": "Scanner",
    "nav.positions": "Positions",
    "nav.execution": "Execution",
    "nav.dxy": "DXY Guardian",
    "nav.ai": "AI",
    "nav.settings": "Settings",
    "nav.logout": "Logout",
    "nav.mt5": "MT5",
  },
  ar: {
    "dashboard.title": "\u0644\u0648\u062d\u0629 \u0627\u0644\u062a\u062d\u0643\u0645",
    "app.tagline": "\u0646\u0638\u0627\u0645 \u0627\u0644\u062a\u062f\u0627\u0648\u0644 \u0627\u0644\u0645\u062a\u0642\u062f\u0645",
    "user.label": "\u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645",
    "user.status": "\u0645\u062a\u0635\u0644",
    "lang": "\u0627\u0644\u0644\u063a\u0629",

    "nav.overview": "\u0627\u0644\u0631\u0626\u064a\u0633\u064a\u0629",
    "nav.charts": "\u0627\u0644\u0631\u0633\u0648\u0645 \u0627\u0644\u0628\u064a\u0627\u0646\u064a\u0629",
    "nav.scanner": "\u0627\u0644\u0641\u0631\u0635",
    "nav.positions": "\u0627\u0644\u0645\u0631\u0627\u0643\u0632",
    "nav.execution": "\u0627\u0644\u062a\u0646\u0641\u064a\u0630",
    "nav.dxy": "\u062d\u0627\u0631\u0633 DXY",
    "nav.ai": "\u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a",
    "nav.settings": "\u0627\u0644\u0625\u0639\u062f\u0627\u062f\u0627\u062a",
    "nav.logout": "\u062a\u0633\u062c\u064a\u0644 \u0627\u0644\u062e\u0631\u0648\u062c",
    "nav.mt5": "\u0627\u062a\u0635\u0627\u0644 MT5",
  },
  fr: {
    "dashboard.title": "Tableau de bord",
    "app.tagline": "Systeme de trading avance",
    "user.label": "Utilisateur",
    "user.status": "Connecte",
    "lang": "Langue",

    "nav.overview": "Apercu",
    "nav.charts": "Graphiques",
    "nav.scanner": "Scanner",
    "nav.positions": "Positions",
    "nav.execution": "Execution",
    "nav.dxy": "Gardien DXY",
    "nav.ai": "IA",
    "nav.settings": "Parametres",
    "nav.logout": "Deconnexion",
    "nav.mt5": "MT5",
  },
};

export function t(lang: Lang, key: string): string {
  const d = dictionaries[lang] || dictionaries.en;
  return d[key] || dictionaries.en[key] || key;
}

export function dirFor(lang: Lang): "ltr" | "rtl" {
  return lang === "ar" ? "rtl" : "ltr";
}