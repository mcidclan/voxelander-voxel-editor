import struct
import os
import io

class VOXImporter:
  def __init__(self):
    self.models = []
    self.palette = []
    self.current_model = None
    self.transforms = {}
    self.shapes = {}
    self.groups = {}
    self.has_scene_graph = False

  def load_vox_file(self, filepath):
    if not os.path.exists(filepath):
      print(f"File {filepath} does not exist")
      return [], []

    with open(filepath, 'rb') as f:
      magic = f.read(4)
      if magic != b'VOX ':
        print("Not a valid .vox file")
        return [], []

      version = struct.unpack('<I', f.read(4))[0]

      main_chunk = self._read_chunk(f)
      if main_chunk['id'] != b'MAIN':
        print("Missing MAIN chunk")
        return [], []

      self._parse_chunks(f, main_chunk['child_size'])

    return self.models, self.palette

  def _read_chunk(self, f):
    chunk_id = f.read(4)
    if len(chunk_id) < 4:
      return None

    content_size = struct.unpack('<I', f.read(4))[0]
    child_size = struct.unpack('<I', f.read(4))[0]

    return {
      'id': chunk_id,
      'content_size': content_size,
      'child_size': child_size
    }

  def _parse_chunks(self, f, remaining_size):
    while remaining_size > 0:
      chunk = self._read_chunk(f)
      if chunk is None:
        break

      start_pos = f.tell()

      if chunk['id'] == b'SIZE':
        self._parse_size_chunk(f, chunk['content_size'])
      elif chunk['id'] == b'XYZI':
        xyzi_data = f.read(chunk['content_size'])
        self._parse_xyzi_chunk(io.BytesIO(xyzi_data), chunk['content_size'])
      elif chunk['id'] == b'RGBA':
        self._parse_rgba_chunk(f, chunk['content_size'])
      elif chunk['id'] == b'nTRN':
        self.has_scene_graph = True
        self._parse_ntrn_chunk(f, chunk['content_size'])
      elif chunk['id'] == b'nGRP':
        self.has_scene_graph = True
        self._parse_ngrp_chunk(f, chunk['content_size'])
      elif chunk['id'] == b'nSHP':
        self.has_scene_graph = True
        self._parse_nshp_chunk(f, chunk['content_size'])
      else:
        f.seek(start_pos + chunk['content_size'])

      if chunk['child_size'] > 0:
        self._parse_chunks(f, chunk['child_size'])

      remaining_size -= 12 + chunk['content_size'] + chunk['child_size']

  def _parse_size_chunk(self, f, size):
    x, y, z = struct.unpack('<3I', f.read(12))
    self.current_model = {
      'size': (x, y, z),
      'voxels': [],
      'id': len(self.models)
    }

  def _parse_xyzi_chunk(self, f, size):
    if self.current_model is None:
      self.current_model = {
        'size': (256, 256, 256),
        'voxels': [],
        'id': len(self.models)
      }

    num_voxels_bytes = f.read(4)
    if len(num_voxels_bytes) < 4:
      return

    num_voxels = struct.unpack('<I', num_voxels_bytes)[0]
    expected_size = num_voxels * 4

    voxel_data = f.read(expected_size)
    if len(voxel_data) < expected_size:
      return

    voxels = []
    positions_in_model = set()
    
    for i in range(0, expected_size, 4):
      x, y, z, color_index = struct.unpack('<4B', voxel_data[i:i+4])
      pos = (x, y, z)
      
      if pos not in positions_in_model:
        positions_in_model.add(pos)
        voxels.append((x, y, z, color_index))

    self.current_model['voxels'] = voxels
    self.models.append(self.current_model)
    self.current_model = None

  def _parse_rgba_chunk(self, f, size):
    self.palette = []
    for _ in range(256):
      r, g, b, a = struct.unpack('<4B', f.read(4))
      self.palette.append((r/255.0, g/255.0, b/255.0, a/255.0))

  def _parse_ntrn_chunk(self, f, size):
    node_id = struct.unpack('<I', f.read(4))[0]
    node_attrs = self._read_dict(f)
    child_node_id = struct.unpack('<I', f.read(4))[0]
    reserved_id = struct.unpack('<I', f.read(4))[0]
    layer_id = struct.unpack('<I', f.read(4))[0]
    num_frames = struct.unpack('<I', f.read(4))[0]
    
    frames = []
    for _ in range(num_frames):
      frame_attrs = self._read_dict(f)
      frames.append(frame_attrs)
    
    transform = {
      'translation': [0, 0, 0],
      'rotation': 0
    }
    
    if frames and '_t' in frames[0]:
      t_str = frames[0]['_t']
      coords = t_str.split()
      if len(coords) >= 3:
        try:
          transform['translation'] = [int(coords[0]), int(coords[1]), int(coords[2])]
        except ValueError:
          transform['translation'] = [0, 0, 0]
    
    self.transforms[node_id] = {
      'child_node_id': child_node_id,
      'transform': transform,
      'layer_id': layer_id
    }

  def _parse_ngrp_chunk(self, f, size):
    node_id = struct.unpack('<I', f.read(4))[0]
    node_attrs = self._read_dict(f)
    num_children = struct.unpack('<I', f.read(4))[0]
    
    children = []
    for _ in range(num_children):
      child_id = struct.unpack('<I', f.read(4))[0]
      children.append(child_id)
    
    self.groups[node_id] = {
      'children': children,
      'attrs': node_attrs
    }

  def _parse_nshp_chunk(self, f, size):
    node_id = struct.unpack('<I', f.read(4))[0]
    node_attrs = self._read_dict(f)
    num_models = struct.unpack('<I', f.read(4))[0]
    
    models = []
    for _ in range(num_models):
      model_id = struct.unpack('<I', f.read(4))[0]
      model_attrs = self._read_dict(f)
      models.append({'id': model_id, 'attrs': model_attrs})
    
    self.shapes[node_id] = {
      'models': models,
      'attrs': node_attrs
    }

  def _read_dict(self, f):
    num_pairs = struct.unpack('<I', f.read(4))[0]
    attrs = {}
    for _ in range(num_pairs):
      key = self._read_string(f)
      value = self._read_string(f)
      attrs[key] = value
    return attrs

  def _read_string(self, f):
    length = struct.unpack('<I', f.read(4))[0]
    return f.read(length).decode('utf-8')

  def get_model_instances(self):
    if not self.has_scene_graph:
      instances = []
      for i, model in enumerate(self.models):
        instances.append({
          'model_id': i,
          'transform': [0, 0, 0]
        })
      return instances
    
    instances = []
    processed_shapes = set()
    
    def collect_transforms(node_id, cumulative_transform=[0, 0, 0]):
      if node_id in self.transforms:
        trans_data = self.transforms[node_id]
        new_transform = [
          cumulative_transform[0] + trans_data['transform']['translation'][0],
          cumulative_transform[1] + trans_data['transform']['translation'][1],
          cumulative_transform[2] + trans_data['transform']['translation'][2]
        ]
        collect_transforms(trans_data['child_node_id'], new_transform)
      
      elif node_id in self.groups:
        for child_id in self.groups[node_id]['children']:
          collect_transforms(child_id, cumulative_transform)
      
      elif node_id in self.shapes and node_id not in processed_shapes:
        processed_shapes.add(node_id)
        shape_data = self.shapes[node_id]
        for model_info in shape_data['models']:
          instances.append({
            'model_id': model_info['id'],
            'transform': cumulative_transform[:]
          })
    
    for root_id in self.transforms:
      if not any(trans['child_node_id'] == root_id for trans in self.transforms.values()):
        collect_transforms(root_id)
    
    if not instances:
      for i, model in enumerate(self.models):
        instances.append({
          'model_id': i,
          'transform': [0, 0, 0]
        })
    
    return instances

