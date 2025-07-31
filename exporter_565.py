import struct
import math
import numpy as np

class Exporter565:
  def __init__(self, voxels):
    self.voxels = voxels
    self.OPT_MODEL_RED_LEVEL = 0.9
    self.OPT_MODEL_GREEN_LEVEL = 1.0
    self.OPT_MODEL_BLUE_LEVEL = 1.5
    self.OPT_MODEL_BRIGHTNESS = 0
    self.SIZE = 256
    self.HALF = self.SIZE / 2
    self.swap_yz = False
    self.invert_y = False

  def on_key_event(self, key, action):
    import glfw
    if key == glfw.KEY_E and action == glfw.RELEASE:
      self.export_to_file("object_0.bin")
      print("Export completed! File saved: object_0.bin")

  def export_to_file(self, filename="./object_0.bin"):
    coords = {}

    for (x, y, z), info in self.voxels.blocks.items():
      block_id = info['block_id']
      batch = self.voxels.batches[block_id]
      voxel_local_index = self._find_voxel_local_index(batch, x, y, z)
      color = self._get_voxel_color(batch['vertices'], voxel_local_index)
      smoothed_color = self._smooth_color_with_neighbors(x, y, z, color)

      export_x, export_y, export_z = self._transform_coordinates(x, y, z)
      coord_key = int((export_x + self.HALF) + (export_y + self.HALF) * self.SIZE + (export_z + self.SIZE) * self.SIZE * self.SIZE)
     
      if (export_x >= -self.HALF) and (export_x < self.HALF) and (export_y >= -self.HALF) and (export_y < self.HALF) and (export_z >= -self.HALF) and (export_z < self.HALF):
        r = self.OPT_MODEL_BRIGHTNESS + math.floor(smoothed_color[0] * 0x1F * self.OPT_MODEL_RED_LEVEL)
        g = self.OPT_MODEL_BRIGHTNESS + math.floor(smoothed_color[1] * 0x3F * self.OPT_MODEL_GREEN_LEVEL)
        b = self.OPT_MODEL_BRIGHTNESS + math.floor(smoothed_color[2] * 0x1F * self.OPT_MODEL_BLUE_LEVEL)

        r = min(r, 0x1F) if r >= 0 else 0
        g = min(g, 0x3F) if g >= 0 else 0
        b = min(b, 0x1F) if b >= 0 else 0
        
        if coord_key not in coords:
          coords[coord_key] = [r, g, b, export_x, export_y, export_z, 1.0]
        else:
          _c = coords[coord_key]
          _c[0] += r
          _c[1] += g
          _c[2] += b
          _c[6] += 1.0

    with open(filename, "wb") as f:
      for key in coords:
        coord = coords[key]
        coord[0] /= coord[6]
        coord[1] /= coord[6]
        coord[2] /= coord[6]

        color = int(coord[0]) | (int(coord[1]) << 5) | (int(coord[2]) << 11)

        f.write(struct.pack("<H", color))
        f.write(struct.pack("<b", int(coord[3])))
        f.write(struct.pack("<b", int(coord[4])))
        f.write(struct.pack("<b", int(coord[5])))
        f.write(struct.pack("<b", 1))

    print(f"Export completed: {len(coords)} voxels written to {filename}")

  def _transform_coordinates(self, x, y, z):
    if self.invert_y:
      return x, -y, z
    return x, y, z

  def _get_voxel_color(self, vertices, voxel_index):
    vertex_start = voxel_index * 24 * 9
    if vertex_start + 8 < len(vertices):
      return [
        vertices[vertex_start + 6],
        vertices[vertex_start + 7],
        vertices[vertex_start + 8]
      ]
    return [1.0, 1.0, 1.0]

  def _smooth_color_with_neighbors(self, x, y, z, base_color):
    neighbors = [
      (x+1, y, z), (x-1, y, z),
      (x, y+1, z), (x, y-1, z),
      (x, y, z+1), (x, y, z-1)
    ]
   
    total_color = np.array(base_color)
    count = 1.0
   
    for nx, ny, nz in neighbors:
      neighbor_key = (nx, ny, nz)
      if neighbor_key in self.voxels.blocks:
        info = self.voxels.blocks[neighbor_key]
        block_id = info['block_id']
        batch = self.voxels.batches[block_id]
        voxel_local_index = self._find_voxel_local_index(batch, nx, ny, nz)
        neighbor_color = self._get_voxel_color(batch['vertices'], voxel_local_index)
        total_color += np.array(neighbor_color)
        count += 1.0
    
    smoothed = total_color / count
    return [smoothed[0], smoothed[1], smoothed[2]]

  def _find_voxel_local_index(self, batch, x, y, z):
    px, py, pz = batch['position']
    size = batch['size']
    dx = (x - px) // size
    dy = (y - py) // size
    dz = (z - pz) // size
    dim = int(batch['dim'])
    return dx + dy * dim + dz * dim * dim

  def set_color_levels(self, red=0.9, green=1.0, blue=1.5):
    self.OPT_MODEL_RED_LEVEL = red
    self.OPT_MODEL_GREEN_LEVEL = green
    self.OPT_MODEL_BLUE_LEVEL = blue

  def set_brightness(self, brightness=0):
    self.OPT_MODEL_BRIGHTNESS = brightness

  def set_grid_size(self, size=256):
    self.SIZE = size
    self.HALF = size / 2

  def set_invert_y(self, invert=True):
    self.invert_y = invert
  
  def set_swap_yz(self, swap=True):
    self.swap_yz = swap
