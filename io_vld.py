import struct

SECTION_NAME_SIZE = 256
UINT32_SIZE = 4

class VLDFile:
  def __init__(self):
    self.sections = {}

  def save(self, path, data_dict):
    with open(path, 'wb') as f:
      for name, binary_data in data_dict.items():
        name_bytes = name.encode('ascii')[:SECTION_NAME_SIZE]
        name_bytes = name_bytes.ljust(SECTION_NAME_SIZE, b'\x00')
        size_bytes = struct.pack('<I', len(binary_data))
        f.write(name_bytes)
        f.write(size_bytes)
        f.write(binary_data)

  def open(self, path):
    self.sections = {}
    with open(path, 'rb') as f:
      while True:
        name_bytes = f.read(SECTION_NAME_SIZE)
        if not name_bytes or len(name_bytes) < SECTION_NAME_SIZE:
          break
        name = name_bytes.rstrip(b'\x00').decode('ascii')
        size_bytes = f.read(UINT32_SIZE)
        if not size_bytes or len(size_bytes) < UINT32_SIZE:
          break
        size = struct.unpack('<I', size_bytes)[0]
        data = f.read(size)
        if len(data) < size:
          raise IOError(f"Unexpected end of file while reading section '{name}'")
        self.sections[name] = data
    return self.sections

class VLDHelper:
  @staticmethod
  def export_voxels(voxels):
    data = bytearray()
    for pos, info in voxels.blocks.items():
      x, y, z = pos
      size = info['size']
      color = [1.0, 1.0, 1.0]
      for b in voxels.batches:
        if b is None:
          continue
        if pos in voxels.blocks and voxels.blocks[pos]['block_id'] == voxels.batches.index(b):
          v = b['vertices']
          if len(v) >= 9:
            color = v[6:9]
          break
      data.extend(struct.pack('<3iI3f', x, y, z, size, *color))
    return bytes(data)

  @staticmethod
  def import_voxels(voxels, binary_data):
    voxels.blocks.clear()
    voxels.batches.clear()
    entry_size = struct.calcsize('<3iI3f')
    for i in range(0, len(binary_data), entry_size):
      x, y, z, size, r, g, b = struct.unpack('<3iI3f', binary_data[i:i+entry_size])
      voxels.add_batch((x, y, z), size, [r, g, b])

  @staticmethod
  def export_grid(grid):
    return struct.pack('<2I', grid.world_size, grid.cell_size)

  @staticmethod
  def import_grid(grid, binary_data):
    world_size, cell_size = struct.unpack('<2I', binary_data)
    grid.world_size = world_size
    grid.cell_size = cell_size
    grid._update_geometry()
    grid._update_arrow_geometry()
