import glfw
import numpy as np
from OpenGL.GL import *
import ctypes

VERTEX_SHADER_SRC = """
#version 330 core
layout (location = 0) in vec3 aPos;
uniform mat4 mvp;
void main() {
  gl_Position = mvp * vec4(aPos, 1.0);
}
"""

FRAGMENT_SHADER_SRC = """
#version 330 core
out vec4 FragColor;

uniform vec3 color;

void main() {
  FragColor = vec4(color, 1.0);
}
"""

class Overlay:
  def __init__(self, width, height):
    self.colors = [
      (1.0, 0.0, 0.0),
      (0.0, 1.0, 0.0),
      (0.0, 0.0, 1.0),
      (1.0, 1.0, 0.0),
      (1.0, 1.0, 1.0),
      (1.0, 0.5, 0.0),
      (0.4, 0.2, 0.1),
      (0.1, 0.1, 0.1),
      (1.0, 0.4, 0.7),
      (0.6, 0.0, 0.6),
      (0.5, 0.8, 1.0),
      (0.5, 1.0, 0.5),
    ]
    self.color_index = 0
    self.color = self.colors[self.color_index]

    self.shader_program = self.create_shader()
    self.vao = self.create_cube_vao()
    
    self.translation = [-float(width) * 0.5, - float(height) * 0.5, 0.0]

  def create_shader(self):
    def compile_shader(source, shader_type):
      shader = glCreateShader(shader_type)
      glShaderSource(shader, source)
      glCompileShader(shader)
      if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        raise RuntimeError(glGetShaderInfoLog(shader))
      return shader

    vs = compile_shader(VERTEX_SHADER_SRC, GL_VERTEX_SHADER)
    fs = compile_shader(FRAGMENT_SHADER_SRC, GL_FRAGMENT_SHADER)
    program = glCreateProgram()
    glAttachShader(program, vs)
    glAttachShader(program, fs)
    glLinkProgram(program)
    if not glGetProgramiv(program, GL_LINK_STATUS):
      raise RuntimeError(glGetProgramInfoLog(program))
    glDeleteShader(vs)
    glDeleteShader(fs)
    return program

  def create_cube_vao(self):
    vertices = np.array([
      [-0.5, -0.5, -0.5],
      [ 0.5, -0.5, -0.5],
      [ 0.5,  0.5, -0.5],
      [-0.5,  0.5, -0.5],
      [-0.5, -0.5,  0.5],
      [ 0.5, -0.5,  0.5],
      [ 0.5,  0.5,  0.5],
      [-0.5,  0.5,  0.5],
    ], dtype=np.float32)

    indices = np.array([
      0, 1, 2, 2, 3, 0,
      4, 5, 6, 6, 7, 4,
      0, 1, 5, 5, 4, 0,
      2, 3, 7, 7, 6, 2,
      1, 2, 6, 6, 5, 1,
      0, 3, 7, 7, 4, 0,
    ], dtype=np.uint32)

    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)
    ebo = glGenBuffers(1)

    glBindVertexArray(vao)

    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))

    glBindVertexArray(0)
    return vao

  def draw(self, projection):
    glUseProgram(self.shader_program)
    glDisable(GL_DEPTH_TEST)

    translate = np.eye(4, dtype=np.float32)
    translate[:3, 3] = self.translation + np.array([50.0, 50.0, 0.0], dtype=np.float32)

    scale = np.diag([30.0, 30.0, 30.0, 1.0]).astype(np.float32)
    
    rot_y = np.array([
      [np.cos(np.pi/4), 0, np.sin(np.pi/4), 0],
      [0, 1, 0, 0],
      [-np.sin(np.pi/4), 0, np.cos(np.pi/4), 0],
      [0, 0, 0, 1]
    ], dtype=np.float32)

    rot_z = np.array([
      [np.cos(np.pi/4), -np.sin(np.pi/4), 0, 0],
      [np.sin(np.pi/4),  np.cos(np.pi/4), 0, 0],
      [0, 0, 1, 0],
      [0, 0, 0, 1]
    ], dtype=np.float32)

    view = np.eye(4, dtype=np.float32)

    model = translate @ rot_y @ rot_z @ scale
    mvp = projection @ model

    glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "mvp"), 1, GL_FALSE, mvp.T)
    glUniform3fv(glGetUniformLocation(self.shader_program, "color"), 1, self.color)

    glBindVertexArray(self.vao)
    glDrawElements(GL_TRIANGLES, 36, GL_UNSIGNED_INT, None)
    glBindVertexArray(0)

    glEnable(GL_DEPTH_TEST)
    glUseProgram(0)

  def on_key_event(self, key, action):
    if key == glfw.KEY_C and action == glfw.PRESS:
      self.color_index = (self.color_index + 1) % len(self.colors)
      self.color = self.colors[self.color_index]

  def cleanup(self):
    glDeleteVertexArrays(1, [self.vao])
    glDeleteProgram(self.shader_program)
