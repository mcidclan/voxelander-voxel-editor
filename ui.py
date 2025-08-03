import imgui
import imgui.integrations.glfw as imgui_glfw
from OpenGL.GL import *
import glfw

class UI:
  def __init__(self, window, width, height):
    self.width = width
    self.height = height
    self.menu_height = 16
    self.bottom_bar_height = 16
    
    imgui.create_context()
    self.renderer = imgui_glfw.GlfwRenderer(window)
    
    self.open_callback = lambda: print("open")
    self.save_callback = lambda: print("save")
    
  def set_callbacks(self, open_callback=None, save_callback=None):
    if open_callback:
      self.open_callback = open_callback
    if save_callback:
      self.save_callback = save_callback
    
  def update_size(self, width, height):
    self.width = width
    self.height = height
    
  def process_inputs(self):
    self.renderer.process_inputs()
    
  def draw(self):
    imgui.new_frame()
    
    imgui.set_next_window_position(0, 0)
    imgui.set_next_window_size(self.width, self.menu_height)
    
    imgui.push_style_color(imgui.COLOR_WINDOW_BACKGROUND, 0.2, 0.2, 0.2, 1.0)
    imgui.push_style_color(imgui.COLOR_MENUBAR_BACKGROUND, 0.0, 0.0, 0.0, 0.0)
    imgui.push_style_var(imgui.STYLE_WINDOW_MIN_SIZE, (0, 0))
    imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, (8, 8))
    
    if imgui.begin("MenuBar", flags=imgui.WINDOW_NO_TITLE_BAR | 
                                   imgui.WINDOW_NO_RESIZE | 
                                   imgui.WINDOW_NO_MOVE |
                                   imgui.WINDOW_NO_SCROLLBAR |
                                   imgui.WINDOW_MENU_BAR):
      
      if imgui.begin_menu_bar():
        if imgui.begin_menu("File"):
          if imgui.menu_item("Open")[0]:
            self.open_callback()
          if imgui.menu_item("Save")[0]:
            self.save_callback()
          imgui.menu_item("Exit")[0]
          imgui.end_menu()
        imgui.end_menu_bar()
        
    imgui.end()
                    
    imgui.pop_style_var(2)
    imgui.pop_style_color(2)
    
    imgui.set_next_window_position(0, self.height - self.bottom_bar_height)
    imgui.set_next_window_size(self.width, self.bottom_bar_height)
    
    imgui.push_style_color(imgui.COLOR_WINDOW_BACKGROUND, 0.2, 0.2, 0.2, 1.0)
    imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, (8, 2))
    
    if imgui.begin("Status", flags=imgui.WINDOW_NO_TITLE_BAR | 
                                   imgui.WINDOW_NO_RESIZE | 
                                   imgui.WINDOW_NO_MOVE |
                                   imgui.WINDOW_NO_SCROLLBAR):
      text = "Status: Ready"
      window_width = imgui.get_window_size()[0]
      text_width = imgui.calc_text_size(text)[0]
      imgui.set_cursor_pos_x(window_width - text_width - 10)
      imgui.text(text)
    imgui.end()

    
    imgui.pop_style_var()
    imgui.pop_style_color()
    
    imgui.render()
    self.renderer.render(imgui.get_draw_data())
    
  def cleanup(self):
    self.renderer.shutdown()
