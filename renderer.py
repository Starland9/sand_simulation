"""
Rendu 3D OpenGL pour la Simulation de Sable
==========================================
Utilise des shaders modernes pour un rendu efficace des particules.
Support des ombres, de l'éclairage et des effets visuels.
"""

import numpy as np
from OpenGL.GL import *
from OpenGL.GL import shaders
import pyrr
from typing import Tuple, Optional
import ctypes


# Vertex Shader pour les particules (utilise geometry shader pour les sphères)
PARTICLE_VERTEX_SHADER = """
#version 330 core

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 color;
layout(location = 2) in float size;

out vec3 vColor;
out float vSize;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform float globalScale;

void main() {
    vColor = color;
    vSize = size * globalScale;
    gl_Position = view * model * vec4(position, 1.0);
    gl_PointSize = vSize * 500.0 / gl_Position.z;
}
"""

# Fragment Shader pour les particules (sphères avec éclairage)
PARTICLE_FRAGMENT_SHADER = """
#version 330 core

in vec3 vColor;
in float vSize;

out vec4 FragColor;

uniform vec3 lightDir;
uniform vec3 lightColor;
uniform float ambientStrength;
uniform vec3 viewPos;
uniform int shadingMode;  // 0: flat, 1: sphere, 2: glow

void main() {
    // Calcule la normale de la "sphère" à partir des coordonnées du point
    vec2 coord = gl_PointCoord * 2.0 - 1.0;
    float dist = dot(coord, coord);
    
    if (dist > 1.0) {
        discard;
    }
    
    vec3 normal = vec3(coord.x, coord.y, sqrt(1.0 - dist));
    
    // Éclairage
    vec3 ambient = ambientStrength * lightColor;
    
    float diff = max(dot(normal, normalize(lightDir)), 0.0);
    vec3 diffuse = diff * lightColor;
    
    // Spéculaire
    vec3 viewDir = vec3(0.0, 0.0, 1.0);
    vec3 reflectDir = reflect(-normalize(lightDir), normal);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32.0);
    vec3 specular = 0.5 * spec * lightColor;
    
    vec3 result;
    
    if (shadingMode == 0) {
        // Mode plat
        result = vColor;
    } else if (shadingMode == 1) {
        // Mode sphère avec éclairage
        result = (ambient + diffuse + specular) * vColor;
    } else {
        // Mode glow
        float glow = 1.0 - sqrt(dist);
        result = vColor * (0.5 + glow * 0.5);
        result += vec3(glow * 0.2);
    }
    
    // Ombre douce sur les bords
    float edge = 1.0 - sqrt(dist);
    float alpha = smoothstep(0.0, 0.1, edge);
    
    FragColor = vec4(result, alpha);
}
"""

# Shaders pour le sol/grille
GRID_VERTEX_SHADER = """
#version 330 core

layout(location = 0) in vec3 position;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec3 fragPos;

void main() {
    fragPos = position;
    gl_Position = projection * view * model * vec4(position, 1.0);
}
"""

GRID_FRAGMENT_SHADER = """
#version 330 core

in vec3 fragPos;
out vec4 FragColor;

uniform vec3 gridColor;
uniform float gridSize;
uniform float lineWidth;

void main() {
    // Calcule la grille
    vec2 grid = abs(fract(fragPos.xz / gridSize - 0.5) - 0.5) / fwidth(fragPos.xz / gridSize);
    float line = min(grid.x, grid.y);
    
    float alpha = 1.0 - min(line, 1.0);
    alpha *= 0.5;  // Transparence de base
    
    // Lignes principales (chaque 5 unités)
    vec2 majorGrid = abs(fract(fragPos.xz / (gridSize * 5.0) - 0.5) - 0.5) / fwidth(fragPos.xz / (gridSize * 5.0));
    float majorLine = min(majorGrid.x, majorGrid.y);
    float majorAlpha = 1.0 - min(majorLine, 1.0);
    
    alpha = max(alpha, majorAlpha * 0.8);
    
    FragColor = vec4(gridColor, alpha);
}
"""

# Shaders pour les limites (boîte wireframe)
BOX_VERTEX_SHADER = """
#version 330 core

layout(location = 0) in vec3 position;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main() {
    gl_Position = projection * view * model * vec4(position, 1.0);
}
"""

BOX_FRAGMENT_SHADER = """
#version 330 core

out vec4 FragColor;
uniform vec3 boxColor;
uniform float alpha;

void main() {
    FragColor = vec4(boxColor, alpha);
}
"""


