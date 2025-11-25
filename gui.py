"""
Interface Graphique PyQt6 pour la Simulation de Sable
=====================================================
Interface complète avec contrôles pour:
- Propriétés physiques globales
- Propriétés par type de sable
- Contrôles de rendu
- Statistiques en temps réel
"""

import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QSlider, QComboBox, QPushButton, QSpinBox,
    QDoubleSpinBox, QCheckBox, QTabWidget, QScrollArea, QFrame,
    QColorDialog, QSplitter, QStatusBar, QToolBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QAction, QIcon, QPalette
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *

from sand_physics import (
    PhysicsEngine, SandType, SandProperties, DEFAULT_SAND_PROPERTIES
)
from renderer import Renderer
from presets import apply_preset, get_preset_names, PRESETS


class SandGLWidget(QOpenGLWidget):
    """Widget OpenGL pour le rendu de la simulation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.renderer = Renderer()
        self.physics = PhysicsEngine()
        
        # État de la souris
        self.last_mouse_pos = None
        self.mouse_button = None
        
        # Timer pour l'animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.is_running = False
        self.target_fps = 60
        
        # Émetteur de sable
        self.emitter_active = False
        self.emitter_type = SandType.NORMAL
        self.emitter_rate = 10
        self.emitter_spread = 2.0
        self.emitter_position = np.array([0.0, 40.0, 0.0], dtype=np.float32)
        
        self.setMinimumSize(400, 400)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def initializeGL(self):
        """Initialise OpenGL"""
        self.renderer.initialize()
        self.renderer.set_bounds(self.physics.bounds)
        
    def resizeGL(self, width, height):
        """Redimensionne le viewport"""
        glViewport(0, 0, width, height)
        
    def paintGL(self):
        """Dessine la scène"""
        # Met à jour les données des particules
        positions, colors, sizes = self.physics.get_particle_data()
        self.renderer.update_particles(positions, colors, sizes)
        
        # Rend la scène
        self.renderer.render(self.width(), self.height())
        
    def update_simulation(self):
        """Met à jour la simulation"""
        if self.is_running:
            # Émetteur de sable
            if self.emitter_active:
                self.emit_particles()
            
            # Met à jour la physique
            self.physics.update()
            
            # Rafraîchit l'affichage
            self.update()
            
    def emit_particles(self):
        """Émet des particules depuis l'émetteur"""
        self.physics.add_particles_burst(
            self.emitter_position,
            self.emitter_rate,
            self.emitter_spread,
            self.emitter_type,
            np.array([0.0, -5.0, 0.0], dtype=np.float32)
        )
        
    def start_simulation(self):
        """Démarre la simulation"""
        self.is_running = True
        self.timer.start(1000 // self.target_fps)
        
    def stop_simulation(self):
        """Arrête la simulation"""
        self.is_running = False
        self.timer.stop()
        
    def toggle_simulation(self):
        """Bascule la simulation"""
        if self.is_running:
            self.stop_simulation()
        else:
            self.start_simulation()
            
    def reset_simulation(self):
        """Réinitialise la simulation"""
        self.physics.clear_particles()
        self.update()
        
    def mousePressEvent(self, event):
        """Gère les clics souris"""
        self.last_mouse_pos = event.position()
        self.mouse_button = event.button()
        
    def mouseReleaseEvent(self, event):
        """Gère le relâchement de la souris"""
        self.mouse_button = None
        
    def mouseMoveEvent(self, event):
        """Gère le mouvement de la souris"""
        if self.last_mouse_pos is None:
            return
            
        dx = event.position().x() - self.last_mouse_pos.x()
        dy = event.position().y() - self.last_mouse_pos.y()
        
        if self.mouse_button == Qt.MouseButton.LeftButton:
            # Orbite
            self.renderer.camera.orbit(dx, dy)
        elif self.mouse_button == Qt.MouseButton.MiddleButton:
            # Pan
            self.renderer.camera.pan(-dx, dy)
        elif self.mouse_button == Qt.MouseButton.RightButton:
            # Zoom
            self.renderer.camera.zoom(dy * 0.01)
            
        self.last_mouse_pos = event.position()
        self.update()
        
    def wheelEvent(self, event):
        """Gère la molette de la souris"""
        delta = event.angleDelta().y() / 120
        self.renderer.camera.zoom(delta)
        self.update()
        
    def keyPressEvent(self, event):
        """Gère les touches du clavier"""
        key = event.key()
        
        if key == Qt.Key.Key_Space:
            self.toggle_simulation()
        elif key == Qt.Key.Key_R:
            self.reset_simulation()
        elif key == Qt.Key.Key_E:
            self.emitter_active = not self.emitter_active


class PropertySlider(QWidget):
    """Widget slider personnalisé avec label et valeur"""
    
    valueChanged = pyqtSignal(float)
    
    def __init__(self, label: str, min_val: float, max_val: float, 
                 default: float, decimals: int = 2, parent=None):
        super().__init__(parent)
        self.decimals = decimals
        self.scale = 10 ** decimals
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        self.label = QLabel(label)
        self.label.setMinimumWidth(100)
        layout.addWidget(self.label)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(int(min_val * self.scale))
        self.slider.setMaximum(int(max_val * self.scale))
        self.slider.setValue(int(default * self.scale))
        self.slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.slider, stretch=1)
        
        # Valeur
        self.value_label = QLabel(f"{default:.{decimals}f}")
        self.value_label.setMinimumWidth(50)
        layout.addWidget(self.value_label)
        
    def _on_value_changed(self, value):
        """Callback interne du slider"""
        real_value = value / self.scale
        self.value_label.setText(f"{real_value:.{self.decimals}f}")
        self.valueChanged.emit(real_value)
        
    def value(self) -> float:
        """Retourne la valeur actuelle"""
        return self.slider.value() / self.scale
        
    def setValue(self, value: float):
        """Définit la valeur"""
        self.slider.setValue(int(value * self.scale))


