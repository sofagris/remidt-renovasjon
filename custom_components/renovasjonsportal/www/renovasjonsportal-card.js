const CARD_TAG = "renovasjonsportal-card";
const ICON_BASE = "/renovasjonsportal/icons";

const FRACTION_ICONS = {
  papir: "papir.png",
  matavfall: "matavfall.png",
  restavfall: "restavfall.png",
  "glass og metallemballasje": "glass-og-metallemballasje.png",
  "glass- og metallemballasje": "glass-og-metallemballasje.png",
  plastemballasje: "plastemballasje.png",
};

function normalizeFraction(name) {
  return String(name || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");
}

function iconForFraction(name) {
  const key = normalizeFraction(name);
  const file = FRACTION_ICONS[key];
  return file ? `${ICON_BASE}/${file}` : `${ICON_BASE}/restavfall.png`;
}

function slugForFraction(name) {
  return normalizeFraction(name)
    .replace(/æ/g, "ae")
    .replace(/ø/g, "o")
    .replace(/å/g, "a")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function formatRelativeDays(days) {
  if (days === null || days === undefined || Number.isNaN(Number(days))) {
    return "Ukjent";
  }
  const value = Number(days);
  if (value <= 0) return "I dag";
  if (value === 1) return "I morgen";
  return `Om ${value} dager`;
}

function formatCollectionDate(value) {
  if (!value || value === "unknown" || value === "unavailable") {
    return "";
  }
  const date = new Date(`${value}T12:00:00`);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString("nb-NO", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function findSuggestedEntity(hass, entities) {
  const candidates = entities || Object.keys(hass?.states || {});
  const byAttribute = candidates.find((entityId) => {
    const state = hass?.states?.[entityId];
    return Array.isArray(state?.attributes?.avfallstyper);
  });
  if (byAttribute) {
    return byAttribute;
  }
  return (
    candidates.find(
      (entityId) =>
        entityId.includes("neste_tomming") ||
        entityId.includes("next_collection") ||
        entityId.includes("renovasjonsportal")
    ) || ""
  );
}

class RenovasjonsportalCard extends HTMLElement {
  constructor() {
    super();
    this._config = {};
    this._hass = undefined;
  }

  static getConfigForm() {
    return {
      schema: [
        {
          name: "entity",
          required: true,
          selector: {
            entity: { filter: { domain: "sensor" } },
          },
        },
        { name: "name", selector: { text: {} } },
        {
          name: "show_name",
          selector: { boolean: {} },
        },
      ],
    };
  }

  static getStubConfig(hass, entities) {
    return {
      entity: findSuggestedEntity(hass, entities),
      show_name: true,
    };
  }

  static getCardSize() {
    return 3;
  }

  setConfig(config) {
    if (!config || typeof config !== "object") {
      throw new Error("Ugyldig konfigurasjon for Renovasjonsportal-kortet.");
    }
    this._config = {
      show_name: true,
      ...config,
    };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return RenovasjonsportalCard.getCardSize();
  }

  connectedCallback() {
    this._render();
  }

  _ensureDom() {
    if (this._root) {
      return;
    }

    this.innerHTML = `
      <ha-card>
        <div class="rp-content"></div>
      </ha-card>
      <style>
        renovasjonsportal-card {
          display: block;
        }
        renovasjonsportal-card ha-card {
          overflow: hidden;
        }
        renovasjonsportal-card .rp-content {
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 14px;
        }
        renovasjonsportal-card .rp-header {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        renovasjonsportal-card .rp-title {
          font-size: 0.95rem;
          font-weight: 500;
          color: var(--secondary-text-color);
          line-height: 1.3;
        }
        renovasjonsportal-card .rp-relative {
          font-size: 1.55rem;
          font-weight: 650;
          line-height: 1.2;
          color: var(--primary-text-color);
        }
        renovasjonsportal-card .rp-date {
          font-size: 0.95rem;
          color: var(--secondary-text-color);
          text-transform: capitalize;
        }
        renovasjonsportal-card .rp-fractions {
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
        }
        renovasjonsportal-card .rp-fraction {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 6px;
          min-width: 72px;
          max-width: 96px;
          flex: 1 1 72px;
        }
        renovasjonsportal-card .rp-fraction img {
          width: 56px;
          height: 56px;
          object-fit: contain;
          display: block;
        }
        renovasjonsportal-card .rp-fraction-label {
          font-size: 0.75rem;
          line-height: 1.25;
          text-align: center;
          color: var(--primary-text-color);
          word-break: break-word;
        }
        renovasjonsportal-card .rp-warning {
          color: var(--secondary-text-color);
          font-size: 0.95rem;
        }
      </style>
    `;
    this._root = this.querySelector(".rp-content");
  }

  _render() {
    this._ensureDom();
    if (!this._root) {
      return;
    }

    const entityId = this._config.entity;
    if (!entityId) {
      this._root.innerHTML = `
        <div class="rp-title">Renovasjonsportal</div>
        <div class="rp-warning">Velg sensoren for neste tømming.</div>
      `;
      return;
    }

    const stateObj = this._hass?.states?.[entityId];
    const title =
      this._config.name ||
      stateObj?.attributes?.friendly_name ||
      "Neste tømming";

    if (!stateObj) {
      this._root.innerHTML = `
        <div class="rp-title">${escapeHtml(title)}</div>
        <div class="rp-warning">Finner ikke entity: ${escapeHtml(entityId)}</div>
      `;
      return;
    }

    if (stateObj.state === "unavailable" || stateObj.state === "unknown") {
      this._root.innerHTML = `
        ${this._config.show_name !== false ? `<div class="rp-title">${escapeHtml(title)}</div>` : ""}
        <div class="rp-warning">Ingen tømmedata tilgjengelig</div>
      `;
      return;
    }

    const days = stateObj.attributes.dager_til;
    const fractions = Array.isArray(stateObj.attributes.avfallstyper)
      ? stateObj.attributes.avfallstyper
      : [];
    const relative = formatRelativeDays(days);
    const dateLabel = formatCollectionDate(stateObj.state);

    const fractionHtml =
      fractions.length > 0
        ? fractions
            .map((fraction) => {
              const mapped = iconForFraction(fraction);
              const fallback = `${ICON_BASE}/${slugForFraction(fraction)}.png`;
              const src = mapped || fallback;
              const label = escapeHtml(fraction);
              return `
                <div class="rp-fraction">
                  <img src="${src}" alt="${label}" loading="lazy" />
                  <span class="rp-fraction-label">${label}</span>
                </div>
              `;
            })
            .join("")
        : `<div class="rp-warning">Ingen avfallstyper oppgitt</div>`;

    this._root.innerHTML = `
      <div class="rp-header">
        ${this._config.show_name !== false ? `<div class="rp-title">${escapeHtml(title)}</div>` : ""}
        <div class="rp-relative">${escapeHtml(relative)}</div>
        ${dateLabel ? `<div class="rp-date">${escapeHtml(dateLabel)}</div>` : ""}
      </div>
      <div class="rp-fractions">${fractionHtml}</div>
    `;
  }
}

window.customCards = window.customCards || [];

function registerCard() {
  if (!window.customElements.get(CARD_TAG)) {
    window.customElements.define(CARD_TAG, RenovasjonsportalCard);
  }

  if (!window.customCards.some((card) => card.type === CARD_TAG)) {
    window.customCards.push({
      type: CARD_TAG,
      name: "Renovasjonsportal",
      description: "Viser neste søppeltømming med avfallsikoner.",
      preview: true,
      documentationURL: "https://github.com/sofagris/remidt-renovasjon",
    });
  }
}

registerCard();
