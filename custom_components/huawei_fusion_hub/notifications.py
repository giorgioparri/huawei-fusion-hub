"""Localized texts for backend notifications.

Backend-generated persistent notifications cannot use the frontend
translation system, so we pick the language from hass.config.language
with English fallback.
"""
from __future__ import annotations

TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "title": "Huawei Fusion Hub",
        "summary": (
            "Discovery completed: **{total} entities** created ({counts}).\n\n"
            "Entities matched per source: {per_source}."
        ),
        "rediscovery_new": "**{n} new entities** created ({counts})",
        "rediscovery_gained": (
            "**{n} existing entities** gained an additional fallback source"
        ),
        "rediscovery": "New data detected from {sources}: {parts}.",
        "offline": (
            "Source **{name}** is offline. "
            "Values are now served by the next available source."
        ),
        "online": "Source **{name}** is back online.",
        "derived": (
            "Two calculated sensors have been added: **estimated time to full "
            "charge** and **estimated time to minimum charge**.\n\n"
            "They are derived from the battery power and state of charge the hub "
            "already aggregates, and they assume the current rate holds until the "
            "target — so they move as conditions change, and publish nothing when "
            "the battery is idle.\n\n"
            "You can turn them off, or change the minimum charge level they count "
            "down to, from *Settings → Devices & Services → Huawei Fusion Hub → "
            "Configure*.\n\n"
            "[Details in the documentation]"
            "(https://github.com/giorgioparri/huawei-fusion-hub"
            "#battery-runtime-estimates)"
        ),
    },
    "it": {
        "title": "Huawei Fusion Hub",
        "summary": (
            "Discovery completata: **{total} entità** create ({counts}).\n\n"
            "Entità abbinate per sorgente: {per_source}."
        ),
        "rediscovery_new": "**{n} nuove entità** create ({counts})",
        "rediscovery_gained": (
            "**{n} entità esistenti** hanno guadagnato una sorgente di fallback"
        ),
        "rediscovery": "Nuovi dati rilevati da {sources}: {parts}.",
        "offline": (
            "La sorgente **{name}** è offline. "
            "I valori vengono ora forniti dalla successiva sorgente disponibile."
        ),
        "online": "La sorgente **{name}** è di nuovo online.",
        "derived": (
            "Sono stati aggiunti due sensori calcolati: **tempo stimato alla "
            "carica completa** e **tempo stimato al livello minimo**.\n\n"
            "Sono derivati dalla potenza e dallo stato di carica della batteria "
            "che l'hub già aggrega, e assumono che il regime attuale si mantenga "
            "fino all'obiettivo: si muovono quindi al variare delle condizioni, e "
            "non pubblicano nulla quando la batteria è ferma.\n\n"
            "Puoi disattivarli, o cambiare il livello minimo di carica fino a cui "
            "contano, da *Impostazioni → Dispositivi e servizi → Huawei Fusion "
            "Hub → Configura*.\n\n"
            "[Dettagli nella documentazione]"
            "(https://github.com/giorgioparri/huawei-fusion-hub"
            "#battery-runtime-estimates)"
        ),
    },
    "de": {
        "title": "Huawei Fusion Hub",
        "summary": (
            "Erkennung abgeschlossen: **{total} Entitäten** erstellt ({counts}).\n\n"
            "Zugeordnete Entitäten pro Quelle: {per_source}."
        ),
        "rediscovery_new": "**{n} neue Entitäten** erstellt ({counts})",
        "rediscovery_gained": (
            "**{n} bestehende Entitäten** haben eine zusätzliche Ausweichquelle "
            "erhalten"
        ),
        "rediscovery": "Neue Daten von {sources} erkannt: {parts}.",
        "offline": (
            "Die Quelle **{name}** ist offline. "
            "Die Werte kommen jetzt von der nächsten verfügbaren Quelle."
        ),
        "online": "Die Quelle **{name}** ist wieder online.",
        "derived": (
            "Zwei berechnete Sensoren wurden hinzugefügt: **geschätzte Zeit bis "
            "zur vollen Ladung** und **geschätzte Zeit bis zur Mindestladung**.\n\n"
            "Sie werden aus der Batterieleistung und dem Ladezustand abgeleitet, "
            "die der Hub bereits zusammenführt, und gehen davon aus, dass die "
            "aktuelle Rate bis zum Ziel gleich bleibt — sie ändern sich daher mit "
            "den Bedingungen und veröffentlichen nichts, solange die Batterie "
            "ruht.\n\n"
            "Du kannst sie unter *Einstellungen → Geräte & Dienste → Huawei Fusion "
            "Hub → Konfigurieren* ausschalten oder den Mindestladestand ändern, "
            "bis zu dem sie herunterzählen.\n\n"
            "[Details in der Dokumentation]"
            "(https://github.com/giorgioparri/huawei-fusion-hub"
            "#battery-runtime-estimates)"
        ),
    },
}


def get_texts(hass) -> dict[str, str]:
    lang = (hass.config.language or "en").split("-")[0].lower()
    return TEXTS.get(lang, TEXTS["en"])