class ColorButton(QPushButton):
    """Bouton pour sélectionner une couleur"""
    
    colorChanged = pyqtSignal(tuple)
    
    def __init__(self, initial_color: tuple = (1.0, 1.0, 1.0), parent=None):
        super().__init__(parent)
        self.color = initial_color
        self._update_style()
        self.clicked.connect(self._pick_color)
        self.setMinimumHeight(30)
        
    def _update_style(self):
        """Met à jour le style du bouton"""
        r, g, b = [int(c * 255) for c in self.color]
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgb({r}, {g}, {b});
                border: 2px solid #555;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: #888;
            }}
        """)
        
    def _pick_color(self):
        """Ouvre le sélecteur de couleur"""
        r, g, b = [int(c * 255) for c in self.color]
        initial = QColor(r, g, b)
        color = QColorDialog.getColor(initial, self, "Choisir une couleur")
        
        if color.isValid():
            self.color = (color.redF(), color.greenF(), color.blueF())
            self._update_style()
            self.colorChanged.emit(self.color)
            
    def setColor(self, color: tuple):
        """Définit la couleur"""
        self.color = color
        self._update_style()


class PhysicsControlPanel(QWidget):
    """Panneau de contrôle des propriétés physiques globales"""
    
    def __init__(self, gl_widget: SandGLWidget, parent=None):
        super().__init__(parent)
        self.gl_widget = gl_widget
        self._setup_ui()
        
    def _setup_ui(self):
        """Configure l'interface"""
        layout = QVBoxLayout(self)
        
        # Groupe Gravité
        gravity_group = QGroupBox("Gravité")
        gravity_layout = QVBoxLayout(gravity_group)
        
        self.gravity_slider = PropertySlider("Échelle", 0.0, 3.0, 1.0)
        self.gravity_slider.valueChanged.connect(
            lambda v: setattr(self.gl_widget.physics, 'global_gravity_scale', v)
        )
        gravity_layout.addWidget(self.gravity_slider)
        
        layout.addWidget(gravity_group)
        
        # Groupe Friction
        friction_group = QGroupBox("Friction Globale")
        friction_layout = QVBoxLayout(friction_group)
        
        self.friction_slider = PropertySlider("Friction", 0.0, 2.0, 1.0)
        self.friction_slider.valueChanged.connect(
            lambda v: setattr(self.gl_widget.physics, 'global_friction', v)
        )
        friction_layout.addWidget(self.friction_slider)
        
        layout.addWidget(friction_group)
        
        # Groupe Collisions
        collision_group = QGroupBox("Interactions")
        collision_layout = QVBoxLayout(collision_group)
        
        self.collision_check = QCheckBox("Collisions entre particules")
        self.collision_check.setChecked(True)
        self.collision_check.toggled.connect(
            lambda v: setattr(self.gl_widget.physics, 'enable_collisions', v)
        )
        collision_layout.addWidget(self.collision_check)
        
        self.cohesion_check = QCheckBox("Cohésion entre particules")
        self.cohesion_check.setChecked(True)
        self.cohesion_check.toggled.connect(
            lambda v: setattr(self.gl_widget.physics, 'enable_cohesion', v)
        )
        collision_layout.addWidget(self.cohesion_check)
        
        layout.addWidget(collision_group)
        
        # Groupe Simulation
        sim_group = QGroupBox("Simulation")
        sim_layout = QVBoxLayout(sim_group)
        
        self.substeps_slider = PropertySlider("Sous-étapes", 1, 8, 2, decimals=0)
        self.substeps_slider.valueChanged.connect(
            lambda v: setattr(self.gl_widget.physics, 'sub_steps', int(v))
        )
        sim_layout.addWidget(self.substeps_slider)
        
        self.timestep_slider = PropertySlider("Pas de temps", 0.005, 0.05, 1/60, decimals=3)
        self.timestep_slider.valueChanged.connect(
            lambda v: setattr(self.gl_widget.physics, 'time_step', v)
        )
        sim_layout.addWidget(self.timestep_slider)
        
        layout.addWidget(sim_group)
        
        layout.addStretch()