class Camera:
    """Caméra 3D avec orbite autour d'un point"""
    
    def __init__(self):
        self.target = np.array([0.0, 10.0, 0.0], dtype=np.float32)
        self.distance = 60.0
        self.pitch = -30.0  # Degrés
        self.yaw = 45.0     # Degrés
        self.fov = 45.0
        self.near = 0.1
        self.far = 500.0
        self.aspect = 1.0
        
    def get_position(self) -> np.ndarray:
        """Calcule la position de la caméra"""
        pitch_rad = np.radians(self.pitch)
        yaw_rad = np.radians(self.yaw)
        
        x = self.distance * np.cos(pitch_rad) * np.sin(yaw_rad)
        y = self.distance * np.sin(-pitch_rad)
        z = self.distance * np.cos(pitch_rad) * np.cos(yaw_rad)
        
        return self.target + np.array([x, y, z], dtype=np.float32)
    
    def get_view_matrix(self) -> np.ndarray:
        """Retourne la matrice de vue"""
        position = self.get_position()
        return pyrr.matrix44.create_look_at(
            position,
            self.target,
            np.array([0.0, 1.0, 0.0], dtype=np.float32)
        )
    
    def get_projection_matrix(self) -> np.ndarray:
        """Retourne la matrice de projection"""
        return pyrr.matrix44.create_perspective_projection(
            self.fov, self.aspect, self.near, self.far
        )
    
    def orbit(self, dx: float, dy: float):
        """Orbite la caméra autour du point cible"""
        self.yaw += dx * 0.5
        self.pitch += dy * 0.5
        self.pitch = np.clip(self.pitch, -89.0, 89.0)
        
    def zoom(self, delta: float):
        """Zoom avant/arrière"""
        self.distance *= (1.0 - delta * 0.1)
        self.distance = np.clip(self.distance, 5.0, 200.0)
        
    def pan(self, dx: float, dy: float):
        """Déplace le point cible"""
        # Calcule les vecteurs right et up de la caméra
        yaw_rad = np.radians(self.yaw)
        right = np.array([np.cos(yaw_rad), 0.0, -np.sin(yaw_rad)], dtype=np.float32)
        up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        
        self.target += right * dx * 0.1
        self.target += up * dy * 0.1


