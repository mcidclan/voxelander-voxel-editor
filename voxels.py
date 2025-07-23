import numpy as np
import glfw
from OpenGL.GL import *
import ctypes

def get_cube_data():
  """Generate cube data with correct normals for each face"""
  vertices = []
  indices = []
  normals = []

  faces = [
    ([-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0.5, 0.5, -0.5], [-0.5, 0.5, -0.5], [0.0, 0.0, -1.0]),
    ([-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, 0.5], [0.0, 0.0, 1.0]),
    ([-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0.5, -0.5, 0.5], [-0.5, -0.5, 0.5], [0.0, -1.0, 0.0]),
    ([-0.5, 0.5, -0.5], [0.5, 0.5, -0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, 0.5], [0.0, 1.0, 0.0]),
    ([0.5, -0.5, -0.5], [0.5, 0.5, -0.5], [0.5, 0.5, 0.5], [0.5, -0.5, 0.5], [1.0, 0.0, 0.0]),
    ([-0.5, -0.5, -0.5], [-0.5, 0.5, -0.5], [-0.5, 0.5, 0.5], [-0.5, -0.5, 0.5], [-1.0, 0.0, 0.0]),
  ]

  vertex_count = 0

  for v1, v2, v3, v4, normal in faces:
    face_vertices = [v1, v2, v3, v4]
    for vertex in face_vertices:
      vertices.extend(vertex)
      normals.extend(normal)

    indices.extend([
      vertex_count, vertex_count + 1, vertex_count + 2,
      vertex_count + 2, vertex_count + 3, vertex_count
    ])
    vertex_count += 4

  return np.array(vertices, dtype=np.float32), np.array(indices, dtype=np.uint32), np.array(normals, dtype=np.float32)

cube_vertices_flat, cube_indices, cube_normals_flat = get_cube_data()

