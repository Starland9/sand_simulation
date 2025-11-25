#!/usr/bin/env python3
"""
===========================================
🏖️ SIMULATION DE SABLE COLORÉ 3D 🏖️
===========================================

Une simulation physique complète de particules de sable en 3D
avec interface graphique pour ajuster les propriétés en temps réel.

Fonctionnalités:
- Moteur physique avec collisions réalistes
- 6 types de sable avec propriétés uniques
- Rendu 3D OpenGL avec shaders
- Interface PyQt6 complète
- Contrôles de caméra intuitifs
- Modification des propriétés en temps réel

Utilisation:
    python main.py

Dépendances:
    pip install -r requirements.txt

Contrôles:
    - Clic gauche + glisser: Orbite caméra
    - Clic milieu + glisser: Pan
    - Clic droit / Molette: Zoom
    - Espace: Play/Pause
    - R: Réinitialiser
    - E: Activer/Désactiver l'émetteur

Auteur: GitHub Copilot
"""

import sys
import os

# Ajoute le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """Vérifie que toutes les dépendances sont installées"""
    missing = []
    
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
        
    try:
        import PyQt6
    except ImportError:
        missing.append("PyQt6")
        
    try:
        import OpenGL
    except ImportError:
        missing.append("PyOpenGL")
        
    try:
        import pyrr
    except ImportError:
        missing.append("pyrr")
        
    if missing:
        print("❌ Dépendances manquantes:")
        for dep in missing:
            print(f"   - {dep}")
        print("\n📦 Installez-les avec:")
        print("   pip install -r requirements.txt")
        print("   ou")
        print(f"   pip install {' '.join(missing)}")
        sys.exit(1)
        
    print("✅ Toutes les dépendances sont installées!")


def main():
    """Point d'entrée principal"""
    print("""
    ╔═══════════════════════════════════════════════════╗
    ║     🏖️  SIMULATION DE SABLE COLORÉ 3D  🏖️        ║
    ╠═══════════════════════════════════════════════════╣
    ║  Simulation physique de particules avec:          ║
    ║  • 6 types de sable différents                    ║
    ║  • Rendu 3D OpenGL                                ║
    ║  • Interface graphique complète                   ║
    ║  • Propriétés ajustables en temps réel            ║
    ╚═══════════════════════════════════════════════════╝
    """)
    
    # Vérifie les dépendances
    check_dependencies()
    
    print("🚀 Démarrage de l'application...")
    
    # Import et lancement de l'interface
    from gui import main as gui_main
    gui_main()


if __name__ == "__main__":
    main()