class Renderer:
    """Gestionnaire de rendu OpenGL"""
    
    def __init__(self):
        self.particle_shader = None
        self.grid_shader = None
        self.box_shader = None
        self.particle_vao = None
        self.particle_vbo_pos = None
        self.particle_vbo_color = None
        self.particle_vbo_size = None
        self.grid_vao = None
        self.grid_vbo = None
        self.box_vao = None
        self.box_vbo = None
        self.box_ebo = None
        
        self.camera = Camera()
        
        # Paramètres de rendu
        self.light_dir = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        self.light_color = np.array([1.0, 1.0, 0.95], dtype=np.float32)
        self.ambient_strength = 0.3
        self.background_color = (0.1, 0.1, 0.15)
        self.grid_color = np.array([0.5, 0.5, 0.6], dtype=np.float32)
        self.box_color = np.array([0.3, 0.5, 0.8], dtype=np.float32)
        self.global_particle_scale = 1.0
        self.shading_mode = 1  # 0: flat, 1: sphere, 2: glow
        self.show_grid = True
        self.show_bounds = True
        self.particle_count = 0
        
        # Limites du monde
        self.bounds = np.array([
            [-25, 0, -25],
            [25, 50, 25]
        ], dtype=np.float32)
        
    def initialize(self):
        """Initialise OpenGL et les shaders"""
        # Active les fonctionnalités nécessaires
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_PROGRAM_POINT_SIZE)
        
        # Compile les shaders
        self._compile_shaders()
        
        # Crée les VAOs/VBOs
        self._create_particle_buffers()
        self._create_grid_buffers()
        self._create_box_buffers()
        
    def _compile_shaders(self):
        """Compile tous les shaders"""
        # Shader pour les particules
        vertex = shaders.compileShader(PARTICLE_VERTEX_SHADER, GL_VERTEX_SHADER)
        fragment = shaders.compileShader(PARTICLE_FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        self.particle_shader = shaders.compileProgram(vertex, fragment)
        
        # Shader pour la grille
        vertex = shaders.compileShader(GRID_VERTEX_SHADER, GL_VERTEX_SHADER)
        fragment = shaders.compileShader(GRID_FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        self.grid_shader = shaders.compileProgram(vertex, fragment)
        
        # Shader pour la boîte
        vertex = shaders.compileShader(BOX_VERTEX_SHADER, GL_VERTEX_SHADER)
        fragment = shaders.compileShader(BOX_FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
        self.box_shader = shaders.compileProgram(vertex, fragment)
        
    def _create_particle_buffers(self):
        """Crée les buffers pour les particules"""
        self.particle_vao = glGenVertexArrays(1)
        glBindVertexArray(self.particle_vao)
        
        # Buffer des positions
        self.particle_vbo_pos = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.particle_vbo_pos)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        
        # Buffer des couleurs
        self.particle_vbo_color = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.particle_vbo_color)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1)
        
        # Buffer des tailles
        self.particle_vbo_size = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.particle_vbo_size)
        glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(2)
        
        glBindVertexArray(0)
        
    def _create_grid_buffers(self):
        """Crée les buffers pour la grille au sol"""
        # Crée un grand quad pour le sol
        grid_size = 50.0
        vertices = np.array([
            -grid_size, 0.0, -grid_size,
            grid_size, 0.0, -grid_size,
            grid_size, 0.0, grid_size,
            -grid_size, 0.0, -grid_size,
            grid_size, 0.0, grid_size,
            -grid_size, 0.0, grid_size,
        ], dtype=np.float32)
        
        self.grid_vao = glGenVertexArrays(1)
        glBindVertexArray(self.grid_vao)
        
        self.grid_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.grid_vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        
        glBindVertexArray(0)
        
    def _create_box_buffers(self):
        """Crée les buffers pour la boîte de limites"""
        min_b = self.bounds[0]
        max_b = self.bounds[1]
        
        # Les 8 sommets de la boîte
        vertices = np.array([
            min_b[0], min_b[1], min_b[2],  # 0
            max_b[0], min_b[1], min_b[2],  # 1
            max_b[0], max_b[1], min_b[2],  # 2
            min_b[0], max_b[1], min_b[2],  # 3
            min_b[0], min_b[1], max_b[2],  # 4
            max_b[0], min_b[1], max_b[2],  # 5
            max_b[0], max_b[1], max_b[2],  # 6
            min_b[0], max_b[1], max_b[2],  # 7
        ], dtype=np.float32)
        
        # Indices pour les lignes
        indices = np.array([
            # Face avant
            0, 1, 1, 2, 2, 3, 3, 0,
            # Face arrière
            4, 5, 5, 6, 6, 7, 7, 4,
            # Connexions
            0, 4, 1, 5, 2, 6, 3, 7,
        ], dtype=np.uint32)
        
        self.box_vao = glGenVertexArrays(1)
        glBindVertexArray(self.box_vao)
        
        self.box_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.box_vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        
        self.box_ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.box_ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
        
        glBindVertexArray(0)
        
    def update_particles(self, positions: np.ndarray, colors: np.ndarray, sizes: np.ndarray):
        """Met à jour les données des particules"""
        self.particle_count = len(sizes)
        
        if self.particle_count == 0:
            return
            
        glBindVertexArray(self.particle_vao)
        
        # Met à jour les positions
        glBindBuffer(GL_ARRAY_BUFFER, self.particle_vbo_pos)
        glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_DYNAMIC_DRAW)
        
        # Met à jour les couleurs
        glBindBuffer(GL_ARRAY_BUFFER, self.particle_vbo_color)
        glBufferData(GL_ARRAY_BUFFER, colors.nbytes, colors, GL_DYNAMIC_DRAW)
        
        # Met à jour les tailles
        glBindBuffer(GL_ARRAY_BUFFER, self.particle_vbo_size)
        glBufferData(GL_ARRAY_BUFFER, sizes.nbytes, sizes, GL_DYNAMIC_DRAW)
        
        glBindVertexArray(0)
        
    def render(self, width: int, height: int):
        """Effectue le rendu de la scène"""
        self.camera.aspect = width / height if height > 0 else 1.0
        
        # Clear
        glClearColor(*self.background_color, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Matrices
        view = self.camera.get_view_matrix()
        projection = self.camera.get_projection_matrix()
        model = pyrr.matrix44.create_identity(dtype=np.float32)
        
        # Rend la grille
        if self.show_grid:
            self._render_grid(model, view, projection)
        
        # Rend les limites
        if self.show_bounds:
            self._render_box(model, view, projection)
        
        # Rend les particules
        self._render_particles(model, view, projection)
        
    def _render_particles(self, model, view, projection):
        """Rend les particules"""
        if self.particle_count == 0:
            return
            
        glUseProgram(self.particle_shader)
        
        # Uniforms
        glUniformMatrix4fv(glGetUniformLocation(self.particle_shader, "model"), 
                         1, GL_FALSE, model)
        glUniformMatrix4fv(glGetUniformLocation(self.particle_shader, "view"), 
                         1, GL_FALSE, view)
        glUniformMatrix4fv(glGetUniformLocation(self.particle_shader, "projection"), 
                         1, GL_FALSE, projection)
        glUniform3fv(glGetUniformLocation(self.particle_shader, "lightDir"), 
                    1, self.light_dir)
        glUniform3fv(glGetUniformLocation(self.particle_shader, "lightColor"), 
                    1, self.light_color)
        glUniform1f(glGetUniformLocation(self.particle_shader, "ambientStrength"), 
                   self.ambient_strength)
        glUniform3fv(glGetUniformLocation(self.particle_shader, "viewPos"), 
                    1, self.camera.get_position())
        glUniform1f(glGetUniformLocation(self.particle_shader, "globalScale"), 
                   self.global_particle_scale)
        glUniform1i(glGetUniformLocation(self.particle_shader, "shadingMode"), 
                   self.shading_mode)
        
        glBindVertexArray(self.particle_vao)
        glDrawArrays(GL_POINTS, 0, self.particle_count)
        glBindVertexArray(0)
        
    def _render_grid(self, model, view, projection):
        """Rend la grille au sol"""
        glUseProgram(self.grid_shader)
        
        glUniformMatrix4fv(glGetUniformLocation(self.grid_shader, "model"), 
                         1, GL_FALSE, model)
        glUniformMatrix4fv(glGetUniformLocation(self.grid_shader, "view"), 
                         1, GL_FALSE, view)
        glUniformMatrix4fv(glGetUniformLocation(self.grid_shader, "projection"), 
                         1, GL_FALSE, projection)
        glUniform3fv(glGetUniformLocation(self.grid_shader, "gridColor"), 
                    1, self.grid_color)
        glUniform1f(glGetUniformLocation(self.grid_shader, "gridSize"), 2.0)
        
        glBindVertexArray(self.grid_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)
        
    def _render_box(self, model, view, projection):
        """Rend la boîte de limites"""
        glUseProgram(self.box_shader)
        
        glUniformMatrix4fv(glGetUniformLocation(self.box_shader, "model"), 
                         1, GL_FALSE, model)
        glUniformMatrix4fv(glGetUniformLocation(self.box_shader, "view"), 
                         1, GL_FALSE, view)
        glUniformMatrix4fv(glGetUniformLocation(self.box_shader, "projection"), 
                         1, GL_FALSE, projection)
        glUniform3fv(glGetUniformLocation(self.box_shader, "boxColor"), 
                    1, self.box_color)
        glUniform1f(glGetUniformLocation(self.box_shader, "alpha"), 0.5)
        
        glLineWidth(2.0)
        glBindVertexArray(self.box_vao)
        glDrawElements(GL_LINES, 24, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        
    def set_bounds(self, bounds: np.ndarray):
        """Met à jour les limites du monde"""
        self.bounds = bounds
        self._create_box_buffers()
        
    def cleanup(self):
        """Nettoie les ressources OpenGL"""
        if self.particle_vao:
            glDeleteVertexArrays(1, [self.particle_vao])
        if self.particle_vbo_pos:
            glDeleteBuffers(1, [self.particle_vbo_pos])
        if self.particle_vbo_color:
            glDeleteBuffers(1, [self.particle_vbo_color])
        if self.particle_vbo_size:
            glDeleteBuffers(1, [self.particle_vbo_size])
        if self.grid_vao:
            glDeleteVertexArrays(1, [self.grid_vao])
        if self.grid_vbo:
            glDeleteBuffers(1, [self.grid_vbo])
        if self.box_vao:
            glDeleteVertexArrays(1, [self.box_vao])
        if self.box_vbo:
            glDeleteBuffers(1, [self.box_vbo])
        if self.box_ebo:
            glDeleteBuffers(1, [self.box_ebo])
