# Renovasjonsportal for Home Assistant

En HACS-klar Home Assistant-integrasjon for tømmeplaner fra
`kalender.renovasjonsportal.no`.

Integrasjonen søker etter adressen i Home Assistant-grensesnittet og oppretter
én sensor for neste tømming. Hvis flere avfallstyper tømmes samme dag, samles de
i den samme sensoren.

## Entitet

Sensoren får navnet **Neste tømming** under en enhet med adressens navn.

- Tilstand: neste tømmedato, med device class `date`
- `avfallstyper`: liste over avfallstypene som tømmes denne dagen
- `avfallstyper_tekst`: avfallstypene som kommaseparert tekst
- `dager_til`: antall dager til tømming

Eksempel:

```yaml
state: "2026-08-13"
attributes:
  avfallstyper:
    - Papir
    - Matavfall
  avfallstyper_tekst: Papir, Matavfall
  dager_til: 1
```

Data oppdateres automatisk hver 12. time.

## Installasjon med HACS

Før integrasjonen kan installeres gjennom HACS må dette innholdet ligge i et
offentlig GitHub-repository, for eksempel `sofagris/ha-renovasjonsportal`.

1. Åpne HACS.
2. Velg **Custom repositories**.
3. Legg inn repository-URL-en og velg typen **Integration**.
4. Installer **Renovasjonsportal**.
5. Start Home Assistant på nytt.
6. Gå til **Innstillinger → Enheter og tjenester → Legg til integrasjon**.
7. Søk etter **Renovasjonsportal**, skriv inn adressen og velg riktig treff.

## Manuell installasjon

Kopier katalogen `custom_components/renovasjonsportal` til Home Assistant sin
`config/custom_components/`-katalog og start Home Assistant på nytt. Legg
deretter til integrasjonen fra **Enheter og tjenester**.

## Eksempel på dashboard

Bytt entity-id dersom Home Assistant oppretter et annet navn:

```yaml
type: markdown
content: >-
  {% set entity = 'sensor.storgata_1_neste_tomming' %}
  ## Søppeltømming
  **{{ state_attr(entity, 'avfallstyper_tekst') }}**
  tømmes {{ as_timestamp(states(entity)) | timestamp_custom('%d.%m.%Y') }}
  (om {{ state_attr(entity, 'dager_til') }} dager).
```

## Eksempel på påminnelse kvelden før

```yaml
automation:
  - alias: Sett frem søppel
    triggers:
      - trigger: time
        at: "19:00:00"
    conditions:
      - condition: template
        value_template: >-
          {{ state_attr('sensor.storgata_1_neste_tomming', 'dager_til') == 1 }}
    actions:
      - action: notify.notify
        data:
          title: Sett frem søppel
          message: >-
            I morgen tømmes
            {{ state_attr('sensor.storgata_1_neste_tomming',
                          'avfallstyper_tekst') }}.
```

## API

Integrasjonen bruker de offentlige endepunktene:

- `/api/address/{adresse}` for adresseoppslag
- `/api/address/{adresse-id}/details` for tømmeplan

Ingen API-nøkkel er nødvendig.

## Lisens

MIT
