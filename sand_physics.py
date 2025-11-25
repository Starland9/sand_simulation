"""
Simulation de Sable Coloré 3D
=============================
Un projet complet de simulation de particules de sable avec:
- Rendu 3D OpenGL avec shaders
- Physique réaliste avec collisions
- Interface graphique PyQt6
- Propriétés physiques ajustables en temps réel
- Différents types de sable avec comportements uniques

Auteur: GitHub Copilot
"""

import sys
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum
import time


class SandType(Enum):
    """Types de sable avec différentes propriétés"""
    NORMAL = "Normal"
    LOURD = "Lourd"
    LEGER = "Léger"
    REBONDISSANT = "Rebondissant"
    VISQUEUX = "Visqueux"
    EXPLOSIF = "Explosif"


@dataclass
class SandProperties:
    """Propriétés physiques d'un type de sable"""
    name: str
    color: Tuple[float, float, float]  # RGB normalisé
    mass: float = 1.0
    friction: float = 0.3
    restitution: float = 0.2  # Rebond
    cohesion: float = 0.0  # Force d'attraction entre particules
    viscosity: float = 0.0  # Résistance au mouvement
    gravity_scale: float = 1.0
    particle_size: float = 0.5
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'color': self.color,
            'mass': self.mass,
            'friction': self.friction,
            'restitution': self.restitution,
            'cohesion': self.cohesion,
            'viscosity': self.viscosity,
            'gravity_scale': self.gravity_scale,
            'particle_size': self.particle_size
        }


# Propriétés par défaut pour chaque type de sable
DEFAULT_SAND_PROPERTIES = {
    SandType.NORMAL: SandProperties(
        name="Sable Normal",
        color=(0.96, 0.87, 0.70),
        mass=1.0,
        friction=0.4,
        restitution=0.1,
        cohesion=0.0,
        viscosity=0.0,
        gravity_scale=1.0,
        particle_size=0.5
    ),
    SandType.LOURD: SandProperties(
        name="Sable Lourd",
        color=(0.4, 0.35, 0.3),
        mass=3.0,
        friction=0.6,
        restitution=0.05,
        cohesion=0.1,
        viscosity=0.1,
        gravity_scale=1.5,
        particle_size=0.6
    ),
    SandType.LEGER: SandProperties(
        name="Sable Léger",
        color=(1.0, 0.98, 0.9),
        mass=0.3,
        friction=0.2,
        restitution=0.3,
        cohesion=0.0,
        viscosity=0.0,
        gravity_scale=0.5,
        particle_size=0.4
    ),
    SandType.REBONDISSANT: SandProperties(
        name="Sable Rebondissant",
        color=(0.2, 0.8, 0.4),
        mass=0.8,
        friction=0.2,
        restitution=0.8,
        cohesion=0.0,
        viscosity=0.0,
        gravity_scale=1.0,
        particle_size=0.5
    ),
    SandType.VISQUEUX: SandProperties(
        name="Sable Visqueux",
        color=(0.6, 0.3, 0.1),
        mass=1.5,
        friction=0.8,
        restitution=0.0,
        cohesion=0.5,
        viscosity=0.7,
        gravity_scale=0.8,
        particle_size=0.55
    ),
    SandType.EXPLOSIF: SandProperties(
        name="Sable Explosif",
        color=(1.0, 0.3, 0.1),
        mass=1.0,
        friction=0.3,
        restitution=0.5,
        cohesion=0.0,
        viscosity=0.0,
        gravity_scale=1.0,
        particle_size=0.45
    )
}


@dataclass
class Particle:
    """Une particule de sable"""
    position: np.ndarray  # [x, y, z]
    velocity: np.ndarray  # [vx, vy, vz]
    sand_type: SandType
    properties: SandProperties
    age: float = 0.0
    is_active: bool = True
    
    def __post_init__(self):
        self.position = np.array(self.position, dtype=np.float32)
        self.velocity = np.array(self.velocity, dtype=np.float32)


class SpatialGrid:
    """Grille spatiale pour optimiser la détection de collisions"""
    
    def __init__(self, cell_size: float = 1.0, bounds: Tuple[float, float, float] = (50, 50, 50)):
        self.cell_size = cell_size
        self.bounds = bounds
        self.grid = {}
        
    def _get_cell(self, position: np.ndarray) -> Tuple[int, int, int]:
        """Obtient l'index de cellule pour une position"""
        return (
            int(position[0] / self.cell_size),
            int(position[1] / self.cell_size),
            int(position[2] / self.cell_size)
        )
    
    def clear(self):
        """Vide la grille"""
        self.grid.clear()
        
    def insert(self, particle_idx: int, position: np.ndarray):
        """Insère une particule dans la grille"""
        cell = self._get_cell(position)
        if cell not in self.grid:
            self.grid[cell] = []
        self.grid[cell].append(particle_idx)
        
    def get_neighbors(self, position: np.ndarray) -> List[int]:
        """Obtient les indices des particules voisines"""
        cell = self._get_cell(position)
        neighbors = []
        
        # Vérifie les 27 cellules adjacentes (3x3x3)
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                for dz in range(-1, 2):
                    neighbor_cell = (cell[0] + dx, cell[1] + dy, cell[2] + dz)
                    if neighbor_cell in self.grid:
                        neighbors.extend(self.grid[neighbor_cell])
                        
        return neighbors


