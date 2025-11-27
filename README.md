# 🏖️ Simulation de Sable 3D

Une application Python (PyQt6 + OpenGL) pour simuler et visualiser en temps réel des particules de "sable" avec différents comportements physiques et un rendu 3D interactif.

## ✨ Fonctionnalités
- Rendu 3D via shaders (OpenGL) : grille, boîte de limites, particules billboard
- Plusieurs types de sable (normal, lourd, léger, rebondissant, visqueux, explosif)
- Paramètres physiques ajustables : gravité, friction, cohésion, restitution, viscosité
- Émetteur de particules configurable (position, type, taux, dispersion)
- Contrôles caméra : orbite, zoom, pan
- Interface riche (PyQt6) : onglets, sliders, couleurs, statistiques
- Build exécutable autonome via PyInstaller

## 📁 Structure du projet
```
.
├── main.py                 # Point d'entrée, vérification dépendances
├── gui.py                  # Interface PyQt6 (fenêtre principale + panneaux)
├── renderer.py             # Rendu OpenGL, shaders particules/grille/boîte
├── sand_physics.py         # Moteur physique (particules, collisions, cohésion)
├── presets.py              # (Optionnel) Gestion de presets si utilisé
├── requirements.txt        # Dépendances Python
├── sand_simulation.spec    # Fichier PyInstaller
├── build_with_pyinstaller.py # Script de build
└── README.md               # Documentation
```

## 🛠️ Prérequis
- Python ≥ 3.10 recommandé
- Carte graphique supportant OpenGL 3.3 core
- Environnement X11/Wayland (Linux) ou équivalent sous Windows/macOS

## 📦 Installation
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 🚀 Lancer la simulation
```bash
python main.py
```
Au démarrage :
- Appuyer sur `Espace` pour démarrer/pause la simulation
- Appuyer sur `E` pour activer/désactiver l'émetteur
- Utiliser la barre d'outils pour ajouter rapidement des particules

## 🎮 Contrôles Caméra & Interaction
| Action | Contrôle |
|--------|----------|
| Orbite | Clic gauche + glisser |
| Pan    | Clic milieu + glisser |
| Zoom   | Molette ou clic droit + glisser |
| Play/Pause | `Espace` |
| Activer émetteur | `E` |
| Réinitialiser | `R` |
| Réinitialiser caméra | Bouton dédié (onglet Rendu) |

## ⚙️ Types de Sable (exemples)
| Type | Caractéristiques |
|------|------------------|
| Normal | Paramètres équilibrés |
| Lourd | Masse ↑, gravité ↑, mouvement lent |
| Léger | Masse ↓, chute ralentie |
| Rebondissant | Restitution ↑ |
| Visqueux | Viscosité + cohésion ↑ |
| Explosif | Restitution modérée, idéal pour effets dynamiques |

## 🔬 Moteur Physique (Résumé)
- Intégration simple (Euler semi-implicite) avec sous-steps
- Grille spatiale pour réduire complexité des collisions
- Collisions particules + limites avec friction et restitution
- Cohésion optionnelle entre particules de même type
- Paramètres globaux modulables (friction, gravité)

## 🎨 Rendu
- Vertex + Geometry + Fragment shaders : chaque particule devient un quad (billboard) orienté vers la caméra
- Éclairage sphérique simulé dans le fragment shader (diffus, spéculaire, ambiant)
- Transparence douce sur les bords

## 🏗️ Build Exécutable (PyInstaller)
Générer un dossier `dist/sand_simulation` autonome :
```bash
pip install -r requirements.txt  # S'assure que PyInstaller est installé
python build_with_pyinstaller.py
```
Exécutable créé : `dist/sand_simulation/sand_simulation` (Linux/macOS) ou `.exe` sous Windows si construit là-bas.

Ou directement :
```bash
pyinstaller sand_simulation.spec --noconfirm --clean
```

## 🩺 Dépannage (Troubleshooting)
| Problème | Cause possible | Solution |
|----------|----------------|----------|
| Aucune particule visible | Émetteur inactif / taille trop petite / shaders | Appuyer sur `E`, augmenter "Échelle particules", vérifier GPU OpenGL 3.3 |
| Crash PyInstaller | Import caché manquant | Ajouter le module dans `hidden_imports` dans `sand_simulation.spec` |
| FPS bas | Trop de particules / cohésion coûteuse | Réduire taux émission, désactiver cohésion, diminuer taille fenêtre |
| Artefacts d'affichage | Pilote OpenGL ancien | Mettre à jour pilote / tester sur autre machine |

## 🔧 Extension possible
- Exporter frames ou vidéo (FFmpeg)
- Couche multithread pour physique
- Instancing au lieu de geometry shader pour portabilité
- Uniform Buffer Objects pour optimiser les paramètres partagés

## ✅ Vérification rapide
Checklist locale :
```bash
python -c "import PyQt6, OpenGL, numpy, pyrr; print('OK')"
python main.py  # Tester rendu
```

## 📄 Licence
Projet interne / expérimental (ajoutez la licence si nécessaire).

## 🙌 Crédit
Prototype assisté par IA (Claude Opus 4.5 pour idées / structuration). Rendu et logique adaptés manuellement.

---
Suggestions ou besoin d’une version anglaise ? Ouvrez une issue ou demandez directement.
