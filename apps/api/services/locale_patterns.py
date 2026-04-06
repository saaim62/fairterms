"""
Non-English regex fragments for rule categories (applied on lowercased text in analyzer; indices use str.lower() for alignment).
Keys: category id → locale → patterns merged with English `Rule.patterns`.

See `locale_config.SUPPORTED_EXTRA_LOCALES` for the 24 non-English locales (25 languages
including English base patterns). Additional banks are merged from `locale_patterns_i18n`.
"""

from __future__ import annotations

from services.locale_config import SUPPORTED_EXTRA_LOCALES as LOCALE_PATTERN_LANGUAGES

LOCALE_EXTRA_PATTERNS: dict[str, dict[str, list[str]]] = {
    "arbitration_waiver": {
        "es": [
            r"arbitraje",
            r"renuncia.{0,50}(acción|demanda) colectiva",
            r"juicio por jurado",
            r"mediación obligatoria",
        ],
        "de": [
            r"schiedsgericht",
            r"schiedsverfahren",
            r"verzicht.{0,50}(sammelklage|klassenklage)",
            r"schlichtungsverfahren",
        ],
        "fr": [
            r"arbitrage",
            r"renonciation.{0,50}(action|recours) collective",
            r"renonciation.{0,40}jury",
        ],
    },
    "class_bar_standalone": {
        "es": [
            r"acciones? colectivas?.{0,40}no (permitidas|autorizadas)",
            r"renuncia.{0,40}representación",
        ],
        "de": [
            r"keine sammelklage",
            r"verbots.{0,30}sammelklage",
        ],
        "fr": [
            r"action de groupe.{0,40}exclu",
            r"pas d'action collective",
        ],
    },
    "auto_renewal": {
        "es": [
            r"renovación automática",
            r"renueva(n)? automáticamente",
            r"renovación tacita",
        ],
        "de": [
            r"automatische verlängerung",
            r"verlängert sich automatisch",
            r"stillschweigende verlängerung",
        ],
        "fr": [
            r"renouvellement automatique",
            r"reconduit tacitement",
        ],
    },
    "zombie_renewal": {
        "es": [
            r"sin recordatorio",
            r"renovación anual.{0,60}sin aviso",
        ],
        "de": [
            r"ohne erinnerung",
            r"jahresabo.{0,50}ohne hinweis",
        ],
        "fr": [
            r"sans rappel",
            r"abonnement annuel.{0,50}sans notification",
        ],
    },
    "data_rights": {
        "es": [
            r"licencia (irrevocable|perpetua)",
            r"datos personales.{0,50}terceros",
            r"cesión.{0,40}datos",
        ],
        "de": [
            r"unwiderrufliche lizenz",
            r"dauerhafte lizenz",
            r"personenbezogene daten.{0,50}dritte",
        ],
        "fr": [
            r"licence (irrévocable|perpétuelle)",
            r"données personnelles.{0,50}tiers",
        ],
    },
    "data_succession": {
        "es": [
            r"sucesor.{0,50}(datos|información)",
            r"fusiones?.{0,40}datos personales",
            r"quiebra.{0,50}datos",
        ],
        "de": [
            r"nachfolger.{0,50}(daten|informationen)",
            r"übernahme.{0,40}nutzerdaten",
            r"insolvenz.{0,50}daten",
        ],
        "fr": [
            r"successeur.{0,50}données",
            r"fusion.{0,40}données personnelles",
        ],
    },
    "cross_service_tracking": {
        "es": [
            r"combinar.{0,40}datos.{0,40}servicios",
            r"entre productos",
        ],
        "de": [
            r"kombination.{0,40}daten.{0,40}dienste",
            r"übergreifend.{0,30}produkte",
        ],
        "fr": [
            r"combiner.{0,40}données.{0,40}services",
        ],
    },
    "unilateral_changes": {
        "es": [
            r"modificar.{0,40}(términos|condiciones).{0,40}sin",
            r"uso continuado.{0,40}acept",
        ],
        "de": [
            r"änder(n|ung).{0,40}(bedingungen|agb).{0,40}ohne",
            r"fortgesetzte nutzung.{0,40}akzept",
        ],
        "fr": [
            r"modifier.{0,40}(conditions|termes).{0,40}sans",
            r"utilisation continue.{0,40}constitue",
        ],
    },
    "retroactive_changes": {
        "es": [
            r"retroactivo",
            r"conducta previa",
            r"ya recopilados",
        ],
        "de": [
            r"rückwirkend",
            r"bereits erhobene daten",
        ],
        "fr": [
            r"rétroactif",
            r"données déjà collectées",
        ],
    },
    "cancellation_friction": {
        "es": [
            r"no reembolsable",
            r"sin reembolso",
            r"cancelación.{0,40}teléfono",
        ],
        "de": [
            r"nicht erstattungsfähig",
            r"keine rückerstattung",
            r"kündigung.{0,40}telefon",
        ],
        "fr": [
            r"non remboursable",
            r"aucun remboursement",
            r"annulation.{0,40}téléphone",
        ],
    },
    "fee_modification": {
        "es": [
            r"aumento de precios",
            r"tarifa.{0,40}sin previo aviso",
        ],
        "de": [
            r"preiserhöhung",
            r"gebühr.{0,40}ohne vorankündigung",
        ],
        "fr": [
            r"augmentation de prix",
            r"frais.{0,40}sans préavis",
        ],
    },
    "gag_clauses": {
        "es": [
            r"no difamación",
            r"prohibición.{0,40}reseñas",
            r"críticas negativas",
        ],
        "de": [
            r"nicht abwerten",
            r"bewertungsverbot",
            r"negative rezension",
        ],
        "fr": [
            r"non-dénigrement",
            r"interdiction.{0,40}avis",
        ],
    },
    "unilateral_interpretation": {
        "es": [
            r"único criterio",
            r"interpretación exclusiva",
            r"a nuestra entera discreción",
        ],
        "de": [
            r"alleinige auslegung",
            r"nach unserem ermessen",
        ],
        "fr": [
            r"seule interprétation",
            r"à notre seule discrétion",
        ],
    },
    "liquidated_damages_penalties": {
        "es": [
            r"daños liquidados",
            r"penalización.{0,40}por infracción",
        ],
        "de": [
            r"vertragsstrafe",
            r"pauschalierte schadensersatz",
        ],
        "fr": [
            r"dommages et intérêts forfaitaires",
            r"pénalité.{0,40}manquement",
        ],
    },
    "perpetual_restraint": {
        "es": [
            r"no competencia.{0,40}indefinid",
            r"sobrevive.{0,40}terminación",
        ],
        "de": [
            r"wettbewerbsverbot.{0,40}unbefristet",
            r"überdauert.{0,40}beendigung",
        ],
        "fr": [
            r"non-concurrence.{0,40}indétermin",
            r"survit.{0,40}résiliation",
        ],
    },
    "waiver_of_statutory_rights": {
        "es": [
            r"rgpd",
            r"gdpr",
            r"renuncia.{0,40}derechos del consumidor",
        ],
        "de": [
            r"dsgvo",
            r"verzicht.{0,40}verbraucherrechte",
        ],
        "fr": [
            r"rgpd",
            r"renonciation.{0,40}droits des consommateurs",
        ],
    },
    "limitation_of_liability": {
        "es": [
            r"limitación de responsabilidad",
            r"no seremos responsables.{0,40}daños indirectos",
        ],
        "de": [
            r"haftungsbeschränkung",
            r"keine haftung.{0,40}folgeschäden",
        ],
        "fr": [
            r"limitation de responsabilité",
            r"aucune responsabilité.{0,40}dommages indirects",
        ],
    },
    "disclaimer_of_warranties": {
        "es": [
            r"sin garantía",
            r"tal cual",
            r"comercialización",
        ],
        "de": [
            r"ohne gewähr",
            r"wie besehen",
            r"marktgängigkeit",
        ],
        "fr": [
            r"sans garantie",
            r"en l'état",
            r"qualité marchande",
        ],
    },
    "broad_indemnity": {
        "es": [
            r"indemnizar",
            r"mantener indemne",
        ],
        "de": [
            r"freistellung",
            r"schadlos halten",
        ],
        "fr": [
            r"indemniser",
            r"tenir indemne",
        ],
    },
    "forum_selection_exclusive": {
        "es": [
            r"jurisdicción exclusiva",
            r"foro exclusivo",
        ],
        "de": [
            r"ausschließlicher gerichtsstand",
            r"alleinige zuständigkeit",
        ],
        "fr": [
            r"juridiction exclusive",
            r"tribunaux exclusivement compétents",
        ],
    },
    "discretionary_termination": {
        "es": [
            r"suspender.{0,40}cuenta.{0,40}discreción",
            r"terminar.{0,40}sin previo aviso",
        ],
        "de": [
            r"konto.{0,40}sperren.{0,40}ermessen",
            r"beenden.{0,40}ohne vorankündigung",
        ],
        "fr": [
            r"suspendre.{0,40}compte.{0,40}discrétion",
            r"résilier.{0,40}sans préavis",
        ],
    },
    "data_selling": {
        "es": [
            r"vender.{0,40}datos personales",
            r"venta de información personal",
        ],
        "de": [
            r"verkauf.{0,40}personenbezogene daten",
        ],
        "fr": [
            r"vente.{0,40}données personnelles",
        ],
    },
    "mandatory_delay_tactics": {
        "es": [
            r"mediación.{0,50}antes de demandar",
        ],
        "de": [
            r"mediation.{0,50}vor gericht",
        ],
        "fr": [
            r"médiation.{0,50}avant toute action",
        ],
    },
    "no_injunctive_relief": {
        "es": [
            r"sin medidas cautelares",
            r"renuncia.{0,40}medida cautelar",
        ],
        "de": [
            r"keine einstweilige verfügung",
        ],
        "fr": [
            r"pas de mesure injonctive",
        ],
    },
    "one_way_attorneys_fees": {
        "es": [
            r"honorarios de abogados.{0,40}parte vencedora",
        ],
        "de": [
            r"anwaltskosten.{0,40}obsiegende partei",
        ],
        "fr": [
            r"honoraires d'avocats.{0,40}partie gagnante",
        ],
    },
    "shortened_limitation_period": {
        "es": [
            r"plazo de un año",
            r"prescripción.{0,40}un año",
        ],
        "de": [
            r"innerhalb eines jahres",
            r"verjährung.{0,40}ein jahr",
        ],
        "fr": [
            r"délai d'un an",
            r"prescription.{0,40}un an",
        ],
    },
    "ai_training_license": {
        "es": [
            r"entren(ar|amiento).{0,40}(ia|inteligencia artificial|modelo)",
            r"aprendizaje automático",
        ],
        "de": [
            r"trainieren.{0,40}(ki|künstliche intelligenz|modell)",
            r"machine learning",
        ],
        "fr": [
            r"entraîn(er|ement).{0,40}(ia|intelligence artificielle)",
        ],
    },
    "biometric_harvesting": {
        "es": [
            r"datos biométricos",
            r"reconocimiento facial",
        ],
        "de": [
            r"biometrische daten",
            r"gesichtserkennung",
        ],
        "fr": [
            r"données biométriques",
            r"reconnaissance faciale",
        ],
    },
    "inactivity_fee_seizure": {
        "es": [
            r"cuota de inactividad",
            r"cuenta inactiva.{0,40}(caduca|expira)",
        ],
        "de": [
            r"inaktivitätsgebühr",
            r"inaktives konto.{0,40}verfällt",
        ],
        "fr": [
            r"frais d'inactivité",
            r"compte inactif.{0,40}expire",
        ],
    },
    "english_language_supremacy": {
        "es": [
            r"solo la versión en inglés",
            r"versión inglesa prevalece",
        ],
        "de": [
            r"nur die englische fassung",
            r"englische version maßgeblich",
        ],
        "fr": [
            r"seule la version anglaise",
            r"version anglaise prévaut",
        ],
    },
    "device_exploitation": {
        "es": [
            r"criptominería",
            r"poder de procesamiento",
        ],
        "de": [
            r"krypto[- ]?mining",
            r"rechenleistung",
        ],
        "fr": [
            r"crypto[- ]?minage",
            r"puissance de calcul",
        ],
    },
    "shadow_profiling": {
        "es": [
            r"correos electrónicos de contactos",
            r"perfiles de terceros",
        ],
        "de": [
            r"kontaktdaten",
            r"drittanbieterprofile",
        ],
        "fr": [
            r"contacts.{0,40}collecte",
        ],
    },
    "overbroad_ip_restrictions": {
        "es": [
            r"ingeniería inversa",
            r"descompilar",
        ],
        "de": [
            r"reverse engineering",
            r"dekompilieren",
        ],
        "fr": [
            r"ingénierie inverse",
            r"décompiler",
        ],
    },
    "no_assignment_by_user": {
        "es": [
            r"no puede ceder.{0,60}nosotros podemos",
        ],
        "de": [
            r"sie dürfen nicht abtreten.{0,60}wir dürfen",
        ],
        "fr": [
            r"vous ne pouvez pas céder.{0,60}nous pouvons",
        ],
    },
    "third_party_disclaimer": {
        "es": [
            r"no responsables.{0,40}terceros",
            r"bajo su propio riesgo.{0,40}terceros",
        ],
        "de": [
            r"nicht verantwortlich.{0,40}dritte",
        ],
        "fr": [
            r"pas responsables.{0,40}tiers",
        ],
    },
    "force_majeure_broad": {
        "es": [
            r"fuerza mayor",
            r"caso fortuito",
        ],
        "de": [
            r"höhere gewalt",
        ],
        "fr": [
            r"force majeure",
        ],
    },
    "notice_of_breach_delay": {
        "es": [
            r"notificar.{0,40}dentro de (60|90|120) días",
        ],
        "de": [
            r"benachrichtigen.{0,40}innerhalb von (60|90|120) tagen",
        ],
        "fr": [
            r"notifier.{0,40}sous (60|90|120) jours",
        ],
    },
    "children_data_collection": {
        "es": [
            r"menores de 13",
            r"consentimiento parental",
        ],
        "de": [
            r"unter 13 jahren",
            r"elterliche zustimmung",
        ],
        "fr": [
            r"moins de 13 ans",
            r"consentement parental",
        ],
    },
    "marketing_communications_burden": {
        "es": [
            r"marketing.{0,40}sms",
            r"comunicaciones promocionales",
        ],
        "de": [
            r"werbe[- ]?sms",
            r"werbebotschaften",
        ],
        "fr": [
            r"sms marketing",
            r"communications promotionnelles",
        ],
    },
    "private_message_monitoring": {
        "es": [
            r"mensajes privados",
            r"leer.{0,40}mensajes directos",
        ],
        "de": [
            r"private nachrichten",
            r"überwachung.{0,40}nachrichten",
        ],
        "fr": [
            r"messages privés",
            r"lire.{0,40}messages directs",
        ],
    },
    "off_platform_tracking": {
        "es": [
            r"historial del navegador",
            r"registro de pulsaciones",
        ],
        "de": [
            r"browserverlauf",
            r"tastatureingaben",
        ],
        "fr": [
            r"historique du navigateur",
            r"frappes au clavier",
        ],
    },
    "payment_method_updating": {
        "es": [
            r"actualización automática.{0,40}tarjeta",
            r"account updater",
        ],
        "de": [
            r"automatische aktualisierung.{0,40}zahlungsdaten",
            r"account updater",
        ],
        "fr": [
            r"mise à jour automatique.{0,40}carte",
            r"account updater",
        ],
    },
    "consent_to_background_check": {
        "es": [
            r"verificación de antecedentes",
            r"consentimiento.{0,40}chequeo de crédito",
        ],
        "de": [
            r"überprüfung des leumunds",
            r"bonitätsprüfung",
        ],
        "fr": [
            r"vérification des antécédents",
            r"enquête de crédit",
        ],
    },
}

from services.locale_patterns_i18n import apply_extra_lang_banks

apply_extra_lang_banks(LOCALE_EXTRA_PATTERNS)
