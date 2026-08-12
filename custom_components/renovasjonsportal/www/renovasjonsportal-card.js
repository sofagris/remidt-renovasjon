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
  return file ? `${ICON_BASE}/${file}` : null;
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

class RenovasjonsportalCard extends HTMLElement {
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
    const match = (entities || []).find((entityId) => {
      const state = hass?.states?.[entityId];
      return (
        state &&
        Object.prototype.hasOwnProperty.call(state.attributes || {}, "avfallstyper")
      );
    });
    return {
      entity: match || "",
      show_name: true,
    };
  }

  static getCardSize() {
    return 3;
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("Du må velge en entity for Renovasjonsportal-kortet.");
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

  _render() {
    if (!this._config) {
      return;
    }

    if (!this._card) {
      this.innerHTML = `
        <ha-card>
          <div class="rp-content"></div>
        </ha-card>
        <style>
          :host {
            display: block;
          }
          ha-card {
            overflow: hidden;
          }
          .rp-content {
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 14px;
          }
          .rp-header {
            display: flex;
            flex-direction: column;
            gap: 2px;
          }
          .rp-title {
            font-size: 0.95rem;
            font-weight: 500;
            color: var(--secondary-text-color);
            line-height: 1.3;
          }
          .rp-relative {
            font-size: 1.55rem;
            font-weight: 650;
            line-height: 1.2;
            color: var(--primary-text-color);
          }
          .rp-date {
            font-size: 0.95rem;
            color: var(--secondary-text-color);
            text-transform: capitalize;
          }
          .rp-fractions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
          }
          .rp-fraction {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            min-width: 72px;
            max-width: 96px;
            flex: 1 1 72px;
          }
          .rp-fraction img {
            width: 56px;
            height: 56px;
            object-fit: contain;
            display: block;
          }
          .rp-fraction-label {
            font-size: 0.75rem;
            line-height: 1.25;
            text-align: center;
            color: var(--primary-text-color);
            word-break: break-word;
          }
          .rp-warning {
            color: var(--warning-color, var(--error-color));
            font-size: 0.95rem;
          }
        </style>
      `;
      this._card = this.querySelector("ha-card");
      this._root = this.querySelector(".rp-content");
    }

    const entityId = this._config.entity;
    const stateObj = this._hass?.states?.[entityId];
    const title =
      this._config.name ||
      stateObj?.attributes?.friendly_name ||
      "Neste tømming";

    if (!stateObj) {
      this._root.innerHTML = `
        <div class="rp-warning">Finner ikke entity: ${this._escape(entityId)}</div>
      `;
      return;
    }

    if (stateObj.state === "unavailable" || stateObj.state === "unknown") {
      this._root.innerHTML = `
        ${this._config.show_name !== false ? `<div class="rp-title">${this._escape(title)}</div>` : ""}
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
              const icon = iconForFraction(fraction);
              const label = this._escape(fraction);
              const image = icon
                ? `<img src="${icon}" alt="${label}" loading="lazy" />`
                : `<img src="${ICON_BASE}/restavfall.png" alt="${label}" loading="lazy" />`;
              return `
                <div class="rp-fraction">
                  ${image}
                  <span class="rp-fraction-label">${label}</span>
                </div>
              `;
            })
            .join("")
        : `<div class="rp-warning">Ingen avfallstyper oppgitt</div>`;

    this._root.innerHTML = `
      <div class="rp-header">
        ${this._config.show_name !== false ? `<div class="rp-title">${this._escape(title)}</div>` : ""}
        <div class="rp-relative">${this._escape(relative)}</div>
        ${dateLabel ? `<div class="rp-date">${this._escape(dateLabel)}</div>` : ""}
      </div>
      <div class="rp-fractions">${fractionHtml}</div>
    `;
  }

  _escape(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }
}

if (!customElements.get("renovasjonsportal-card")) {
  customElements.define("renovasjonsportal-card", RenovasjonsportalCard);
}

window.customCards = window.customCards || [];
if (
  !window.customCards.some((card) => card.type === "renovasjonsportal-card")
) {
  window.customCards.push({
    type: "renovasjonsportal-card",
    name: "Renovasjonsportal",
    description: "Viser neste søppeltømming med avfallsikoner.",
    preview: true,
    documentationURL: "https://github.com/sofagris/ha-renovasjonsportal",
  });
}
