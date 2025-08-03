import glfw
from OpenGL.GL import *
import numpy as np
import ctypes
import math
import time
from target_cursor import TargetCursor
from voxels import Voxels  
from camera import Camera
from overlay import Overlay
from grid import Grid
from ui import UI
from io_565 import Exporter565
from io_vld import VLDFile, VLDHelper
from io_vox import VOXHelper

camera = Camera()
voxels = None
overlay = None
grid = None
cursor = None
exporter = None
ui = None

current_width = 800.0
current_height = 600.0
projection = None
ortho = None

def world_size_changed(value):
  camera.distance = value

def cell_size_changed(value):
  cursor.cell_size = value
  disp = value * 0.5
  camera.set_unit(value)
  camera.target = np.array([disp, disp, disp], dtype=np.float32)
  camera.target_destination = np.array([disp, disp, disp], dtype=np.float32)

def key_callback(window, key, scancode, action, mods):
  camera.key_callback(window, key, scancode, action, mods)
  voxels.on_key_event(key, action, camera, overlay)
  overlay.on_key_event(key, action)
  grid.on_key_event(key, action)
  exporter.on_key_event(key, action)

  """Temporary .vld"""
  if key == glfw.KEY_S and action == glfw.PRESS:
    if glfw.get_key(window, glfw.KEY_LEFT_CONTROL) == glfw.PRESS or \
       glfw.get_key(window, glfw.KEY_RIGHT_CONTROL) == glfw.PRESS:
      vld = VLDFile()
      data = {
        "voxels": VLDHelper.export_voxels(voxels),
        "grid": VLDHelper.export_grid(grid)
      }
      vld.save("scene.vld", data)
   
  if key == glfw.KEY_O and action == glfw.PRESS:
    if glfw.get_key(window, glfw.KEY_LEFT_CONTROL) == glfw.PRESS or \
       glfw.get_key(window, glfw.KEY_RIGHT_CONTROL) == glfw.PRESS:
      vld = VLDFile()
      sections = vld.open("scene.vld")
      if "voxels" in sections:
        VLDHelper.import_voxels(voxels, sections["voxels"])
      if "grid" in sections:
        VLDHelper.import_grid(grid, sections["grid"])
  
  """Temporay .vox"""
  if key == glfw.KEY_V and action == glfw.PRESS:
    if glfw.get_key(window, glfw.KEY_LEFT_CONTROL) == glfw.PRESS or \
       glfw.get_key(window, glfw.KEY_RIGHT_CONTROL) == glfw.PRESS:
      VOXHelper.import_vox(voxels, "scene.vox", voxel_size=1, center=True, region_size=256)


def getOrtho(width, height):
  left = -width / 2
  right = width / 2
  bottom = -height / 2
  top = height / 2
  near = -1000.0
  far = 1000.0
  return np.array([
    [2.0 / (right - left), 0, 0, -(right + left) / (right - left)],
    [0, 2.0 / (top - bottom), 0, -(top + bottom) / (top - bottom)],
    [0, 0, -2.0 / (far - near), -(far + near) / (far - near)],
    [0, 0, 0, 1]
  ], dtype=np.float32)

def getPerspective(width, height):
  fov = np.radians(45.0)
  aspect = width / height
  near = 0.1
  far = 3000.0
  
  f = 1.0 / np.tan(fov * 0.5)
  return np.array([
    [f/aspect, 0, 0, 0],
    [0, f, 0, 0],
    [0, 0, (far+near)/(near-far), (2*far*near)/(near-far)],
    [0, 0, -1, 0]
  ], dtype=np.float32)

def window_size_callback(window, width, height):
  global current_width, current_height, projection, ortho
  
  current_width = float(width)
  current_height = float(height)
  
  overlay.translation = [-float(width) * 0.5, - float(height) * 0.5, 0.0]
  glViewport(0, 0, width, height)
  
  projection = getPerspective(current_width, current_height)
  ortho = getOrtho(current_width, current_height)
  
  ui.update_size(width, height)

def main():
  global current_width, current_height, projection, ortho
  global voxels, overlay, grid, cursor, exporter, ui
  
  
  if not glfw.init():
    return
    
  window = glfw.create_window(int(current_width), int(current_height), "Voxelander - Voxel Editor", None, None)
  if not window:
    glfw.terminate()
    return
  
  glfw.make_context_current(window)
  
  ui = UI(window, int(current_width), int(current_height))
  ui.set_callbacks(
    lambda: print("open"),
    lambda: print("save")
  )

  glfw.set_key_callback(window, key_callback)
  glfw.set_window_size_callback(window, window_size_callback)

  grid = Grid()
  overlay = Overlay(current_width, current_height)
  voxels = Voxels()
  cursor = TargetCursor(camera)
  cursor.set_grid_size(1)
  cursor.set_cell_size(1.0)
  
  grid.cell_size_changed = cell_size_changed
  grid.world_size_changed = world_size_changed

  exporter = Exporter565(voxels)
  exporter.set_color_levels(red=0.9, green=1.0, blue=1.5)
  exporter.set_brightness(0)
  exporter.set_grid_size(256)
  # exporter.set_swap_yz(True)
  exporter.set_invert_y(True)
  
  glEnable(GL_DEPTH_TEST)
  glClearColor(0.2, 0.3, 0.3, 1.0)
  
  projection = getPerspective(current_width, current_height)
  ortho = getOrtho(current_width, current_height)
  
  camera.set_unit(1.0)
  camera.set_movement_speed(10.0)
  camera.set_delays(0.5, 0.25)
  
  last_time = time.time()
  while not glfw.window_should_close(window):
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time
    
    glfw.poll_events()
    ui.process_inputs()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    camera.update(delta_time)
    
    view = camera.get_view_matrix()
    pv = projection @ view
    
    voxels.draw(pv)
    grid.draw_grid(pv)
    cursor.draw(camera.target, pv)
    grid.draw(pv)
    overlay.draw(ortho)
    
    glViewport(0, 0, int(current_width), int(current_height))
    ui.draw()
        
    glfw.swap_buffers(window)
  
  cursor.cleanup()
  overlay.cleanup()
  voxels.cleanup()
  grid.cleanup()
  ui.cleanup()
  
  glfw.terminate()

if __name__ == '__main__':
  main()
