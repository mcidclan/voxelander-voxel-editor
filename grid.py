import numpy as np
from OpenGL.GL import *
import glfw
import ctypes

class Grid:
 def __init__(self, world_size=16, cell_size=1):
   self.cell_size_changed = None
   self.world_size_changed = None
   self.available_world_sizes = [4, 8, 16, 32, 64, 128, 256, 512]
   
   self.world_size_index = self.available_world_sizes.index(world_size)
   self._world_size = world_size

   self.cell_sizes = self._get_valid_cell_sizes()
   self.cell_size_index = self.cell_sizes.index(cell_size)

   self._cell_size = cell_size
   self.centered_mode = False
   
   self.arrow_lengths = [1, 3, self.world_size // 2, self.world_size + 1]
   self.arrow_length_index = 1
   self.show_arrows = True

   self._create_shaders()
   self._create_buffers()
   self._update_geometry()
   self._update_arrow_geometry()

 def _get_valid_cell_sizes(self):
   max_size = self.world_size // 2
   sizes = []
   size = 1
   while size <= max_size:
     sizes.append(size)
     size *= 2
   return sizes

 def _create_shaders(self):
   vertex_shader_source = """
   #version 330 core
   layout (location = 0) in vec3 aPos;
   uniform mat4 mvp;
   uniform vec3 color;
   out vec3 fragColor;
   void main()
   {
       gl_Position = mvp * vec4(aPos, 1.0);
       fragColor = color;
   }
   """
   fragment_shader_source = """
   #version 330 core
   in vec3 fragColor;
   out vec4 FragColor;
   void main()
   {
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

 def _create_buffers(self):
   self.world_vao = glGenVertexArrays(1)
   self.world_vbo = glGenBuffers(1)
   glBindVertexArray(self.world_vao)
   glBindBuffer(GL_ARRAY_BUFFER, self.world_vbo)
   glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))
   glEnableVertexAttribArray(0)

   self.grid_vao = glGenVertexArrays(1)
   self.grid_vbo = glGenBuffers(1)
   glBindVertexArray(self.grid_vao)
   glBindBuffer(GL_ARRAY_BUFFER, self.grid_vbo)
   glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))
   glEnableVertexAttribArray(0)
   
   self.arrow_vao = glGenVertexArrays(1)
   self.arrow_vbo = glGenBuffers(1)
   glBindVertexArray(self.arrow_vao)
   glBindBuffer(GL_ARRAY_BUFFER, self.arrow_vbo)
   glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))
   glEnableVertexAttribArray(0)

   glBindVertexArray(0)

 def _update_geometry(self):
   half_size = self.world_size / 2
   base = -half_size if self.centered_mode else 0
   top = half_size if self.centered_mode else self.world_size

   world_vertices = []
   corners = [
     [base, base, base], [top, base, base],
     [top, base, base], [top, base, top],
     [top, base, top], [base, base, top],
     [base, base, top], [base, base, base],

     [base, top, base], [top, top, base],
     [top, top, base], [top, top, top],
     [top, top, top], [base, top, top],
     [base, top, top], [base, top, base],

     [base, base, base], [base, top, base],
     [top, base, base], [top, top, base],
     [top, base, top], [top, top, top],
     [base, base, top], [base, top, top]
   ]
   world_vertices.extend(corners)

   grid_vertices = []
   step = self.cell_size
   start = base
   end = top

   x = start
   while x <= end:
     grid_vertices.append([x, 0, start])
     grid_vertices.append([x, 0, end])
     x += step

   z = start
   while z <= end:
     grid_vertices.append([start, 0, z])
     grid_vertices.append([end, 0, z])
     z += step

   world_vertices = np.array(world_vertices, dtype=np.float32)
   grid_vertices = np.array(grid_vertices, dtype=np.float32)

   glBindBuffer(GL_ARRAY_BUFFER, self.world_vbo)
   glBufferData(GL_ARRAY_BUFFER, world_vertices.nbytes, world_vertices, GL_STATIC_DRAW)

   glBindBuffer(GL_ARRAY_BUFFER, self.grid_vbo)
   glBufferData(GL_ARRAY_BUFFER, grid_vertices.nbytes, grid_vertices, GL_STATIC_DRAW)

   self.world_vertex_count = len(world_vertices)
   self.grid_vertex_count = len(grid_vertices)

 def _update_arrow_geometry(self):
   length = self.arrow_lengths[self.arrow_length_index]
   arrow_head_size = 0.3

   arrow_vertices = []
   
   arrow_vertices.append([0, 0, 0])
   arrow_vertices.append([length, 0, 0])
   
   arrow_vertices.append([length, 0, 0])
   arrow_vertices.append([length - arrow_head_size, arrow_head_size, arrow_head_size])
   
   arrow_vertices.append([length, 0, 0])
   arrow_vertices.append([length - arrow_head_size, -arrow_head_size, arrow_head_size])
   
   arrow_vertices.append([length, 0, 0])
   arrow_vertices.append([length - arrow_head_size, arrow_head_size, -arrow_head_size])
   
   arrow_vertices.append([length, 0, 0])
   arrow_vertices.append([length - arrow_head_size, -arrow_head_size, -arrow_head_size])
   
   arrow_vertices.append([0, 0, 0])
   arrow_vertices.append([0, length, 0])
   
   arrow_vertices.append([0, length, 0])
   arrow_vertices.append([arrow_head_size, length - arrow_head_size, arrow_head_size])
   
   arrow_vertices.append([0, length, 0])
   arrow_vertices.append([-arrow_head_size, length - arrow_head_size, arrow_head_size])
   
   arrow_vertices.append([0, length, 0])
   arrow_vertices.append([arrow_head_size, length - arrow_head_size, -arrow_head_size])
   
   arrow_vertices.append([0, length, 0])
   arrow_vertices.append([-arrow_head_size, length - arrow_head_size, -arrow_head_size])
   
   arrow_vertices.append([0, 0, 0])
   arrow_vertices.append([0, 0, length])
   
   arrow_vertices.append([0, 0, length])
   arrow_vertices.append([arrow_head_size, arrow_head_size, length - arrow_head_size])
   
   arrow_vertices.append([0, 0, length])
   arrow_vertices.append([-arrow_head_size, arrow_head_size, length - arrow_head_size])
   
   arrow_vertices.append([0, 0, length])
   arrow_vertices.append([arrow_head_size, -arrow_head_size, length - arrow_head_size])
   
   arrow_vertices.append([0, 0, length])
   arrow_vertices.append([-arrow_head_size, -arrow_head_size, length - arrow_head_size])

   arrow_vertices = np.array(arrow_vertices, dtype=np.float32)
   
   glBindBuffer(GL_ARRAY_BUFFER, self.arrow_vbo)
   glBufferData(GL_ARRAY_BUFFER, arrow_vertices.nbytes, arrow_vertices, GL_STATIC_DRAW)
   self.arrow_vertex_count = len(arrow_vertices)

 @property
 def cell_size(self):
   return self._cell_size
   
 @cell_size.setter
 def cell_size(self, value):
   self._cell_size = value
   if self.cell_size_changed:
     self.cell_size_changed(value)

 @property
 def world_size(self):
   return self._world_size
   
 @world_size.setter
 def world_size(self, value):
   self._world_size = value
   if self.world_size_changed:
     self.world_size_changed(value)
   
 def on_key_event(self, key, action):
   if action == glfw.RELEASE:
     if key == glfw.KEY_1:
       self.centered_mode = not self.centered_mode
       self._update_geometry()
       self._update_arrow_geometry()

     elif key == glfw.KEY_2:
       self.world_size_index = (self.world_size_index + 1) % len(self.available_world_sizes)
       self.world_size = self.available_world_sizes[self.world_size_index]

       self.cell_sizes = self._get_valid_cell_sizes()

       if self.cell_size > self.cell_sizes[-1]:
         self.cell_size_index = 0
         self.cell_size = self.cell_sizes[0]
       else:
         self.cell_size_index = self.cell_sizes.index(self.cell_size)

       self.arrow_lengths = [1, self.world_size // 2, self.world_size + 1]
       
       self._update_geometry()
       self._update_arrow_geometry()

     elif key == glfw.KEY_3:
       self.cell_size_index = (self.cell_size_index + 1) % len(self.cell_sizes)
       self.cell_size = self.cell_sizes[self.cell_size_index]
       self._update_geometry()
       
     elif key == glfw.KEY_4:
       self.arrow_length_index = (self.arrow_length_index + 1) % 3
       self._update_arrow_geometry()

 def draw_grid(self, pv_matrix):
   model = np.eye(4, dtype=np.float32)
   mvp = pv_matrix @ model

   glUseProgram(self.shader_program)
   glUniformMatrix4fv(self.mvp_location, 1, GL_FALSE, mvp.T)

   glUniform3f(self.color_location, 0.312, 0.48, 0.48)
   glBindVertexArray(self.grid_vao)
   glDrawArrays(GL_LINES, 0, self.grid_vertex_count)

   glBindVertexArray(0)
   glUseProgram(0)

 def draw(self, pv_matrix):
   glDisable(GL_DEPTH_TEST)
   model = np.eye(4, dtype=np.float32)
   mvp = pv_matrix @ model

   glUseProgram(self.shader_program)
   glUniformMatrix4fv(self.mvp_location, 1, GL_FALSE, mvp.T)

   glUniform3f(self.color_location, 1.0, 0.5, 0.0)
   glBindVertexArray(self.world_vao)
   glDrawArrays(GL_LINES, 0, self.world_vertex_count)
   
   if self.show_arrows:
     glUniform3f(self.color_location, 1.0, 0.0, 0.0)
     glBindVertexArray(self.arrow_vao)
     glDrawArrays(GL_LINES, 0, 2)
     
     glDrawArrays(GL_LINES, 2, 8)

     glUniform3f(self.color_location, 0.0, 1.0, 0.0)
     glDrawArrays(GL_LINES, 10, 2)
     glDrawArrays(GL_LINES, 12, 8)

     glUniform3f(self.color_location, 0.0, 0.0, 1.0)
     glDrawArrays(GL_LINES, 20, 2)
     glDrawArrays(GL_LINES, 22, 8)

   glBindVertexArray(0)
   glUseProgram(0)
   glEnable(GL_DEPTH_TEST)
   
 def cleanup(self):
   glDeleteVertexArrays(1, [self.world_vao])
   glDeleteVertexArrays(1, [self.grid_vao])
   glDeleteVertexArrays(1, [self.arrow_vao])
   glDeleteBuffers(1, [self.world_vbo])
   glDeleteBuffers(1, [self.grid_vbo])
   glDeleteBuffers(1, [self.arrow_vbo])
   glDeleteProgram(self.shader_program)
