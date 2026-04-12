# Harry Potter World — Compilation Guide

## 📋 Processus complet

Ce document explique comment compiler le monde Harry Potter à partir du livre EPUB.

### Étape 1 : Ingestion ✅ (FAIT)

```bash
python scripts/ingest_book.py "Harry Potter 01 Harry Potter and the Sorcerer_s Stone.epub" --output harry_potter_1
```

**Résultat :** 83 segments dans `data/processed/harry_potter_1/`

---

### Étape 2 : Extraction ⏳ (EN COURS)

```bash
python scripts/run_extraction.py harry_potter_1 --model-url http://localhost:8090
```

**Ce que ça fait :**
- 4 passes LLM sur les 83 segments
- Pass 1: Structure (personnages, lieux, objets, événements)
- Pass 2: Relations (graphe social, conflits, timeline)
- Pass 3: Psychologie (personnalité de chaque personnage)
- Pass 4: Symbolisme (thèmes, règles du monde, gravité narrative)

**Résultat attendu :** `data/processed/harry_potter_1/extraction.json`

**Durée estimée :** 2-4 heures selon le modèle LLM

---

### Étape 3 : Nettoyage 🧹 (NOUVEAU)

```bash
python scripts/clean_extraction.py harry_potter_1
```

**Ce que ça fait :**

| Problème | Solution |
|---|---|
| "Harry" et "Harry Potter" = 2 persos différents | Fusion → "Harry Potter" unique |
| 50 desserts dans les objets | Filtrage des objets triviaux |
| Mêmes événements en double | Déduplication |
| Relations avec mauvais IDs | Résolution des noms canoniques |
| Descriptions courtes | Enrichissement automatique |

**Mapping de personnages :**
- `harry` → `Harry Potter`
- `ron` → `Ron Weasley`
- `hermione` → `Hermione Granger`
- `snape` → `Severus Snape`
- `you-know-who` → `Lord Voldemort`
- ... et 50+ autres variantes

**Mapping de lieux :**
- `number four's drive` → `Privet Drive`
- `platform nine-and-three-quarters` → `Platform 9¾`
- `hogwarts school` → `Hogwarts`
- ... etc.

**Résultat :** `data/processed/harry_potter_1/extraction_cleaned.json`

---

### Étape 4 : Compilation 🏗️

**Option A : Version brute (sans nettoyage)**
```bash
python scripts/compile_hp_world.py
```

**Option B : Version nettoyée (RECOMMANDÉ)**
```bash
python scripts/compile_hp_world.py --cleaned
```

**Ce que ça fait :**
- Convertit l'extraction en `WorldBundle`
- Construit les personnages avec relations
- Crée les lieux avec connexions
- Génère les événements canoniques
- Compile les règles du monde
- Prépare les agents AI

**Résultat :** `data/compiled/harry_potter_1/bundle.json`

---

### Étape 5 : Test 🌐

```bash
# Lancer l'interface web
python scripts/web_ui_v2.py

# Ouvrir http://localhost:7860
# Sélectionner "harry_potter_1"
# → Cover art affiché 🖼️
# → Musique en streaming 🎵
# → Gameplay interactif !
```

---

## 📊 Pipeline complet

```
EPUB
 ↓
[1] INGESTION → data/processed/harry_potter_1/segments.json
 ↓
[2] EXTRACTION (4 passes LLM, 2-4h) → extraction.json
 ↓
[3] NETTOYAGE (dédup, filtrage) → extraction_cleaned.json
 ↓
[4] COMPILATION → data/compiled/harry_potter_1/bundle.json
 ↓
[5] TEST WEB UI → http://localhost:7860
```

---

## 🔍 Monitoring

Vérifier la progression de l'extraction :

```bash
# Compter les fichiers cache
dir /b data\cache\harry_potter_1\*.json | find /c /v ""

# Vérifier si extraction.json existe
if exist data\processed\harry_potter_1\extraction.json (echo DONE) else (echo PENDING)

# Voir si Python tourne
tasklist | findstr /i "python"
```

Ou utiliser le script de monitoring :
```bash
powershell -ExecutionPolicy Bypass -File scripts/monitor_extraction.ps1
```

---

## ⚠️ Problèmes connus

### Extraction lente
- **Cause :** Modèle LLM petit (Qwen2.5-7B) ou nombreux segments
- **Solution :** Laisser tourner, c'est normal (2-4h pour 83 segments)

### JSON invalide dans le cache
- **Cause :** LLM produit du JSON malformé
- **Solution :** Le pipeline gère les erreurs silencieusement, mais certaines données peuvent être perdues

### Personnages non reconnus
- **Cause :** Noms trop différents entre les segments
- **Solution :** Le script de nettoyage utilise le fuzzy matching pour résoudre

### Objets triviaux
- **Cause :** LLM extrait tout littéralement (desserts, vêtements...)
- **Solution :** Script de nettoyage filtre par mots-clés

---

## 🛠️ Scripts disponibles

| Script | Usage |
|---|---|
| `ingest_book.py` | Parser le livre EPUB/PDF/TXT |
| `run_extraction.py` | 4-pass LLM extraction |
| `clean_extraction.py` | Nettoyage et enrichissement |
| `compile_hp_world.py` | Compilation du monde |
| `web_ui_v2.py` | Interface web Gradio |
| `icecast_streamer.py` | Streaming musique Icecast |
| `monitor_extraction.ps1` | Monitoring progression |

---

## 📁 Structure des fichiers

```
data/
├── processed/
│   └── harry_potter_1/
│       ├── segments.json          # 83 segments du livre
│       ├── meta.json              # Métadonnées du livre
│       ├── extraction.json        # Brut du LLM (quand terminé)
│       └── extraction_cleaned.json # Après nettoyage
│
├── cache/
│   └── harry_potter_1/
│       └── *.json                 # Cache des appels LLM (57+ fichiers)
│
└── compiled/
    └── harry_potter_1/
        ├── bundle.json            # Monde complet compilé
        ├── locations.json         # Lieux avec connexions
        ├── characters.json        # Personnages avec relations
        ├── objects.json           # Objets du monde
        └── events_canon.json      # Événements canoniques

images/
└── Harry Potter 01.../
    └── *.png                      # Cover art

audio/
└── Harry Potter 01.../
    └── *.mp3                      # OST John Williams (19 tracks)
```

---

*Dernière mise à jour : 2026-04-12*
