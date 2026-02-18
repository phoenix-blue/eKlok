# Stedin Eklok Integratie voor Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Deze custom component integreert de **Stedin Eklok** in Home Assistant, zodat je slim kunt besparen op je energierekening door grote verbruikers aan of uit te schakelen op de beste momenten!

## 🎯 Wat is de Stedin Eklok?

De [Stedin Eklok](https://eklok.nl/) is een real-time indicatie van netbelasting, weergegeven in een eenvoudig kleurensysteem:
- 🟢 **Groen** (< 34): Lage belasting - Ideaal moment voor groot verbruik!
- 🟠 **Oranje** (34-66): Gemiddelde belasting
- 🔴 **Rood** (> 66): Hoge belasting - Vermijd verbruik waar mogelijk

## ✨ Functies

- 📊 **Real-time netbelasting indicatie** (0-100 schaal met kleurcode)
- ⏰ **Slimme planning**: Vind automatisch de beste momenten voor vandaag EN morgen
- 🎨 **Visuele feedback**: Gebruik de exacte Eklok kleuren in je dashboard
- 🤖 **Automatiseringen**: Schakel grote verbruikers automatisch op optimale momenten
- 📈 **Daganalyse**: Overzicht van groene/oranje/rode periodes per dag
- 🔄 **Automatische updates** elke 15 minuten
- 🌐 **Meertalige ondersteuning** (NL, EN)
- 🚫 **Geen login vereist** - Gebruikt publieke API

## 🚀 Installatie via HACS

1. Open HACS in Home Assistant
2. Ga naar "Integrations"
3. Klik op de drie puntjes rechtsboven en selecteer "Custom repositories"
4. Voeg de repository URL toe
5. Selecteer "Integration" als categorie
6. Klik op "Add"
7. Zoek naar "Stedin Eklok" en klik op "Download"
8. Herstart Home Assistant

## 🔧 Handmatige Installatie

1. Kopieer de `custom_components/stedin_eklok` folder naar je Home Assistant `config/custom_components` directory
2. Herstart Home Assistant

## ⚙️ Configuratie

1. Ga naar **Instellingen** > **Apparaten & Services**
2. Klik op **+ Integratie toevoegen**
3. Zoek naar "Stedin Eklok"
4. Klik op "Indienen" (geen login vereist!)
5. De integratie is nu actief ✅

## 📊 Sensors

Deze integratie voegt de volgende sensors toe:

| Sensor | Beschrijving |
|--------|--------------|
| `sensor.stedin_eklok_huidige_waarde` | Huidige netbelasting (0-100) |
| `sensor.stedin_eklok_goed_moment` | Goed moment indicator (Aan/Uit) |
| `sensor.stedin_eklok_groene_uren_vandaag` | Aantal groene uren vandaag |
| `sensor.stedin_eklok_beste_moment_vandaag` | Beste moment vandaag (timestamp) |
| `sensor.stedin_eklok_beste_moment_morgen` | Beste moment morgen (timestamp) |
| `sensor.stedin_eklok_gemiddelde_vandaag` | Gemiddelde waarde vandaag |
| `sensor.stedin_eklok_gemiddelde_morgen` | Gemiddelde waarde morgen |
| `sensor.stedin_eklok_uurdata` | Alle uurdata voor grafieken |

## 🎨 Dashboard

Een voorbeeld dashboard is beschikbaar in [`dashboards/energie-dashboard.yaml`](dashboards/energie-dashboard.yaml):

```yaml
type: sections
title: ⚡ Energie
path: energie
icon: mdi:lightning-bolt
sections:
  - type: grid
    cards:
      - type: gauge
        entity: sensor.stedin_eklok_huidige_waarde
        name: eKlok Netbelasting
        min: 0
        max: 100
        severity:
          green: 0
          yellow: 34
          red: 67
        needle: true
  - type: grid
    cards:
      - type: entities
        title: 🕐 eKlok Momenten
        entities:
          - sensor.stedin_eklok_goed_moment
          - sensor.stedin_eklok_groene_uren_vandaag
          - sensor.stedin_eklok_beste_moment_vandaag
          - sensor.stedin_eklok_beste_moment_morgen
          - sensor.stedin_eklok_gemiddelde_vandaag
  - type: grid
    cards:
      - type: history-graph
        title: 📈 Netbelasting Trend (24u)
        hours_to_show: 24
        refresh_interval: 300
        entities:
          - entity: sensor.stedin_eklok_huidige_waarde
            name: eKlok
```

## 🤖 Voorbeeld Automatisering

```yaml
automation:
  - alias: "Eklok - Start wasmachine bij lage netbelasting"
    trigger:
      - platform: numeric_state
        entity_id: sensor.stedin_eklok_huidige_waarde
        below: 30
    condition:
      - condition: time
        after: "08:00:00"
        before: "20:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.wasmachine
      - service: notify.mobile_app
        data:
          title: "🧺 Wasmachine Gestart"
          message: "Automatisch gestart tijdens lage netbelasting!"
```

## 💡 Slimme Use Cases

- ⚡ **Elektrisch Laden**: Laad je EV tijdens lage netbelasting
- 🔥 **Boiler/Verwarming**: Warm water op tijdens groene periodes
- 🧺 **Huishoudelijke Apparaten**: Start wasmachine, droger, vaatwasser op optimale momenten
- 🔋 **Batterij Opslag**: Laad thuisbatterijen tijdens groene periodes

## 🔧 Vereisten

- Home Assistant 2023.1.0 of hoger
- Internetverbinding voor toegang tot de Eklok API

## ❓ Veelgestelde Vragen

**Q: Moet ik een klant zijn van Stedin?**  
A: Nee! De Eklok API is publiek beschikbaar voor iedereen in Nederland.

**Q: Hoe vaak wordt de data bijgewerkt?**  
A: Elke 15 minuten automatisch.

**Q: Wat betekent de waarde 0-100?**  
A: Dit is een indicatie van de netbelasting. Lager = minder netbelasting = beter moment voor energieverbruik.

## 📜 Licentie

Dit project is gelicentieerd onder de MIT-licentie - zie het [LICENSE](LICENSE) bestand voor details.

## ⚠️ Disclaimer

Deze integratie is niet officieel door Stedin ondersteund of onderschreven. De data komt van de publieke Eklok API. Gebruik op eigen risico.

---

Made with ❤️ for the Home Assistant community | Powered by [Stedin Eklok](https://eklok.nl/)
