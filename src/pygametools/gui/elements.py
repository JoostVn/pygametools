import pygame
import pygame.gfxdraw
import numpy as np
from .base import load_theme, State
from abc import ABC, abstractmethod


"""
TODO:
    - Docstrings
    - Labels
        - Hoover function
    - Application ticker stats with optional in screen printing
    - Textbox (use old GUI)
    - IF/Else update func optimization

"""




class Element(ABC):
        
    
    def __init__(self, theme_name, **kwargs):
        """
        Template for GUI elements.

        Parameters
        ----------
        theme : string
            Name of the theme json file in the themes folder.

        """
        pygame.init()
        self.font_size = kwargs.get('font_size', 10)
        self.font_name = kwargs.get('font_name', 'msreferencesansserif')
        
        self.theme = load_theme(theme_name)
        self.font = pygame.font.SysFont(self.font_name, self.font_size)
        self.state = State.PASSIVE
        self.set_theme()

    def __repr__(self):
        return f'{self.__class__.__name__}|{self.state}'

    def _inscope_mouse(self, mouse_pos):
        """
        Return True if the given mouse position (x,y) sits within the margins
        of the element box.the box itself is imlemented in inherited classes. 

        Parameters
        ----------
        mouse_pos : tuple
            Mouse position.

        Returns
        -------
        in_scope : bool
            True if mouse is in box, else false.
        """
        in_scope = all([
            mouse_pos[0] > self._box[0],
            mouse_pos[0] < self._box[1],
            mouse_pos[1] > self._box[2],
            mouse_pos[1] < self._box[3]])
        return in_scope

    @abstractmethod
    def set_theme(self):
        """
        Reloads all theme colors. Used at init or called externally when 
        self.theme has been changed.
        """
        pass
    
    @property
    @abstractmethod
    def _box(self):
        """
        Return the (left, right, top, bottom) coordinates of the bounding box
        for the element that should trigger a hoover state.
        """
        pass

    @abstractmethod
    def update(self, key_events, mouse_pos):
        """
        Update element state and executes actions
        """
        pass
    
    @abstractmethod
    def draw(self, screen):
        """
        Draw the element to the screen.
        """


class Button(Element):

    def __init__(self, text, func, pos, width, height, 
                 theme_name='default', **kwargs):
        """
        Clickable button.

        Parameters
        ----------
        text : String
            Text on the button.
        func : function or method
            Function to be executed when the button is clicked.
        pos : Array-like
            (x,y) Position of the button.
        width : Int
            Pixel width of the button.
        height : Int
            Pixel height of the button.
        theme_name : String, optional
            Name of the theme JSON file to be used. The default is 
            'default_dark'.
        """
        super().__init__(theme_name, **kwargs)
        
        # Functional attributes
        self.text = text
        self.func = func
        self.pos = np.array(pos)
        self.width = width
        self.height = height
    
    def set_theme(self):
        self.colors = {
           State.PASSIVE: {
               'face':self.theme['1'],
               'edge':self.theme['3'],
               'font':self.theme['5']},
           State.HOOVER: {
               'face':self.theme['2'],
               'edge':self.theme['3'],
               'font':self.theme['6']},
           State.TRIGGERED: {
               'face':self.theme['3'],
               'edge':self.theme['background'],
               'font':self.theme['6']},
           State.ACTIVE: {
               'face':self.theme['2'],
               'edge':self.theme['3'],
               'font':self.theme['6']}
            }
        
    @property
    def _box(self):
        box = (
            self.pos[0],
            self.pos[0] + self.width,
            self.pos[1],
            self.pos[1] + self.height)
        return box

    def update(self, key_events, mouse_pos):
        """
        Sets the button state and executes actions based on mouse behaviour.
        """
        in_box = self._inscope_mouse(mouse_pos)
        click = pygame.BUTTON_LEFT in key_events['down']
        release = pygame.BUTTON_LEFT in key_events['up']
        
        # Trigger when in box and button is clicked
        if in_box and click:
            self.state = State.TRIGGERED
        
        # Execute function triggered, in box, and mouse is released
        elif self.state == State.TRIGGERED and in_box and release:
            self.func()
            self.state = State.HOOVER
        
        # "Activate" when mouse is held but no longer in box
        elif self.state == State.TRIGGERED and not in_box:
            self.state = State.ACTIVE
        
        # Retrigger when active and mouse is moved back in box
        elif self.state == State.ACTIVE and in_box:
            self.state = State.TRIGGERED
            
        # Set to passive when active but mouse is released
        elif self.state == State.ACTIVE and release and not in_box:
            self.state = State.PASSIVE
            
        # Hoover when passive and mouse moves in box
        elif self.state == State.PASSIVE and in_box:
            self.state = State.HOOVER
            
        # Passive when hoover and mouse moves out of box
        elif self.state == State.HOOVER and not in_box:
            self.state = State.PASSIVE
        
    def draw(self, screen):
        """
        Draw the button.
        """
        col = self.colors[self.state]
        x, y = self.pos
        
        # Box
        rect = pygame.rect.Rect(*self.pos, self.width, self.height)
        pygame.draw.rect(screen, col['face'], rect)
        pygame.draw.rect(screen, col['edge'], rect, 1)
        
        # Text
        txt_img = self.font.render(self.text, True, col['font'])
        t_rect = txt_img.get_rect()
        t_w = t_rect[2]
        t_h = t_rect[3]
        x_draw = x + (self.width - t_w) / 2
        y_draw = y + (self.height - t_h) / 2
        screen.blit(txt_img, (x_draw, y_draw))   



