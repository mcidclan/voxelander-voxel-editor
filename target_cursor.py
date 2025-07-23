import numpy as np
from OpenGL.GL import *

class TargetCursor:
  def __init__(self, camera):
    self.camera = camera
    
    self.VAO = None
    self.VBO = None
    self.EBO = None
    self.shader_program = None
    self.mvp_location = None
    self.color_location = None

    self.grid_level = 0
    self.cell_size = 1.0
    
    self._setup_shader()
    self._setup_buffers()
  
  def _setup_shader(self):
    vertex_shader_source = """
    #version 330 core
    layout (location = 0) in vec3 aPos;
    
    uniform mat4 mvp;
    uniform vec3 color;
    
    out vec3 fragColor;
    
    void main() {
      gl_Position = mvp * vec4(aPos, 1.0);
      fragColor = color;
    }
    """
    
    fragment_shader_source = """
    #version 330 core
    in vec3 fragColor;
    out vec4 FragColor;
    
    void main() {
      FragColor = vec4(fragColor, 1.0);
    }
    """
    
    vertex_shader = glCreateShader(GL_VERTEX_SHADER)
    glShaderSource(vertex_shader, vertex_shader_source)
    glCompileShader(vertex_shader)
    
    fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
    glShaderSource(fragment_shader, fragment_shader_source)
    glCompileShader(fragment_shader)
    
    self.shader_program = glCreateProgram()
    glAttachShader(self.shader_program, vertex_shader)
    glAttachShader(self.shader_program, fragment_shader)
    glLinkProgram(self.shader_program)
    
    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)
    
    self.mvp_location = glGetUniformLocation(self.shader_program, "mvp")
    self.color_location = glGetUniformLocation(self.shader_program, "color")
  
  def _generate_grid_wireframe(self):
    grid_sizes = [1, 3, 5, 7, 9]
    grid_size = grid_sizes[self.grid_level]
    
    vertices = []
    indices = []
    
    offset = (grid_size - 1) * self.cell_size * 0.5
    center_index = grid_size // 2
    padding = 0.0
    
    for i in range(grid_size):
      for j in range(grid_size):
        for k in range(grid_size):
          if i == center_index and j == center_index and k == center_index:
            continue
          
          x = i * self.cell_size - offset - self.cell_size * 0.5
          y = j * self.cell_size - offset - self.cell_size * 0.5
          z = k * self.cell_size - offset - self.cell_size * 0.5
          
          cell_size_padded = self.cell_size - 2 * padding
          
          cell_vertices = [
            [x + padding, y + padding, z + padding],
            [x + padding + cell_size_padded, y + padding, z + padding],
            [x + padding + cell_size_padded, y + padding + cell_size_padded, z + padding],
            [x + padding, y + padding + cell_size_padded, z + padding],
            [x + padding, y + padding, z + padding + cell_size_padded],
            [x + padding + cell_size_padded, y + padding, z + padding + cell_size_padded],
            [x + padding + cell_size_padded, y + padding + cell_size_padded, z + padding + cell_size_padded],
            [x + padding, y + padding + cell_size_padded, z + padding + cell_size_padded]
          ]
          
          base_index = len(vertices)
          vertices.extend(cell_vertices)
          
          cell_indices = [
            base_index, base_index + 1,
            base_index + 1, base_index + 2,
            base_index + 2, base_index + 3,
            base_index + 3, base_index,
            base_index + 4, base_index + 5,
            base_index + 5, base_index + 6,
            base_index + 6, base_index + 7,
            base_index + 7, base_index + 4,
            base_index, base_index + 4,
            base_index + 1, base_index + 5,
            base_index + 2, base_index + 6,
            base_index + 3, base_index + 7
          ]
          indices.extend(cell_indices)
    
    return np.array(vertices, dtype=np.float32), np.array(indices, dtype=np.uint32)
  
  def _setup_buffers(self):
    self.VAO = glGenVertexArrays(1)
    self.VBO = glGenBuffers(1)
    self.EBO = glGenBuffers(1)
    
    self._update_buffers()
  
  def _update_buffers(self):
    vertices, indices = self._generate_grid_wireframe()
    
    glBindVertexArray(self.VAO)
    
    glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_DYNAMIC_DRAW)
    
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_DYNAMIC_DRAW)
    
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    
    self.indices_count = len(indices)
    
    glBindVertexArray(0)
  
  def set_grid_size(self, level):
    if 0 <= level <= 4:
      self.grid_level = level
      self._update_buffers()
  
  def set_cell_size(self, size):
    if size > 0:
      self.cell_size = size
      self._update_buffers()
  
  def draw(self, target, pvm_matrix):
    model = np.eye(4, dtype=np.float32)
    model[0, 3] = target[0]
    model[1, 3] = target[1]
    model[2, 3] = target[2]
    
    final_mvp = pvm_matrix @ model
    
    glUseProgram(self.shader_program)
    
    glUniformMatrix4fv(self.mvp_location, 1, GL_FALSE, final_mvp.T)
    
    glUniform3f(self.color_location, 0.26, 0.4, 0.4)
    glBindVertexArray(self.VAO)
    glDrawElements(GL_LINES, self.indices_count, GL_UNSIGNED_INT, None)
    
    glDisable(GL_DEPTH_TEST)
    
    center_vertices, center_indices = self._generate_center_cube()
    
    glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
    glBufferData(GL_ARRAY_BUFFER, center_vertices.nbytes, center_vertices, GL_DYNAMIC_DRAW)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, center_indices.nbytes, center_indices, GL_DYNAMIC_DRAW)
    
    if self.camera.is_moving:
      glUniform3f(self.color_location, 0.8, 0.25, 0.3)
    else:
      glUniform3f(self.color_location, 1.0, 0.3, 0.3)
  
    glDrawElements(GL_LINES, len(center_indices), GL_UNSIGNED_INT, None)
    glEnable(GL_DEPTH_TEST)
    
    self._update_buffers()
    
    glBindVertexArray(0)
    glUseProgram(0)
  
  def _generate_center_cube(self):
    padding = 0.0
    half_size = (self.cell_size - 2 * padding) * 0.5
    
    vertices = np.array([
      [-half_size, -half_size, -half_size],
      [half_size, -half_size, -half_size],
      [half_size, half_size, -half_size],
      [-half_size, half_size, -half_size],
      [-half_size, -half_size, half_size],
      [half_size, -half_size, half_size],
      [half_size, half_size, half_size],
      [-half_size, half_size, half_size]
    ], dtype=np.float32)
    
    indices = np.array([
      0, 1, 1, 2, 2, 3, 3, 0,
      4, 5, 5, 6, 6, 7, 7, 4,
      0, 4, 1, 5, 2, 6, 3, 7
    ], dtype=np.uint32)
    
    return vertices, indices
  
  def cleanup(self):
    if self.VAO:
      glDeleteVertexArrays(1, [self.VAO])
    if self.VBO:
      glDeleteBuffers(1, [self.VBO])
    if self.EBO:
      glDeleteBuffers(1, [self.EBO])
    if self.shader_program:
      glDeleteProgram(self.shader_program)