class SandTypePanel(QWidget):
    """Panneau pour configurer un type de sable spécifique"""
    
    def __init__(self, sand_type: SandType, gl_widget: SandGLWidget, parent=None):
        super().__init__(parent)
        self.sand_type = sand_type
        self.gl_widget = gl_widget
        self.properties = DEFAULT_SAND_PROPERTIES[sand_type]
        self._setup_ui()
        
    def _setup_ui(self):
        """Configure l'interface"""
        layout = QVBoxLayout(self)
        
        # Couleur
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Couleur:"))
        self.color_btn = ColorButton(self.properties.color)
        self.color_btn.colorChanged.connect(self._on_color_changed)
        color_layout.addWidget(self.color_btn, stretch=1)
        layout.addLayout(color_layout)
        
        # Propriétés physiques
        self.mass_slider = PropertySlider("Masse", 0.1, 5.0, self.properties.mass)
        self.mass_slider.valueChanged.connect(self._on_property_changed)
        layout.addWidget(self.mass_slider)
        
        self.friction_slider = PropertySlider("Friction", 0.0, 1.0, self.properties.friction)
        self.friction_slider.valueChanged.connect(self._on_property_changed)
        layout.addWidget(self.friction_slider)
        
        self.restitution_slider = PropertySlider("Rebond", 0.0, 1.0, self.properties.restitution)
        self.restitution_slider.valueChanged.connect(self._on_property_changed)
        layout.addWidget(self.restitution_slider)
        
        self.cohesion_slider = PropertySlider("Cohésion", 0.0, 1.0, self.properties.cohesion)
        self.cohesion_slider.valueChanged.connect(self._on_property_changed)
        layout.addWidget(self.cohesion_slider)
        
        self.viscosity_slider = PropertySlider("Viscosité", 0.0, 1.0, self.properties.viscosity)
        self.viscosity_slider.valueChanged.connect(self._on_property_changed)
        layout.addWidget(self.viscosity_slider)
        
        self.gravity_slider = PropertySlider("Gravité", 0.1, 3.0, self.properties.gravity_scale)
        self.gravity_slider.valueChanged.connect(self._on_property_changed)
        layout.addWidget(self.gravity_slider)
        
        self.size_slider = PropertySlider("Taille", 0.2, 1.5, self.properties.particle_size)
        self.size_slider.valueChanged.connect(self._on_property_changed)
        layout.addWidget(self.size_slider)
        
        # Bouton reset
        reset_btn = QPushButton("Réinitialiser")
        reset_btn.clicked.connect(self._reset_properties)
        layout.addWidget(reset_btn)
        
        layout.addStretch()
        
    def _on_color_changed(self, color: tuple):
        """Callback changement de couleur"""
        self.properties.color = color
        self._update_existing_particles()
        
    def _on_property_changed(self):
        """Callback changement de propriété"""
        self.properties.mass = self.mass_slider.value()
        self.properties.friction = self.friction_slider.value()
        self.properties.restitution = self.restitution_slider.value()
        self.properties.cohesion = self.cohesion_slider.value()
        self.properties.viscosity = self.viscosity_slider.value()
        self.properties.gravity_scale = self.gravity_slider.value()
        self.properties.particle_size = self.size_slider.value()
        self._update_existing_particles()
        
    def _update_existing_particles(self):
        """Met à jour les particules existantes de ce type"""
        for particle in self.gl_widget.physics.particles:
            if particle.sand_type == self.sand_type:
                particle.properties = SandProperties(
                    name=self.properties.name,
                    color=self.properties.color,
                    mass=self.properties.mass,
                    friction=self.properties.friction,
                    restitution=self.properties.restitution,
                    cohesion=self.properties.cohesion,
                    viscosity=self.properties.viscosity,
                    gravity_scale=self.properties.gravity_scale,
                    particle_size=self.properties.particle_size
                )
        self.gl_widget.update()
        
    def _reset_properties(self):
        """Réinitialise les propriétés par défaut"""
        default = DEFAULT_SAND_PROPERTIES[self.sand_type]
        self.color_btn.setColor(default.color)
        self.mass_slider.setValue(default.mass)
        self.friction_slider.setValue(default.friction)
        self.restitution_slider.setValue(default.restitution)
        self.cohesion_slider.setValue(default.cohesion)
        self.viscosity_slider.setValue(default.viscosity)
        self.gravity_slider.setValue(default.gravity_scale)
        self.size_slider.setValue(default.particle_size)
        
    def get_properties(self) -> SandProperties:
        """Retourne les propriétés actuelles"""
        return self.properties