class Slider(Element):

    def __init__(self, obj, attribute, domain, default, pos, width, 
                 theme_name='default', **kwargs):
        """
        Slider that can be used to mutate the value of some attribute for
        a given object.

        Parameters
        ----------
        obj : Any object.
            The object for which an attribute should be mutated by the slider.
        attribute : string
            The attribute name of the object to mutate (object.attribute).
        domain : Array-like
            The min and max values for the attribute.
        default : numerical
            The default/start value for the attribute.
        pos : Array-like
            The (x,y) position of the slider.
        width : Int
            The pixel width of the slider.
        theme_name : String, optional
            Name of the theme JSON file to be used. The default is 
            'default_dark'.
        **kwargs : dict
            See kwargs in init function.
        """
        assert hasattr(obj, attribute), 'Object does not contain attribute'
        super().__init__(theme_name, **kwargs)
        
        # Functional attributes
        self.obj = obj
        self.att = attribute
        self.dom = domain
        self.val = default
        self.pos = pos
        self.width = width
        
        # Kwargs: slider-specific dimension and usage properties
        self.dtype = kwargs.get('dtype', float)
        self.margin_x = kwargs.get('margin_x', 5)   # Slider/text x padding
        self.height = kwargs.get('margin_y', 12)    # Only used for self.box
        self.text = kwargs.get('text', attribute)   # Text next to slider
        
        # Set default object value
        self.obj.__setattr__(self.att, self.dtype(self.val))

    def set_theme(self):
        self.colors = {
           State.PASSIVE: {
               'face':self.theme['0'],
               'edge':self.theme['3'],
               'font':self.theme['3']},
           State.HOOVER: {
               'face':self.theme['1'],
               'edge':self.theme['4'],
               'font':self.theme['4']},
           State.TRIGGERED: {
               'face':self.theme['2'],
               'edge':self.theme['5'],
               'font':self.theme['6']},
            }

    @property
    def _box(self):
        box = (
            self.pos[0],
            self.pos[0] + self.width,
            self.pos[1],
            self.pos[1] + self.height)
        return box
    
    def set_value(self, value):
        """
        For external use. Set the slider value and the object value.
        """
        self.val = value
        self.obj.__setattr__(self.att, self.dtype(self.val))
    
    def _set_value_from_mouse(self, mouse_pos):
        """
        Calculate the fractional position of the mouse on the slider based on 
        the mouse x position relative to the sliders position and width. Then,
        mutltiple this value with the slider domain to determine the slider
        value.
        """
        fract_mouse_x = min(1, max(0,(mouse_pos[0] - self.pos[0]) / self.width))
        attribute_domain = self.dom[1] - self.dom[0]
        attribute_value = self.dtype(
            self.dom[0] + fract_mouse_x * attribute_domain)
        self.val = attribute_value
        self.obj.__setattr__(self.att, self.val)
    
    def update(self, key_events, mouse_pos):
        """
        Sets the slider and executes actions state based on mouse behaviour.
        """        
        in_box = self._inscope_mouse(mouse_pos)
        click = pygame.BUTTON_LEFT in key_events['down']
        release = pygame.BUTTON_LEFT in key_events['up']

        # Trigger slider when clicked in box and set value
        if in_box and click:
            self.state = State.TRIGGERED
            self._set_value_from_mouse(mouse_pos)

        # Set state to hoover when released in box
        elif self.state == State.TRIGGERED and release and in_box:
            self.state = State.HOOVER
            
        # Set state to passive when release out of box
        elif self.state == State.TRIGGERED and release and not in_box:
            self.state = State.PASSIVE
        
        # Set value when state is triggered
        elif self.state == State.TRIGGERED:
            self._set_value_from_mouse(mouse_pos)
    
        # Set state to hoover when passive and in box
        elif self.state == State.PASSIVE and in_box:
            self.state = State.HOOVER
            
        # Set state to passive when hoover and out of box
        elif self.state == State.HOOVER and not in_box:
            self.state = State.PASSIVE

    def draw(self, screen):
        """
        Draw the slider.
        """
        col = self.colors[self.state]
        
        # Draw line
        line_x = self.pos[0]
        line_y = int(self.pos[1] + self.height / 2)
        pygame.draw.line(
            screen, col['edge'], (line_x, line_y), 
            (line_x + self.width, line_y), 1)
        
        # Draw circle knob with border
        fractional_val = (self.val - self.dom[0]) / (self.dom[1] - self.dom[0])
        knob_x = int(line_x + fractional_val * self.width)
        radius = 3 if self.state == State.TRIGGERED else 2
        pygame.gfxdraw.aacircle(
            screen, knob_x, line_y, radius+1, col['edge'])
        pygame.gfxdraw.filled_circle(
            screen, knob_x, line_y, radius+1, col['edge'])
        
        pygame.gfxdraw.aacircle(
            screen, knob_x, line_y, radius, col['face'])
        pygame.gfxdraw.filled_circle(
            screen, knob_x, line_y, radius, col['face'])
        
    
        # Draw text
        txt_img = self.font.render(self.text, True, col['font'])
        text_height = txt_img.get_rect()[3]
        text_x = self.pos[0] + self.width + self.margin_x
        text_y = int(line_y - text_height / 2)
        screen.blit(txt_img, (text_x, text_y))     
        
        
        
