"""
Presets de Scènes pour la Simulation de Sable
=============================================
Scènes préconfigurées pour démontrer les capacités de la simulation.
"""

import numpy as np
from sand_physics import PhysicsEngine, SandType


def create_pyramid(physics: PhysicsEngine, center: np.ndarray, 
                   base_size: int = 10, sand_type: SandType = SandType.NORMAL):
    """Crée une pyramide de sable"""
    height = base_size
    for level in range(height):
        size = base_size - level
        y = center[1] + level * 0.8
        for x in range(-size // 2, size // 2 + 1):
            for z in range(-size // 2, size // 2 + 1):
                pos = np.array([
                    center[0] + x * 0.9,
                    y,
                    center[2] + z * 0.9
                ], dtype=np.float32)
                physics.add_particle(pos, np.zeros(3), sand_type)


def create_wall(physics: PhysicsEngine, start: np.ndarray, 
                width: int, height: int, sand_type: SandType = SandType.LOURD):
    """Crée un mur de sable"""
    for y in range(height):
        for x in range(width):
            pos = np.array([
                start[0] + x * 0.9,
                start[1] + y * 0.9,
                start[2]
            ], dtype=np.float32)
            physics.add_particle(pos, np.zeros(3), sand_type)


def create_cube(physics: PhysicsEngine, center: np.ndarray, 
                size: int = 5, sand_type: SandType = SandType.NORMAL):
    """Crée un cube de sable"""
    half = size // 2
    for x in range(-half, half + 1):
        for y in range(size):
            for z in range(-half, half + 1):
                pos = np.array([
                    center[0] + x * 0.9,
                    center[1] + y * 0.9,
                    center[2] + z * 0.9
                ], dtype=np.float32)
                physics.add_particle(pos, np.zeros(3), sand_type)


def create_sphere(physics: PhysicsEngine, center: np.ndarray, 
                  radius: int = 5, sand_type: SandType = SandType.REBONDISSANT):
    """Crée une sphère de sable"""
    for x in range(-radius, radius + 1):
        for y in range(-radius, radius + 1):
            for z in range(-radius, radius + 1):
                dist = np.sqrt(x*x + y*y + z*z)
                if dist <= radius:
                    pos = np.array([
                        center[0] + x * 0.9,
                        center[1] + radius + y * 0.9,
                        center[2] + z * 0.9
                    ], dtype=np.float32)
                    physics.add_particle(pos, np.zeros(3), sand_type)


def create_rainbow_layers(physics: PhysicsEngine, center: np.ndarray,
                         width: int = 20, height: int = 15):
    """Crée des couches de sable coloré (arc-en-ciel)"""
    types = [SandType.NORMAL, SandType.LOURD, SandType.LEGER, 
             SandType.REBONDISSANT, SandType.VISQUEUX, SandType.EXPLOSIF]
    
    layer_height = height // len(types)
    
    for idx, sand_type in enumerate(types):
        y_start = center[1] + idx * layer_height * 0.9
        for y in range(layer_height):
            for x in range(-width // 2, width // 2):
                pos = np.array([
                    center[0] + x * 0.9,
                    y_start + y * 0.9,
                    center[2]
                ], dtype=np.float32)
                physics.add_particle(pos, np.zeros(3), sand_type)


def create_fountain(physics: PhysicsEngine, center: np.ndarray,
                   count: int = 200, sand_type: SandType = SandType.LEGER):
    """Crée une fontaine de sable"""
    for _ in range(count):
        # Angle aléatoire
        angle = np.random.uniform(0, 2 * np.pi)
        speed = np.random.uniform(5, 15)
        
        pos = center.copy()
        vel = np.array([
            np.cos(angle) * speed * 0.3,
            speed,
            np.sin(angle) * speed * 0.3
        ], dtype=np.float32)
        
        physics.add_particle(pos, vel, sand_type)


def create_explosion(physics: PhysicsEngine, center: np.ndarray,
                    count: int = 300, sand_type: SandType = SandType.EXPLOSIF):
    """Crée une explosion de sable"""
    for _ in range(count):
        # Direction aléatoire
        theta = np.random.uniform(0, np.pi)
        phi = np.random.uniform(0, 2 * np.pi)
        speed = np.random.uniform(10, 25)
        
        vel = np.array([
            speed * np.sin(theta) * np.cos(phi),
            speed * np.sin(theta) * np.sin(phi) + 5,
            speed * np.cos(theta)
        ], dtype=np.float32)
        
        physics.add_particle(center.copy(), vel, sand_type)


def create_hourglass(physics: PhysicsEngine, center: np.ndarray,
                    radius: int = 8, sand_type: SandType = SandType.NORMAL):
    """Crée la forme supérieure d'un sablier"""
    for y in range(radius * 2):
        # Rayon qui diminue vers le bas
        current_radius = max(1, radius - abs(y - radius) // 2)
        for x in range(-current_radius, current_radius + 1):
            for z in range(-current_radius, current_radius + 1):
                dist = np.sqrt(x*x + z*z)
                if dist <= current_radius:
                    pos = np.array([
                        center[0] + x * 0.9,
                        center[1] + y * 0.9,
                        center[2] + z * 0.9
                    ], dtype=np.float32)
                    physics.add_particle(pos, np.zeros(3), sand_type)


# Dictionnaire des presets
PRESETS = {
    "Pyramide": lambda p: create_pyramid(p, np.array([0, 0.5, 0], dtype=np.float32), 
                                         base_size=12, sand_type=SandType.NORMAL),
    "Cube flottant": lambda p: create_cube(p, np.array([0, 25, 0], dtype=np.float32), 
                                           size=8, sand_type=SandType.LOURD),
    "Sphère rebondissante": lambda p: create_sphere(p, np.array([0, 30, 0], dtype=np.float32), 
                                                    radius=6, sand_type=SandType.REBONDISSANT),
    "Arc-en-ciel": lambda p: create_rainbow_layers(p, np.array([0, 0.5, 0], dtype=np.float32)),
    "Fontaine": lambda p: create_fountain(p, np.array([0, 5, 0], dtype=np.float32)),
    "Explosion": lambda p: create_explosion(p, np.array([0, 20, 0], dtype=np.float32)),
    "Sablier": lambda p: create_hourglass(p, np.array([0, 25, 0], dtype=np.float32)),
    "Mur": lambda p: create_wall(p, np.array([-10, 0.5, 0], dtype=np.float32), 
                                 width=20, height=15),
    "Double cube": lambda p: [
        create_cube(p, np.array([-8, 25, 0], dtype=np.float32), 5, SandType.LOURD),
        create_cube(p, np.array([8, 25, 0], dtype=np.float32), 5, SandType.LEGER)
    ],
    "Chaos": lambda p: [
        create_sphere(p, np.array([-10, 30, -10], dtype=np.float32), 4, SandType.REBONDISSANT),
        create_sphere(p, np.array([10, 35, 10], dtype=np.float32), 4, SandType.VISQUEUX),
        create_cube(p, np.array([0, 40, 0], dtype=np.float32), 5, SandType.EXPLOSIF),
    ]
}


def apply_preset(physics: PhysicsEngine, preset_name: str):
    """Applique un preset à la simulation"""
    if preset_name in PRESETS:
        physics.clear_particles()
        PRESETS[preset_name](physics)
        return True
    return False


def get_preset_names() -> list:
    """Retourne la liste des noms de presets"""
    return list(PRESETS.keys())