class Voxels:
  def __init__(self):
    self.grid = {}
    self.vertex_data = []
    self.index_data = []
    self.needs_update = True
    self.VAO = glGenVertexArrays(1)
    self.VBO = glGenBuffers(1)
    self.EBO = glGenBuffers(1)
    self.shader_program = self.create_shader_program()
    self.vertex_stride = 9
    self.vertices_per_cube = 24
    self.indices_per_cube = 36

  def create_shader_program(self):
    vertex_shader_src = '''
    #version 330 core
    layout(location = 0) in vec3 aPos;
    layout(location = 1) in vec3 aNormal;
    layout(location = 2) in vec3 aColor;

    uniform mat4 mvp;
    uniform vec3 lightDir;
    uniform vec3 lightColor;
    uniform float ambientIntensity;

    out vec3 vertexColor;

    void main() {
      normal = normalize(aNormal);
      gl_Position = mvp * vec4(aPos, 1.0);
      float diffuseIntensity = max(dot(normal, lightDir), 0.0);
      vec3 diffuse = diffuseIntensity * lightColor;
      vec3 ambient = ambientIntensity * lightColor;
      vertexColor = aColor * (ambient + diffuse);
    }
    '''

    fragment_shader_src = '''
    #version 330 core
    in vec3 vertexColor;
    out vec4 FragColor;

    void main() {
      FragColor = vec4(vertexColor, 1.0);
    }
    '''

    def compile_shader(source, shader_type):
      shader = glCreateShader(shader_type)
      glShaderSource(shader, source)
      glCompileShader(shader)
      if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        raise RuntimeError(glGetShaderInfoLog(shader).decode())
      return shader

    vs = compile_shader(vertex_shader_src, GL_VERTEX_SHADER)
    fs = compile_shader(fragment_shader_src, GL_FRAGMENT_SHADER)
    program = glCreateProgram()
    glAttachShader(program, vs)
    glAttachShader(program, fs)
    glLinkProgram(program)
    if not glGetProgramiv(program, GL_LINK_STATUS):
      raise RuntimeError(glGetProgramInfoLog(program).decode())
    glDeleteShader(vs)
    glDeleteShader(fs)
    return program

  def on_key_event(self, key, action, camera, overlay):
    if key == glfw.KEY_A and action == glfw.RELEASE:
      if camera.is_moving:
        return

      base_coord = tuple(map(int, camera.target - camera.unit * 0.5))
      cube_size = int(camera.unit)

      should_remove = False
      for x in range(cube_size):
        for y in range(cube_size):
          for z in range(cube_size):
            coord = (base_coord[0] + x, base_coord[1] + y, base_coord[2] + z)
            if coord in self.grid:
              should_remove = True
              break
          if should_remove:
            break
        if should_remove:
          break

      if should_remove:
        for x in range(cube_size):
          for y in range(cube_size):
            for z in range(cube_size):
              coord = (base_coord[0] + x, base_coord[1] + y, base_coord[2] + z)
              if coord in self.grid:
                self.remove_voxel(*coord)
      else:
        for x in range(cube_size):
          for y in range(cube_size):
            for z in range(cube_size):
              coord = (base_coord[0] + x, base_coord[1] + y, base_coord[2] + z)
              self.add_voxel(*coord, overlay.color)

  def add_voxel(self, x, y, z, color):
    key = (x, y, z)
    if key in self.grid:
      return
    vertex_offset = len(self.vertex_data) // 9

    translated_vertices = cube_vertices_flat.reshape(-1, 3) + np.array([x + 0.5, y + 0.5, z + 0.5])

    for i, vertex in enumerate(translated_vertices):
      normal_start = i * 3
      normal = cube_normals_flat[normal_start:normal_start + 3]
      self.vertex_data.extend([
        vertex[0], vertex[1], vertex[2],
        normal[0], normal[1], normal[2],
        color[0], color[1], color[2]
      ])
    translated_indices = cube_indices + vertex_offset
    self.index_data.extend(translated_indices)
    self.grid[key] = vertex_offset
    self.needs_update = True

  def remove_voxel(self, x, y, z):
    key = (x, y, z)
    if key not in self.grid:
      return

    removed_vertex_offset = self.grid[key]
    del self.grid[key]

    vertex_start = removed_vertex_offset * 9
    vertex_count = self.vertices_per_cube * 9

    indices_to_remove = []
    for i, idx in enumerate(self.index_data):
      if removed_vertex_offset <= idx < removed_vertex_offset + self.vertices_per_cube:
        indices_to_remove.append(i)

    del self.vertex_data[vertex_start:vertex_start + vertex_count]

    for i in reversed(indices_to_remove):
      del self.index_data[i]

    vertices_removed = self.vertices_per_cube

    for pos, offset in self.grid.items():
      if offset > removed_vertex_offset:
        self.grid[pos] = offset - vertices_removed

    for i in range(len(self.index_data)):
      if self.index_data[i] >= removed_vertex_offset + vertices_removed:
        self.index_data[i] -= vertices_removed

    self.needs_update = True

  def update_buffers(self):
    if not self.needs_update:
      return
    vertices = np.array(self.vertex_data, dtype=np.float32)
    indices = np.array(self.index_data, dtype=np.uint32)
    glBindVertexArray(self.VAO)
    glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
    stride = 9 * 4
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(24))
    glEnableVertexAttribArray(2)
    glBindVertexArray(0)
    self.index_count = len(indices)
    self.needs_update = False

  def draw(self, pvm_matrix):
    self.update_buffers()

    glUseProgram(self.shader_program)

    mvp_location = glGetUniformLocation(self.shader_program, "mvp")
    glUniformMatrix4fv(mvp_location, 1, GL_FALSE, pvm_matrix.T)

    ldx = 30
    ldy = 30
    light_dir = -np.array([
      np.cos(np.radians(ldx)) * np.cos(np.radians(ldy)),
      -np.sin(np.radians(ldy)),
      np.sin(np.radians(ldx)) * np.cos(np.radians(ldy))
    ], dtype=np.float32)
    
    light_color = np.array([1.0, 1.0, 0.95], dtype=np.float32)
    ambient_intensity = 0.4

    light_dir_location = glGetUniformLocation(self.shader_program, "lightDir")
    glUniform3fv(light_dir_location, 1, light_dir)

    light_color_location = glGetUniformLocation(self.shader_program, "lightColor")
    glUniform3fv(light_color_location, 1, light_color)

    ambient_location = glGetUniformLocation(self.shader_program, "ambientIntensity")
    glUniform1f(ambient_location, ambient_intensity)
    glBindVertexArray(self.VAO)
    glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
    glBindVertexArray(0)
    glUseProgram(0)

  def cleanup(self):
    """Release OpenGL resources"""
    if hasattr(self, 'VAO') and self.VAO:
      glDeleteVertexArrays(1, [self.VAO])
      self.VAO = 0

    if hasattr(self, 'VBO') and self.VBO:
      glDeleteBuffers(1, [self.VBO])
      self.VBO = 0

    if hasattr(self, 'EBO') and self.EBO:
      glDeleteBuffers(1, [self.EBO])
      self.EBO = 0

    if hasattr(self, 'shader_program') and self.shader_program:
      glDeleteProgram(self.shader_program)
      self.shader_program = 0
