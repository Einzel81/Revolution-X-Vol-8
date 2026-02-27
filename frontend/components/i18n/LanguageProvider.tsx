"use client";

import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { Lang } from "./i18n";
import { dirFor, t as translate } from "./i18n";

type Ctx = {
  lang: Lang;
  dir: "ltr" | "rtl";
  setLang: (l: Lang) => void;
  t: (key: string) => string;
  cycleLang: () => void;
};

const LanguageContext = createContext<Ctx | null>(null);

const STORAGE_KEY = "rx_lang";

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");

  useEffect(() => {
    const saved = (typeof window !== "undefined" && window.localStorage.getItem(STORAGE_KEY)) || "";
    if (saved === "en" || saved === "ar" || saved === "fr") setLangState(saved);
  }, []);

  const setLang = (l: Lang) => {
    setLangState(l);
    if (typeof window !== "undefined") window.localStorage.setItem(STORAGE_KEY, l);
  };

  const dir = useMemo(() => dirFor(lang), [lang]);

  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.lang = lang;
      document.documentElement.dir = dir;
    }
  }, [lang, dir]);

  const t = (key: string) => translate(lang, key);

  const cycleLang = () => {
    setLang(lang === "en" ? "ar" : lang === "ar" ? "fr" : "en");
  };

  const value: Ctx = { lang, dir, setLang, t, cycleLang };

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider");
  return ctx;
}