class EmitterPanel(QWidget):
    """Panneau de contrôle de l'émetteur de particules"""
    
    def __init__(self, gl_widget: SandGLWidget, parent=None):
        super().__init__(parent)
        self.gl_widget = gl_widget
        self._setup_ui()
        
    def _setup_ui(self):
        """Configure l'interface"""
        layout = QVBoxLayout(self)
        
        # Activation
        self.active_check = QCheckBox("Émetteur actif (E)")
        self.active_check.toggled.connect(
            lambda v: setattr(self.gl_widget, 'emitter_active', v)
        )
        layout.addWidget(self.active_check)
        
        # Type de sable
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type de sable:"))
        self.type_combo = QComboBox()
        for sand_type in SandType:
            self.type_combo.addItem(sand_type.value, sand_type)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo, stretch=1)
        layout.addLayout(type_layout)
        
        # Taux d'émission
        self.rate_slider = PropertySlider("Particules/frame", 1, 50, 10, decimals=0)
        self.rate_slider.valueChanged.connect(
            lambda v: setattr(self.gl_widget, 'emitter_rate', int(v))
        )
        layout.addWidget(self.rate_slider)
        
        # Dispersion
        self.spread_slider = PropertySlider("Dispersion", 0.5, 10.0, 2.0)
        self.spread_slider.valueChanged.connect(
            lambda v: setattr(self.gl_widget, 'emitter_spread', v)
        )
        layout.addWidget(self.spread_slider)
        
        # Position
        pos_group = QGroupBox("Position de l'émetteur")
        pos_layout = QVBoxLayout(pos_group)
        
        self.pos_x = PropertySlider("X", -25, 25, 0)
        self.pos_x.valueChanged.connect(self._on_position_changed)
        pos_layout.addWidget(self.pos_x)
        
        self.pos_y = PropertySlider("Y", 10, 50, 40)
        self.pos_y.valueChanged.connect(self._on_position_changed)
        pos_layout.addWidget(self.pos_y)
        
        self.pos_z = PropertySlider("Z", -25, 25, 0)
        self.pos_z.valueChanged.connect(self._on_position_changed)
        pos_layout.addWidget(self.pos_z)
        
        layout.addWidget(pos_group)
        
        # Actions rapides
        action_group = QGroupBox("Actions rapides")
        action_layout = QVBoxLayout(action_group)
        
        burst_layout = QHBoxLayout()
        self.burst_count = QSpinBox()
        self.burst_count.setRange(10, 1000)
        self.burst_count.setValue(100)
        burst_layout.addWidget(QLabel("Quantité:"))
        burst_layout.addWidget(self.burst_count)
        action_layout.addLayout(burst_layout)
        
        burst_btn = QPushButton("💥 Burst")
        burst_btn.clicked.connect(self._emit_burst)
        action_layout.addWidget(burst_btn)
        
        rain_btn = QPushButton("🌧️ Pluie de sable")
        rain_btn.clicked.connect(self._emit_rain)
        action_layout.addWidget(rain_btn)
        
        layout.addWidget(action_group)
        
        # Presets
        preset_group = QGroupBox("Presets de scènes")
        preset_layout = QVBoxLayout(preset_group)
        
        self.preset_combo = QComboBox()
        for name in get_preset_names():
            self.preset_combo.addItem(name)
        preset_layout.addWidget(self.preset_combo)
        
        load_preset_btn = QPushButton("🎬 Charger le preset")
        load_preset_btn.clicked.connect(self._load_preset)
        preset_layout.addWidget(load_preset_btn)
        
        layout.addWidget(preset_group)
        
        layout.addStretch()
        
    def _on_type_changed(self, index):
        """Callback changement de type"""
        self.gl_widget.emitter_type = self.type_combo.currentData()
        
    def _on_position_changed(self):
        """Callback changement de position"""
        self.gl_widget.emitter_position = np.array([
            self.pos_x.value(),
            self.pos_y.value(),
            self.pos_z.value()
        ], dtype=np.float32)
        
    def _emit_burst(self):
        """Émet un burst de particules"""
        self.gl_widget.physics.add_particles_burst(
            self.gl_widget.emitter_position,
            self.burst_count.value(),
            self.gl_widget.emitter_spread,
            self.gl_widget.emitter_type
        )
        self.gl_widget.update()
        
    def _emit_rain(self):
        """Émet une pluie de particules sur toute la zone"""
        for _ in range(self.burst_count.value()):
            pos = np.array([
                np.random.uniform(-20, 20),
                np.random.uniform(35, 50),
                np.random.uniform(-20, 20)
            ], dtype=np.float32)
            vel = np.array([0.0, -2.0, 0.0], dtype=np.float32)
            self.gl_widget.physics.add_particle(pos, vel, self.gl_widget.emitter_type)
        self.gl_widget.update()
        
    def _load_preset(self):
        """Charge un preset de scène"""
        preset_name = self.preset_combo.currentText()
        apply_preset(self.gl_widget.physics, preset_name)
        self.gl_widget.update()