class Label(Element):
    
    def __init__(self, text, pos, width, height, hcenter=True, vcenter=True,
                 theme_name='default', **kwargs):
        """
        Passive textbox.

        Parameters
        ----------
        text : String
            Text on the button.
        pos : Array-like
            (x,y) Position of the button.
        width : Int
            Pixel width of the button.
        height : Int
            Pixel height of the button.
        hcenter : Bool
            Centers the text horizontally across the box width
        vcenter : Bool
            Centers the text vertically across the box height
        theme_name : String, optional
            Name of the theme JSON file to be used. The default is 
            'default_dark'.
        """
        super().__init__(theme_name, **kwargs)
        
        # Functional attributes
        self.text = text
        self.pos = np.array(pos)
        self.width = width
        self.height = height
        self.hcenter = hcenter
        self.vcenter = vcenter
    
    def set_theme(self):
        self.colors = {
           State.PASSIVE: {
               'face':self.theme['0'],
               'edge':self.theme['background'],
               'font':self.theme['5']},
            }

    @property
    def _box(self):
        return False

    def update(self, key_events, mouse_pos):
        pass
        
    def draw(self, screen):
        """
        Draw the button.
        """
        col = self.colors[self.state]
        x, y = self.pos
        
        # Box
        rect = pygame.rect.Rect(*self.pos, self.width, self.height)
        pygame.draw.rect(screen, col['face'], rect)
        pygame.draw.rect(screen, col['edge'], rect, 1)
        
        # Text
        txt_img = self.font.render(self.text, True, col['font'])
        t_rect = txt_img.get_rect()
        t_w = t_rect[2]
        t_h = t_rect[3]
        
        if self.hcenter:
            x_draw = x + (self.width - t_w) / 2
        else:
            x_draw = x + max(2, int(self.font_size / 2))
        if self.vcenter:
            y_draw = y + (self.height - t_h) / 2
        else:
            y_draw = y + max(2, int(self.font_size / 5))
            
        screen.blit(txt_img, (x_draw, y_draw))   



