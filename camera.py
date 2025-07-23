import glfw
import numpy as np
import time

class Camera:
 def __init__(self):
   self.distance = 16.0
   self.yaw = 180.0
   self.pitch = 0.0
   self.target = np.array([0.5, 0.5, 0.5], dtype=np.float32)
   
   self.target_distance = self.distance
   self.zoom_speed = 5.0
   self.min_distance = 1.0
   self.max_distance = 512.0

   self.unit = 1.0
   self.movement_speed = 2.0
   self.initial_delay = 0.3
   self.repeat_delay = 0.1
   
   self.target_destination = self.target.copy()
   self.is_moving = False
   self.last_move_time = 0.0
   self.initial_move_done = False
   
   self.pressed_keys = set()
   
 def update(self, delta_time):
   if not np.allclose(self.target, self.target_destination, atol=0.001):
     self.is_moving = True
     alpha = 1.0 - np.exp(-self.movement_speed * delta_time)
     self.target = self.target * (1 - alpha) + self.target_destination * alpha
   else:
     if self.is_moving:
       self.target = self.target_destination.copy()
       self.is_moving = False
   
   if abs(self.distance - self.target_distance) > 0.001:
     alpha = 1.0 - np.exp(-self.zoom_speed * delta_time)
     interpolated = (1 - alpha) * self.distance + alpha * self.target_distance
     self.distance = np.clip(interpolated, self.min_distance, self.max_distance)
   else:
     self.distance = self.target_distance

   current_time = time.time()
   if self.pressed_keys:
     if not self.initial_move_done:
       if current_time - self.last_move_time >= self.initial_delay:
         self._process_movement()
         self.initial_move_done = True
         self.last_move_time = current_time
     else:
       if current_time - self.last_move_time >= self.repeat_delay:
         self._process_movement()
         self.last_move_time = current_time
 
 def _process_movement(self):
   movement = np.array([0.0, 0.0, 0.0], dtype=np.float32)
   
   for key in self.pressed_keys:
     if key == 'B':
       movement[2] -= self.unit
     elif key == 'F':
       movement[2] += self.unit
     elif key == 'L':
       movement[0] -= self.unit
     elif key == 'R':
       movement[0] += self.unit
     elif key == 'U':
       movement[1] += self.unit
     elif key == 'D':
       movement[1] -= self.unit
   
   if not np.allclose(movement, [0, 0, 0]):
     self.target_destination += movement
 
 def on_key_press(self, key_name):
   if key_name in ['B', 'F', 'L', 'R', 'U', 'D']:
     if key_name not in self.pressed_keys:
       self.pressed_keys.add(key_name)
       self._process_movement()
       self.last_move_time = time.time()
       self.initial_move_done = False
 
 def on_key_release(self, key_name):
   if key_name in self.pressed_keys:
     self.pressed_keys.remove(key_name)
     if not self.pressed_keys:
       self.initial_move_done = False
 
 def key_callback(self, window, key, scancode, action, mods):
   if action in [glfw.PRESS, glfw.REPEAT]:
     if key == glfw.KEY_B:
       self.on_key_press('B')
     elif key == glfw.KEY_F:
       self.on_key_press('F')
     elif key == glfw.KEY_L:
       self.on_key_press('L')
     elif key == glfw.KEY_R:
       self.on_key_press('R')
     elif key == glfw.KEY_U:
       self.on_key_press('U')
     elif key == glfw.KEY_D:
       self.on_key_press('D')
     
     elif key == glfw.KEY_LEFT:
       self.rotate_yaw(-5)
     elif key == glfw.KEY_RIGHT:
       self.rotate_yaw(5)
     elif key == glfw.KEY_UP:
       self.rotate_pitch(5)
     elif key == glfw.KEY_DOWN:
       self.rotate_pitch(-5)

     elif key == glfw.KEY_6:
       self.target_distance = max(self.min_distance, self.target_distance + 1.0)
     elif key == glfw.KEY_EQUAL:
       self.target_distance = min(self.max_distance, self.target_distance - 1.0)

   elif action == glfw.RELEASE:
     if key == glfw.KEY_B:
       self.on_key_release('B')
     elif key == glfw.KEY_F:
       self.on_key_release('F')
     elif key == glfw.KEY_L:
       self.on_key_release('L')
     elif key == glfw.KEY_R:
       self.on_key_release('R')
     elif key == glfw.KEY_U:
       self.on_key_release('U')
     elif key == glfw.KEY_D:
       self.on_key_release('D')
 
 def set_unit(self, unit):
   self.unit = unit
 
 def set_movement_speed(self, speed):
   self.movement_speed = speed
 
 def set_delays(self, initial_delay, repeat_delay):
   self.initial_delay = initial_delay
   self.repeat_delay = repeat_delay
 
 def adjust_distance(self, delta):
   self.distance = np.clip(self.distance + delta, 1.0, 1024.0)

 def rotate_yaw(self, angle_deg):
   self.yaw += angle_deg
 
 def rotate_pitch(self, angle_deg):
   self.pitch += angle_deg
   self.pitch = np.clip(self.pitch, -89.0, 89.0)
 
 def get_position(self):
   yaw_rad = np.radians(self.yaw)
   pitch_rad = np.radians(self.pitch)
   
   x = self.distance * np.cos(pitch_rad) * np.sin(yaw_rad)
   y = self.distance * np.sin(pitch_rad)
   z = self.distance * np.cos(pitch_rad) * np.cos(yaw_rad)
   return self.target + np.array([x, y, z], dtype=np.float32)
 
 def get_view_matrix(self):
   yaw_rad = np.radians(self.yaw)
   pitch_rad = np.radians(self.pitch)
   
   x = self.distance * np.cos(pitch_rad) * np.sin(yaw_rad)
   y = self.distance * np.sin(pitch_rad)
   z = self.distance * np.cos(pitch_rad) * np.cos(yaw_rad)
   position = self.target + np.array([x, y, z], dtype=np.float32)
   
   return self.look_at(position, self.target, np.array([0.0, 1.0, 0.0], dtype=np.float32))
 
 @staticmethod
 def look_at(eye, center, up):
   f = eye - center
   f = f / np.linalg.norm(f)
   
   s = np.cross(f, up)
   s = s / np.linalg.norm(s)
   u = np.cross(s, f)
   
   view = np.identity(4, dtype=np.float32)
   view[0, :3] = s
   view[1, :3] = u
   view[2, :3] = f
   view[0, 3] = -np.dot(s, eye)
   view[1, 3] = -np.dot(u, eye)
   view[2, 3] = -np.dot(f, eye)
   
   return view