class RenderPanel(QWidget):
    """Panneau de contrôle du rendu"""
    
    def __init__(self, gl_widget: SandGLWidget, parent=None):
        super().__init__(parent)
        self.gl_widget = gl_widget
        self._setup_ui()
        
    def _setup_ui(self):
        """Configure l'interface"""
        layout = QVBoxLayout(self)
        
        # Mode de rendu
        mode_group = QGroupBox("Mode de rendu")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Plat", 0)
        self.mode_combo.addItem("Sphère éclairée", 1)
        self.mode_combo.addItem("Glow", 2)
        self.mode_combo.setCurrentIndex(1)
        self.mode_combo.currentIndexChanged.connect(
            lambda i: setattr(self.gl_widget.renderer, 'shading_mode', 
                            self.mode_combo.currentData())
        )
        mode_layout.addWidget(self.mode_combo)
        
        layout.addWidget(mode_group)
        
        # Échelle des particules
        self.scale_slider = PropertySlider("Échelle particules", 0.5, 3.0, 1.0)
        self.scale_slider.valueChanged.connect(
            lambda v: setattr(self.gl_widget.renderer, 'global_particle_scale', v)
        )
        layout.addWidget(self.scale_slider)
        
        # Options d'affichage
        display_group = QGroupBox("Affichage")
        display_layout = QVBoxLayout(display_group)
        
        self.grid_check = QCheckBox("Afficher la grille")
        self.grid_check.setChecked(True)
        self.grid_check.toggled.connect(
            lambda v: setattr(self.gl_widget.renderer, 'show_grid', v)
        )
        display_layout.addWidget(self.grid_check)
        
        self.bounds_check = QCheckBox("Afficher les limites")
        self.bounds_check.setChecked(True)
        self.bounds_check.toggled.connect(
            lambda v: setattr(self.gl_widget.renderer, 'show_bounds', v)
        )
        display_layout.addWidget(self.bounds_check)
        
        layout.addWidget(display_group)
        
        # Éclairage
        light_group = QGroupBox("Éclairage")
        light_layout = QVBoxLayout(light_group)
        
        self.ambient_slider = PropertySlider("Ambiant", 0.0, 1.0, 0.3)
        self.ambient_slider.valueChanged.connect(
            lambda v: setattr(self.gl_widget.renderer, 'ambient_strength', v)
        )
        light_layout.addWidget(self.ambient_slider)
        
        # Couleur de lumière
        light_color_layout = QHBoxLayout()
        light_color_layout.addWidget(QLabel("Couleur lumière:"))
        self.light_color_btn = ColorButton((1.0, 1.0, 0.95))
        self.light_color_btn.colorChanged.connect(self._on_light_color_changed)
        light_color_layout.addWidget(self.light_color_btn, stretch=1)
        light_layout.addLayout(light_color_layout)
        
        layout.addWidget(light_group)
        
        # Couleurs de fond
        bg_group = QGroupBox("Arrière-plan")
        bg_layout = QVBoxLayout(bg_group)
        
        bg_color_layout = QHBoxLayout()
        bg_color_layout.addWidget(QLabel("Couleur:"))
        self.bg_color_btn = ColorButton((0.1, 0.1, 0.15))
        self.bg_color_btn.colorChanged.connect(self._on_bg_color_changed)
        bg_color_layout.addWidget(self.bg_color_btn, stretch=1)
        bg_layout.addLayout(bg_color_layout)
        
        grid_color_layout = QHBoxLayout()
        grid_color_layout.addWidget(QLabel("Grille:"))
        self.grid_color_btn = ColorButton((0.5, 0.5, 0.6))
        self.grid_color_btn.colorChanged.connect(self._on_grid_color_changed)
        grid_color_layout.addWidget(self.grid_color_btn, stretch=1)
        bg_layout.addLayout(grid_color_layout)
        
        layout.addWidget(bg_group)
        
        # Caméra
        cam_group = QGroupBox("Caméra")
        cam_layout = QVBoxLayout(cam_group)
        
        reset_cam_btn = QPushButton("Réinitialiser la caméra")
        reset_cam_btn.clicked.connect(self._reset_camera)
        cam_layout.addWidget(reset_cam_btn)
        
        self.fov_slider = PropertySlider("FOV", 30, 90, 45, decimals=0)
        self.fov_slider.valueChanged.connect(
            lambda v: setattr(self.gl_widget.renderer.camera, 'fov', v)
        )
        cam_layout.addWidget(self.fov_slider)
        
        layout.addWidget(cam_group)
        
        layout.addStretch()
        
    def _on_light_color_changed(self, color: tuple):
        """Callback changement couleur lumière"""
        self.gl_widget.renderer.light_color = np.array(color, dtype=np.float32)
        
    def _on_bg_color_changed(self, color: tuple):
        """Callback changement couleur fond"""
        self.gl_widget.renderer.background_color = color
        
    def _on_grid_color_changed(self, color: tuple):
        """Callback changement couleur grille"""
        self.gl_widget.renderer.grid_color = np.array(color, dtype=np.float32)
        
    def _reset_camera(self):
        """Réinitialise la caméra"""
        cam = self.gl_widget.renderer.camera
        cam.target = np.array([0.0, 10.0, 0.0], dtype=np.float32)
        cam.distance = 60.0
        cam.pitch = -30.0
        cam.yaw = 45.0
        self.gl_widget.update()


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏖️ Simulation de Sable 3D")
        self.setMinimumSize(1200, 800)
        
        self._setup_ui()
        self._setup_toolbar()
        self._setup_statusbar()
        self._setup_timer()
        
    def _setup_ui(self):
        """Configure l'interface principale"""
        # Widget central avec splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)
        
        # Widget OpenGL
        self.gl_widget = SandGLWidget()
        splitter.addWidget(self.gl_widget)
        
        # Panneau de contrôle (tabs)
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        tabs = QTabWidget()
        
        # Onglet Émetteur
        emitter_scroll = QScrollArea()
        emitter_scroll.setWidgetResizable(True)
        self.emitter_panel = EmitterPanel(self.gl_widget)
        emitter_scroll.setWidget(self.emitter_panel)
        tabs.addTab(emitter_scroll, "🎯 Émetteur")
        
        # Onglet Physique
        physics_scroll = QScrollArea()
        physics_scroll.setWidgetResizable(True)
        self.physics_panel = PhysicsControlPanel(self.gl_widget)
        physics_scroll.setWidget(self.physics_panel)
        tabs.addTab(physics_scroll, "⚙️ Physique")
        
        # Onglets par type de sable
        self.sand_panels = {}
        for sand_type in SandType:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            panel = SandTypePanel(sand_type, self.gl_widget)
            scroll.setWidget(panel)
            self.sand_panels[sand_type] = panel
            tabs.addTab(scroll, f"🏝️ {sand_type.value}")
        
        # Onglet Rendu
        render_scroll = QScrollArea()
        render_scroll.setWidgetResizable(True)
        self.render_panel = RenderPanel(self.gl_widget)
        render_scroll.setWidget(self.render_panel)
        tabs.addTab(render_scroll, "🎨 Rendu")
        
        control_layout.addWidget(tabs)
        splitter.addWidget(control_widget)
        
        # Proportions du splitter
        splitter.setSizes([800, 400])
        
    def _setup_toolbar(self):
        """Configure la barre d'outils"""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Bouton Play/Pause
        self.play_action = QAction("▶️ Démarrer", self)
        self.play_action.setShortcut("Space")
        self.play_action.triggered.connect(self._toggle_simulation)
        toolbar.addAction(self.play_action)
        
        # Bouton Reset
        reset_action = QAction("🔄 Réinitialiser", self)
        reset_action.setShortcut("R")
        reset_action.triggered.connect(self._reset_simulation)
        toolbar.addAction(reset_action)
        
        toolbar.addSeparator()
        
        # Boutons rapides pour ajouter des particules
        for sand_type in [SandType.NORMAL, SandType.REBONDISSANT, SandType.VISQUEUX]:
            action = QAction(f"+ {sand_type.value}", self)
            action.triggered.connect(lambda checked, t=sand_type: self._quick_add(t))
            toolbar.addAction(action)
            
        toolbar.addSeparator()
        
        # Info
        help_action = QAction("❓ Aide", self)
        help_action.triggered.connect(self._show_help)
        toolbar.addAction(help_action)
        
    def _setup_statusbar(self):
        """Configure la barre de statut"""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        self.particle_label = QLabel("Particules: 0")
        self.fps_label = QLabel("FPS: 0")
        self.status_label = QLabel("⏸️ En pause")
        
        self.statusBar.addWidget(self.particle_label)
        self.statusBar.addWidget(self.fps_label)
        self.statusBar.addPermanentWidget(self.status_label)
        
    def _setup_timer(self):
        """Configure le timer pour les mises à jour d'interface"""
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self._update_status)
        self.ui_timer.start(100)  # 10 FPS pour l'UI
        
        self.last_frame_time = 0
        self.frame_count = 0
        
    def _toggle_simulation(self):
        """Bascule la simulation"""
        self.gl_widget.toggle_simulation()
        
        if self.gl_widget.is_running:
            self.play_action.setText("⏸️ Pause")
            self.status_label.setText("▶️ En cours")
        else:
            self.play_action.setText("▶️ Démarrer")
            self.status_label.setText("⏸️ En pause")
            
    def _reset_simulation(self):
        """Réinitialise la simulation"""
        self.gl_widget.reset_simulation()
        
    def _quick_add(self, sand_type: SandType):
        """Ajoute rapidement des particules"""
        self.gl_widget.physics.add_particles_burst(
            np.array([0.0, 35.0, 0.0], dtype=np.float32),
            50,
            5.0,
            sand_type
        )
        self.gl_widget.update()
        
    def _update_status(self):
        """Met à jour la barre de statut"""
        stats = self.gl_widget.physics.get_stats()
        self.particle_label.setText(f"Particules: {stats['particle_count']}")
        
        # Calcul FPS approximatif
        if self.gl_widget.is_running:
            self.frame_count += 1
            import time
            current = time.time()
            if current - self.last_frame_time >= 1.0:
                fps = self.frame_count / (current - self.last_frame_time)
                self.fps_label.setText(f"FPS: {fps:.0f}")
                self.frame_count = 0
                self.last_frame_time = current
                
    def _show_help(self):
        """Affiche l'aide"""
        help_text = """
<h2>🏖️ Simulation de Sable 3D</h2>

<h3>Contrôles de la caméra:</h3>
<ul>
<li><b>Clic gauche + glisser:</b> Orbite autour de la scène</li>
<li><b>Clic milieu + glisser:</b> Pan (déplacement)</li>
<li><b>Clic droit + glisser:</b> Zoom</li>
<li><b>Molette:</b> Zoom avant/arrière</li>
</ul>

<h3>Raccourcis clavier:</h3>
<ul>
<li><b>Espace:</b> Play/Pause</li>
<li><b>R:</b> Réinitialiser</li>
<li><b>E:</b> Activer/Désactiver l'émetteur</li>
</ul>

<h3>Types de sable:</h3>
<ul>
<li><b>Normal:</b> Comportement standard</li>
<li><b>Lourd:</b> Plus dense, tombe plus vite</li>
<li><b>Léger:</b> Flotte presque, très mobile</li>
<li><b>Rebondissant:</b> Rebondit sur les surfaces</li>
<li><b>Visqueux:</b> Colle et forme des amas</li>
<li><b>Explosif:</b> Comportement énergétique</li>
</ul>

<p>Modifiez les propriétés en temps réel dans les onglets!</p>
"""
        QMessageBox.about(self, "Aide - Simulation de Sable", help_text)
        
    def closeEvent(self, event):
        """Nettoyage à la fermeture"""
        self.gl_widget.stop_simulation()
        self.gl_widget.renderer.cleanup()
        event.accept()


def main():
    """Point d'entrée de l'application"""
    app = QApplication(sys.argv)
    
    # Style sombre
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
