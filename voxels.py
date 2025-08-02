import glfw
import numpy as np
from OpenGL.GL import *
import ctypes

def get_cube_faces(size):
  half = size * 0.5
  return [
    ([-half, -half, -half], [half, -half, -half], [half, half, -half], [-half, half, -half], [0, 0, -1]),
    ([-half, -half, half], [half, -half, half], [half, half, half], [-half, half, half], [0, 0, 1]),
    ([-half, -half, -half], [half, -half, -half], [half, -half, half], [-half, -half, half], [0, -1, 0]),
    ([-half, half, -half], [half, half, -half], [half, half, half], [-half, half, half], [0, 1, 0]),
    ([half, -half, -half], [half, half, -half], [half, half, half], [half, -half, half], [1, 0, 0]),
    ([-half, -half, -half], [-half, half, -half], [-half, half, half], [-half, -half, half], [-1, 0, 0]),
  ]

class Voxels:
  def __init__(self):
    self.blocks = {}
    self.batches = []
    self.VAO = glGenVertexArrays(1)
    self.VBO = glGenBuffers(1)
    self.EBO = glGenBuffers(1)
    self.shader_program = self.create_shader_program()
    self.vertex_stride = 9
    self.vertices_per_face = 4
    self.indices_per_face = 6
    self.needs_update = True

  def create_shader_program(self):
    """
    vertex_shader_src = '''
    #version 330 core
    layout(location = 0) in vec3 aPos;
    uniform mat4 mvp;
    void main() {
      gl_Position = mvp * vec4(aPos, 1.0);
    }
    '''
    fragment_shader_src = '''
    #version 330 core
    out vec4 FragColor;
    void main() {
      FragColor = vec4(1.0, 1.0, 1.0, 1.0);
    }
    '''
    """
    
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
      vec3 normal = normalize(aNormal);
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
    
    def compile_shader(src, type):
      shader = glCreateShader(type)
      glShaderSource(shader, src)
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

  def aligned(self, coord, size):
    return tuple((np.floor(np.array(coord) / size) * size).astype(int))

  def on_key_event(self, key, action, camera, overlay):
    if key == glfw.KEY_A and action == glfw.RELEASE:
      if camera.is_moving:
        return
      base = self.aligned(camera.target - camera.unit * 0.5, camera.unit)
      size = int(camera.unit)
      to_remove = []
      for dx in range(size):
        for dy in range(size):
          for dz in range(size):
            pos = (base[0] + dx, base[1] + dy, base[2] + dz)
            if pos in self.blocks:
              if self.blocks[pos]['size'] <= size:
                to_remove.append(self.blocks[pos]['block_id'])
      if to_remove:
        for bid in set(to_remove):
          self.remove_batch(bid)
      else:
        self.add_batch(base, size, overlay.color)

  def add_batch(self, origin, size, color):
    if origin in self.blocks:
      print(f"Conflict at {origin} (already occupied by batch {self.blocks[origin]['block_id']})")
    for dx in range(size):
      for dy in range(size):
        for dz in range(size):
          pos = (origin[0] + dx, origin[1] + dy, origin[2] + dz)
          if pos in self.blocks:
            if self.blocks[pos]['size'] >= size:
              return
    to_remove = []
    for dx in range(size):
      for dy in range(size):
        for dz in range(size):
          pos = (origin[0] + dx, origin[1] + dy, origin[2] + dz)
          if pos in self.blocks:
            to_remove.append(self.blocks[pos]['block_id'])
    for bid in set(to_remove):
      self.remove_batch(bid)

    block_id = len(self.batches)
    vertices = []
    indices = []
    offset = 0

    for dx in range(size):
      for dy in range(size):
        for dz in range(size):
          pos = (origin[0] + dx, origin[1] + dy, origin[2] + dz)
          self.blocks[pos] = {'block_id': block_id, 'size': size}

    cube_faces = get_cube_faces(size)
    center = np.array(origin) + size/2

    for face_idx, (v1, v2, v3, v4, normal) in enumerate(cube_faces):
      nx, ny, nz = normal
      hide_face = False
      if size > 1:
        neighbor_pos = (
          int(center[0] + nx * size),
          int(center[1] + ny * size),
          int(center[2] + nz * size)
        )
        if neighbor_pos in self.blocks:
          hide_face = True
      else:
        neighbor_pos = (
          origin[0] + int(nx),
          origin[1] + int(ny),
          origin[2] + int(nz)
        )
        if neighbor_pos in self.blocks:
          hide_face = True

      if hide_face:
        continue

      face_vertices = [v1, v2, v3, v4]
      for vertex in face_vertices:
        p = center + np.array(vertex)
        vertices.extend([*p, *normal, *color])

      indices.extend([offset, offset + 1, offset + 2, offset + 2, offset + 3, offset])
      offset += 4

    self.batches.append({
      'vertices': vertices,
      'indices': indices,
      'position': tuple(origin),
      'size': size,
      'dim': size
    })
    self.needs_update = True
  
  def remove_batch(self, block_id):
    if block_id >= len(self.batches):
      return
    self.batches[block_id] = None
    self.blocks = {k: v for k, v in self.blocks.items() if v['block_id'] != block_id}
    self.needs_update = True

  def update_buffers(self):
    if not self.needs_update:
      return
    vertices = []
    indices = []
    offset = 0
    for b in self.batches:
      if b is None:
        continue
      v = np.array(b['vertices'], dtype=np.float32)
      i = np.array(b['indices'], dtype=np.uint32) + offset
      vertices.extend(v)
      indices.extend(i)
      offset += len(v) // self.vertex_stride
    vertices = np.array(vertices, dtype=np.float32)
    indices = np.array(indices, dtype=np.uint32)
    glBindVertexArray(self.VAO)
    glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
    stride = self.vertex_stride * 4
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
    ldx, ldy = 30, 30
    light_dir = -np.array([
      np.cos(np.radians(ldx)) * np.cos(np.radians(ldy)),
      -np.sin(np.radians(ldy)),
      np.sin(np.radians(ldx)) * np.cos(np.radians(ldy))
    ], dtype=np.float32)
    light_color = np.array([1.0, 1.0, 0.95], dtype=np.float32)
    ambient_intensity = 0.4
    glUniform3fv(glGetUniformLocation(self.shader_program, "lightDir"), 1, light_dir)
    glUniform3fv(glGetUniformLocation(self.shader_program, "lightColor"), 1, light_color)
    glUniform1f(glGetUniformLocation(self.shader_program, "ambientIntensity"), ambient_intensity)
    glBindVertexArray(self.VAO)
    # glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
    glBindVertexArray(0)
    glUseProgram(0)

  def cleanup(self):
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