class VOXHelper:
  DEFAULT_PALETTE = [
    (1.0, 1.0, 1.0, 1.0),
    (1.0, 1.0, 0.8, 1.0), (1.0, 1.0, 0.6, 1.0), (1.0, 1.0, 0.4, 1.0),
    (1.0, 1.0, 0.2, 1.0), (1.0, 1.0, 0.0, 1.0), (1.0, 0.8, 0.0, 1.0),
    (1.0, 0.6, 0.0, 1.0), (1.0, 0.4, 0.0, 1.0), (1.0, 0.2, 0.0, 1.0),
    (1.0, 0.0, 0.0, 1.0), (1.0, 0.0, 0.2, 1.0), (1.0, 0.0, 0.4, 1.0),
    (1.0, 0.0, 0.6, 1.0), (1.0, 0.0, 0.8, 1.0), (1.0, 0.0, 1.0, 1.0),
  ] + [(0.5, 0.5, 0.5, 1.0)] * 240

  @staticmethod
  def import_vox(voxels, filepath, voxel_size=1, center=False, region_size=None):
    importer = VOXImporter()
    models, palette = importer.load_vox_file(filepath)
    if not models:
      return
    if not palette:
      palette = VOXHelper.DEFAULT_PALETTE
    
    model_instances = importer.get_model_instances()
    
    voxels.blocks.clear()
    voxels.batches.clear()
    
    global_positions = set()
    all_world_positions = []
    
    for instance in model_instances:
      model_id = instance['model_id']
      if model_id >= len(models):
        continue
      
      model = models[model_id]
      transform = instance['transform']
      
      for x, y, z, color_index in model['voxels']:
        world_x = x + transform[0]
        world_y = y + transform[1]
        world_z = z + transform[2]
        all_world_positions.append((world_x, world_y, world_z, color_index))
    
    global_offset_x, global_offset_y, global_offset_z = 0, 0, 0
    
    if center and all_world_positions:
      min_x = min(pos[0] for pos in all_world_positions)
      max_x = max(pos[0] for pos in all_world_positions)
      min_y = min(pos[1] for pos in all_world_positions)
      max_y = max(pos[1] for pos in all_world_positions)
      min_z = min(pos[2] for pos in all_world_positions)
      max_z = max(pos[2] for pos in all_world_positions)
      
      global_offset_x = -(min_x + max_x) // 2
      global_offset_y = -(min_y + max_y) // 2
      global_offset_z = -(min_z + max_z) // 2
    
    for world_x, world_y, world_z, color_index in all_world_positions:
      final_x = world_x + global_offset_x
      final_y = world_y + global_offset_y
      final_z = world_z + global_offset_z
      
      pos_x = final_x * voxel_size
      pos_y = final_z * voxel_size
      pos_z = final_y * voxel_size
      
      final_pos = (pos_x, pos_y, pos_z)
      
      if final_pos in global_positions:
        continue
      global_positions.add(final_pos)
      
      if region_size is not None:
        half_region = region_size // 2
        if center:
          if not (-half_region <= pos_x < half_region and 
                  -half_region <= pos_y < half_region and 
                  -half_region <= pos_z < half_region):
            continue
        else:
          if not (0 <= pos_x < region_size and 
                  0 <= pos_y < region_size and 
                  0 <= pos_z < region_size):
            continue
      
      if color_index > 0 and color_index <= len(palette):
        color = palette[color_index - 1]
        rgb_color = [color[0], color[1], color[2]]
      else:
        rgb_color = [1.0, 1.0, 1.0]
      
      voxels.add_batch(final_pos, voxel_size, rgb_color)

  @staticmethod
  def get_vox_info(filepath):
    importer = VOXImporter()
    try:
      models, palette = importer.load_vox_file(filepath)
      model_instances = importer.get_model_instances()
      
      info = {
        'num_models': len(models),
        'num_instances': len(model_instances),
        'has_custom_palette': len(palette) > 0,
        'has_scene_graph': importer.has_scene_graph,
        'models_info': []
      }
      
      for i, model in enumerate(models):
        model_info = {
          'index': i,
          'size': model['size'],
          'num_voxels': len(model['voxels'])
        }
        info['models_info'].append(model_info)
      
      return info
    except Exception as e:
      return {'error': str(e)}