class CheckBox(Element):
    
    def __init__(self, obj, attribute, default, pos, theme_name='default', 
                 **kwargs):
        """
        Checkbox that can set the value of an attribute of some object to
        either True or False.

        Parameters
        ----------
        obj : Any object.
            The object for which an attribute should be mutated by the slider.
        attribute : string
            The attribute name of the object to mutate (object.attribute).
        default : Bool
            The default/start value for the attribute.
        pos : Array-like
            The (x,y) position of the slider.
        theme_name : String, optional
            Name of the theme JSON file to be used. The default is 
            'default_dark'.
        **kwargs : dict
            See kwargs in init function.
        """
        assert hasattr(obj, attribute), 'Object does not contain attribute'
        super().__init__(theme_name, **kwargs)
        
        # Functional attributes
        self.obj = obj
        self.att = attribute
        self.val = default
        self.pos = pos
        
        # Kwargs: Checkbox-specific dimension and usage properties
        self.margin_x = kwargs.get('margin_x', 5)       # Box/text x padding
        self.click_margin = kwargs.get('click_margin', 5)   # Marging of clickable area around box
        self.text = kwargs.get('text', attribute)       # Text next to box
        self.box_size = kwargs.get('box_size', 12)      # Size of clickable box
        
        # Set default object value
        self.obj.__setattr__(self.att, self.val)

    def set_theme(self):
        self.colors = {
           State.PASSIVE: {
               'face':self.theme['background'],
               'edge':self.theme['3'],
               'font':self.theme['5']},
           State.HOOVER: {
               'face':self.theme['1'],
               'edge':self.theme['4'],
               'font':self.theme['5']},
           State.TRIGGERED: {
               'face':self.theme['2'],
               'edge':self.theme['0'],
               'font':self.theme['5']}
            }
        
    @property
    def _box(self):
        box = (
            self.pos[0] - self.click_margin,
            self.pos[0] + self.box_size + self.click_margin,
            self.pos[1] - self.click_margin,
            self.pos[1] + self.box_size + self.click_margin)
        return box
    
    def switch(self):
        """
        Switch the checkbox state. Can be called externally.
        """
        self.val = not self.val
        self.obj.__setattr__(self.att, self.val)
        
    def update(self, key_events, mouse_pos):
        """
        Sets the CheckBox state and executes actions based on mouse behaviour.
        """
        in_box = self._inscope_mouse(mouse_pos)
        click = pygame.BUTTON_LEFT in key_events['down']
        release = pygame.BUTTON_LEFT in key_events['up']
        
        
        # Trigger when in box and button is clicked
        if in_box and click:
            self.state = State.TRIGGERED
        
        # Change state when mouse is released in box from trigger
        if in_box and release and self.state == State.TRIGGERED:
            self.switch()
            self.state = State.HOOVER
            
        # Set state to passive when triggered and mouse is released not in box
        if not in_box and release:
            self.state = State.PASSIVE
        
        # Set state to hoover when mouse in box
        if in_box and self.state == State.PASSIVE:
            self.state = State.HOOVER
        
        # Set state to passive if hoover and mouse out of box
        if not in_box and self.state == State.HOOVER:
            self.state = State.PASSIVE
        
        pass
        
    def draw(self, screen):
        """
        Draw the CheckBox.
        """
        
        col = self.colors[self.state]
        x, y = self.pos
        
        # Box
        rect = pygame.rect.Rect(*self.pos, self.box_size, self.box_size)
        pygame.draw.rect(screen, col['face'], rect)
        pygame.draw.rect(screen, col['edge'], rect, 1)
        
        # Checkmark
        if self.val:
            checkdim = 1
            rect = pygame.rect.Rect(
                self.pos[0]+checkdim, self.pos[1]+checkdim, 
                self.box_size-2*checkdim, self.box_size-2*checkdim)
            pygame.draw.rect(screen, (30,30,30), rect)
        
        # Draw text
        txt_img = self.font.render(self.text, True, col['font'])
        text_height = txt_img.get_rect()[3]
        text_x = self.pos[0] + self.box_size + self.margin_x
        text_y = int((self.pos[1] + self.box_size / 2) - text_height / 2)
        screen.blit(txt_img, (text_x, text_y))     
        



    