class PhysicsEngine:
    """Moteur physique pour la simulation de sable"""
    
    def __init__(self):
        self.particles: List[Particle] = []
        self.gravity = np.array([0.0, -9.81, 0.0], dtype=np.float32)
        self.bounds = np.array([
            [-25, 0, -25],  # Min bounds
            [25, 50, 25]    # Max bounds
        ], dtype=np.float32)
        self.spatial_grid = SpatialGrid(cell_size=1.5)
        self.collision_damping = 0.8
        self.time_step = 1/60
        self.sub_steps = 2
        
        # Paramètres ajustables
        self.global_gravity_scale = 1.0
        self.global_friction = 1.0
        self.enable_collisions = True
        self.enable_cohesion = True
        
    def add_particle(self, position: np.ndarray, velocity: np.ndarray, 
                     sand_type: SandType = SandType.NORMAL,
                     custom_properties: Optional[SandProperties] = None) -> Particle:
        """Ajoute une nouvelle particule"""
        props = custom_properties or DEFAULT_SAND_PROPERTIES[sand_type]
        particle = Particle(
            position=position.copy(),
            velocity=velocity.copy(),
            sand_type=sand_type,
            properties=props
        )
        self.particles.append(particle)
        return particle
    
    def add_particles_burst(self, center: np.ndarray, count: int, 
                            spread: float, sand_type: SandType,
                            initial_velocity: np.ndarray = None):
        """Ajoute un groupe de particules"""
        if initial_velocity is None:
            initial_velocity = np.array([0.0, 0.0, 0.0])
            
        for _ in range(count):
            offset = (np.random.rand(3) - 0.5) * 2 * spread
            pos = center + offset
            vel = initial_velocity + (np.random.rand(3) - 0.5) * 2
            self.add_particle(pos, vel, sand_type)
            
    def clear_particles(self):
        """Supprime toutes les particules"""
        self.particles.clear()
        
    def update(self, dt: float = None):
        """Met à jour la simulation"""
        if dt is None:
            dt = self.time_step
            
        sub_dt = dt / self.sub_steps
        
        for _ in range(self.sub_steps):
            self._update_step(sub_dt)
            
    def _update_step(self, dt: float):
        """Une étape de mise à jour"""
        # Reconstruit la grille spatiale
        self.spatial_grid.clear()
        for i, p in enumerate(self.particles):
            if p.is_active:
                self.spatial_grid.insert(i, p.position)
        
        # Met à jour chaque particule
        for i, particle in enumerate(self.particles):
            if not particle.is_active:
                continue
                
            # Applique la gravité
            gravity_force = (self.gravity * self.global_gravity_scale * 
                           particle.properties.gravity_scale)
            particle.velocity += gravity_force * dt
            
            # Applique la viscosité
            if particle.properties.viscosity > 0:
                particle.velocity *= (1.0 - particle.properties.viscosity * dt)
            
            # Détection et réponse aux collisions entre particules
            if self.enable_collisions:
                self._handle_particle_collisions(i, particle, dt)
            
            # Cohésion entre particules similaires
            if self.enable_cohesion and particle.properties.cohesion > 0:
                self._apply_cohesion(i, particle, dt)
            
            # Met à jour la position
            particle.position += particle.velocity * dt
            
            # Collisions avec les limites
            self._handle_boundary_collision(particle)
            
            # Met à jour l'âge
            particle.age += dt
            
    def _handle_particle_collisions(self, idx: int, particle: Particle, dt: float):
        """Gère les collisions entre particules"""
        neighbors = self.spatial_grid.get_neighbors(particle.position)
        particle_radius = particle.properties.particle_size
        
        for neighbor_idx in neighbors:
            if neighbor_idx == idx:
                continue
                
            other = self.particles[neighbor_idx]
            if not other.is_active:
                continue
                
            # Calcul de la distance
            diff = particle.position - other.position
            dist_sq = np.dot(diff, diff)
            min_dist = particle_radius + other.properties.particle_size
            
            if dist_sq < min_dist * min_dist and dist_sq > 0.0001:
                dist = np.sqrt(dist_sq)
                normal = diff / dist
                overlap = min_dist - dist
                
                # Masses relatives
                total_mass = particle.properties.mass + other.properties.mass
                mass_ratio1 = other.properties.mass / total_mass
                mass_ratio2 = particle.properties.mass / total_mass
                
                # Séparation des particules
                particle.position += normal * overlap * mass_ratio1 * 0.5
                other.position -= normal * overlap * mass_ratio2 * 0.5
                
                # Réponse de collision (impulsion)
                relative_vel = particle.velocity - other.velocity
                vel_along_normal = np.dot(relative_vel, normal)
                
                if vel_along_normal > 0:
                    continue
                    
                # Coefficient de restitution moyen
                restitution = (particle.properties.restitution + 
                             other.properties.restitution) * 0.5
                
                # Calcul de l'impulsion
                j = -(1 + restitution) * vel_along_normal
                j /= (1/particle.properties.mass + 1/other.properties.mass)
                
                impulse = j * normal
                particle.velocity += impulse / particle.properties.mass
                other.velocity -= impulse / other.properties.mass
                
                # Friction
                tangent = relative_vel - vel_along_normal * normal
                tangent_length = np.linalg.norm(tangent)
                if tangent_length > 0.001:
                    tangent = tangent / tangent_length
                    friction = (particle.properties.friction + 
                              other.properties.friction) * 0.5 * self.global_friction
                    friction_impulse = friction * j * tangent
                    particle.velocity -= friction_impulse / particle.properties.mass * 0.5
                    other.velocity += friction_impulse / other.properties.mass * 0.5
                    
    def _apply_cohesion(self, idx: int, particle: Particle, dt: float):
        """Applique la force de cohésion entre particules similaires"""
        neighbors = self.spatial_grid.get_neighbors(particle.position)
        cohesion_radius = particle.properties.particle_size * 4
        
        for neighbor_idx in neighbors:
            if neighbor_idx == idx:
                continue
                
            other = self.particles[neighbor_idx]
            if not other.is_active or other.sand_type != particle.sand_type:
                continue
                
            diff = other.position - particle.position
            dist_sq = np.dot(diff, diff)
            
            if dist_sq < cohesion_radius * cohesion_radius and dist_sq > 0.01:
                dist = np.sqrt(dist_sq)
                direction = diff / dist
                
                # Force de cohésion (diminue avec la distance)
                strength = particle.properties.cohesion * (1 - dist / cohesion_radius)
                particle.velocity += direction * strength * dt
                
    def _handle_boundary_collision(self, particle: Particle):
        """Gère les collisions avec les limites du monde"""
        radius = particle.properties.particle_size
        restitution = particle.properties.restitution
        friction = particle.properties.friction * self.global_friction
        
        for axis in range(3):
            # Limite inférieure
            if particle.position[axis] < self.bounds[0][axis] + radius:
                particle.position[axis] = self.bounds[0][axis] + radius
                particle.velocity[axis] *= -restitution
                # Applique friction sur les autres axes
                for other_axis in range(3):
                    if other_axis != axis:
                        particle.velocity[other_axis] *= (1 - friction)
                        
            # Limite supérieure
            elif particle.position[axis] > self.bounds[1][axis] - radius:
                particle.position[axis] = self.bounds[1][axis] - radius
                particle.velocity[axis] *= -restitution
                for other_axis in range(3):
                    if other_axis != axis:
                        particle.velocity[other_axis] *= (1 - friction)
                        
    def get_particle_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Retourne les données des particules pour le rendu"""
        if not self.particles:
            return (np.array([], dtype=np.float32),
                   np.array([], dtype=np.float32),
                   np.array([], dtype=np.float32))
            
        positions = []
        colors = []
        sizes = []
        
        for p in self.particles:
            if p.is_active:
                positions.extend(p.position)
                colors.extend(p.properties.color)
                sizes.append(p.properties.particle_size)
                
        return (np.array(positions, dtype=np.float32),
               np.array(colors, dtype=np.float32),
               np.array(sizes, dtype=np.float32))
    
    def get_stats(self) -> dict:
        """Retourne les statistiques de la simulation"""
        active_count = sum(1 for p in self.particles if p.is_active)
        
        if active_count == 0:
            return {
                'particle_count': 0,
                'avg_velocity': 0.0,
                'avg_height': 0.0
            }
            
        velocities = [np.linalg.norm(p.velocity) for p in self.particles if p.is_active]
        heights = [p.position[1] for p in self.particles if p.is_active]
        
        return {
            'particle_count': active_count,
            'avg_velocity': np.mean(velocities) if velocities else 0.0,
            'avg_height': np.mean(heights) if heights else 0.0
        }
