# Ikoner for Renovasjonsportal

Ikonsett for avfallskategorier i Home Assistant. Alle ikonene har transparent
bakgrunn og leveres i 1024 × 1024 og 256 × 256 piksler.

| Kategori | Filnavn |
| --- | --- |
| Papir | `papir.png` |
| Matavfall | `matavfall.png` |
| Restavfall | `restavfall.png` |
| Glass og metallemballasje | `glass-og-metallemballasje.png` |
| Plastemballasje | `plastemballasje.png` |

## Bruk i Home Assistant

Kopier ønsket oppløsning til eksempelvis:

```text
/config/www/renovasjonsportal/
```

Filene blir da tilgjengelige i dashboardet under:

```text
/local/renovasjonsportal/papir.png
/local/renovasjonsportal/matavfall.png
/local/renovasjonsportal/restavfall.png
/local/renovasjonsportal/glass-og-metallemballasje.png
/local/renovasjonsportal/plastemballasje.png
```

Home Assistants vanlige `icon`-egenskap bruker MDI-symboler. PNG-filene brukes
derfor som bilder i kort som støtter `image`, `entity_picture` eller tilsvarende.