class TextBox(Element):
    
    def __init__(self, pos, width, height, default='',
                 theme_name='default', **kwargs):
        """
        Editable textfield.

        Parameters
        ----------
        pos : Array-like
            (x,y) Position of the button.
        width : Int
            Pixel width of the button.
        height : Int
            Pixel height of the button.
        theme_name : String, optional
            Name of the theme JSON file to be used. The default is 
            'default_dark'.
        """
        super().__init__(theme_name, **kwargs)
        
        # Functional attributes
        self.pos = np.array(pos)
        self.width = width
        self.height = height
        self.val = default
    
    def set_theme(self):
        self.colors = {
           State.PASSIVE: {
               'face':self.theme['6'],
               'edge':self.theme['3'],
               'font':self.theme['0']},
           State.HOOVER: {
               'face':self.theme['5'],
               'edge':self.theme['3'],
               'font':self.theme['0']},
           State.TRIGGERED: {
               'face':self.theme['4'],
               'edge':self.theme['background'],
               'font':self.theme['0']},
           State.ACTIVE: {
               'face':self.theme['6'],
               'edge':self.theme['background'],
               'font':self.theme['0']}
            }
        
    @property
    def _box(self):
        box = (
            self.pos[0],
            self.pos[0] + self.width,
            self.pos[1],
            self.pos[1] + self.height)
        return box

    def update(self, key_events, mouse_pos):
        """
        Sets the button state and executes actions based on mouse behaviour.
        """
        in_box = self._inscope_mouse(mouse_pos)
        click = pygame.BUTTON_LEFT in key_events['down']
        release = pygame.BUTTON_LEFT in key_events['up']
                
        
        # Hoover when passive and mouse moves in box
        if self.state == State.PASSIVE and in_box:
            self.state = State.HOOVER
        
        # Passive when hoover and mouse moves out of box
        elif self.state == State.HOOVER and not in_box:
            self.state = State.PASSIVE
        
        # Trigger when in box and button is clicked
        elif click and in_box:
            self.state = State.TRIGGERED
                
        # Set to passive when triggered and mouse is released out of box
        elif self.state == State.TRIGGERED and release and not in_box:
            self.state = State.PASSIVE
        
        # Set active when triggered, in box, and mouse is released
        elif self.state == State.TRIGGERED and in_box and release:
            self.state = State.ACTIVE
        
        # Keep triggered when mouse is held and moves out of box
        elif self.state == State.TRIGGERED and not in_box:
            self.state = State.TRIGGERED
            
        # Set to passive when active but clicked out of box
        elif self.state == State.ACTIVE and click and not in_box:
            self.state = State.PASSIVE
            
            
        
    def draw(self, screen):
        """
        Draw the button.
        """
        col = self.colors[self.state]
        x, y = self.pos
        
        # Box
        rect = pygame.rect.Rect(*self.pos, self.width, self.height)
        pygame.draw.rect(screen, col['face'], rect)
        pygame.draw.rect(screen, col['edge'], rect, 1)
        
        # Text
        txt_img = self.font.render(self.val, True, col['font'])
        t_rect = txt_img.get_rect()
        t_w = t_rect[2]
        t_h = t_rect[3]
        x_draw = x + (self.width - t_w) / 2
        y_draw = y + (self.height - t_h) / 2
        screen.blit(txt_img, (x_draw, y_draw))   
    