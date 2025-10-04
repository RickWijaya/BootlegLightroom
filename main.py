"""
TO DO
Add Gen AI API CALL
Add Hue Slider
Add Highlight Slider
Add Shadow Slider
Add Tint Slider
Add Vibrance Slider

Cara run  :
1. Install dependencies:
   pip install pillow numpy opencv-python matplotlib
2. Run the script:
   python main.py
3. Make sure using python 3.7 or above
--Ricky Wijaya
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageFilter, ImageOps, ImageEnhance, ImageDraw
import numpy as np
import cv2
#import requests
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class AdvancedImageProcessor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BLALR - Advanced Image Processor")
        self.geometry("1400x800")
        self.minsize(1200, 700)
        self.maxsize(1920, 1080)
        # Set dark theme
        self.configure(bg='#2b2b2b')
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._setup_dark_theme()
        
        # Image state
        self.original_image = None
        self.current_image = None
        self.preview_image_tk = None
        
        # Transform values
        self.transform_values = {
            'resize': 100,
            'rotate': 0,
            'translate_x': 0,
            'translate_y': 0,
            'scale_x': 100,
            'scale_y': 100,
            'shear_x': 0,
            'shear_y': 0
        }
        
        # Store slider references for reset
        self.slider_widgets = {}
        
        # API Key for image generation (user will need to provide)
        self.api_key = ""
        
        self._build_ui()
        
    def _setup_dark_theme(self):
        """Setup dark theme for the application"""
        self.style.configure('TFrame', background='#2b2b2b')
        self.style.configure('TLabel', background='#2b2b2b', foreground='white')
        self.style.configure('TLabelframe', background='#2b2b2b', foreground='white')
        self.style.configure('TLabelframe.Label', background='#2b2b2b', foreground='white')
        self.style.configure('TButton', background='#404040', foreground='white')
        self.style.map('TButton', background=[('active', '#505050')])
        self.style.configure('TScale', background='#2b2b2b', troughcolor='#404040')
        self.style.configure('TEntry', fieldbackground='#404040', foreground='white')
        self.style.configure('Header.TLabel', font=('Arial', 10, 'bold'))
        
    def _build_ui(self):
        # Main container
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Top toolbar
        self._build_toolbar(main_container)
        
        # Content area
        content = ttk.Frame(main_container)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Tools
        self.left_panel = ttk.Frame(content, width=320)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.left_panel.pack_propagate(False)
        
        # Center - Image display
        self.center_frame = ttk.Frame(content)
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Right panel - Adjustments
        self.right_panel = ttk.Frame(content, width=320)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        self.right_panel.pack_propagate(False)
        
        # Setup panels
        self._build_left_panel()
        self._build_center_panel()
        self._build_right_panel()
        
    def _build_toolbar(self, parent):
        """Build top toolbar"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # File operations
        ttk.Button(toolbar, text="Open", command=self.open_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Generate AI Image", command=self.generate_ai_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Reset", command=self.reset_image).pack(side=tk.LEFT, padx=2)
        
        # Status
        self.status_label = ttk.Label(toolbar, text="No image loaded", style='Header.TLabel')
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
    def _build_left_panel(self):
        # Main left panel frame (single frame, no notebook)
        left_frame = ttk.Frame(self.left_panel)
        left_frame.pack(fill=tk.BOTH, expand=True)

        # Create scrollable frame for transform controls
        canvas = tk.Canvas(left_frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Transform controls (all content from before)
        ttk.Label(scrollable_frame, text="Basic Transforms", style='Header.TLabel').pack(pady=5)

        # Resize
        self._add_slider_with_entry(scrollable_frame, "Resize (%)", 'resize', 10, 200, 100, 
                        lambda v: self.update_transform('resize', v))

        # Rotate
        self._add_slider_with_entry(scrollable_frame, "Rotate (°)", 'rotate', -180, 180, 0, 
                        lambda v: self.update_transform('rotate', v))

        # Crop button
        ttk.Button(scrollable_frame, text="Crop (Interactive)", 
                  command=self.interactive_crop).pack(fill=tk.X, padx=5, pady=2)

        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Translation
        ttk.Label(scrollable_frame, text="Translation", style='Header.TLabel').pack(pady=5)
        self._add_slider_with_entry(scrollable_frame, "Translate X", 'translate_x', -200, 200, 0, 
                        lambda v: self.update_transform('translate_x', v))
        self._add_slider_with_entry(scrollable_frame, "Translate Y", 'translate_y', -200, 200, 0, 
                        lambda v: self.update_transform('translate_y', v))

        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Scale
        ttk.Label(scrollable_frame, text="Scale", style='Header.TLabel').pack(pady=5)
        self._add_slider_with_entry(scrollable_frame, "Scale X (%)", 'scale_x', 10, 200, 100, 
                        lambda v: self.update_transform('scale_x', v))
        self._add_slider_with_entry(scrollable_frame, "Scale Y (%)", 'scale_y', 10, 200, 100, 
                        lambda v: self.update_transform('scale_y', v))

        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Shear
        ttk.Label(scrollable_frame, text="Shear", style='Header.TLabel').pack(pady=5)
        self._add_slider_with_entry(scrollable_frame, "Shear X", 'shear_x', -45, 45, 0, 
                        lambda v: self.update_transform('shear_x', v))
        self._add_slider_with_entry(scrollable_frame, "Shear Y", 'shear_y', -45, 45, 0, 
                        lambda v: self.update_transform('shear_y', v))

        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Reflection
        ttk.Label(scrollable_frame, text="Reflection", style='Header.TLabel').pack(pady=5)
        ttk.Button(scrollable_frame, text="Flip Horizontal", 
                  command=lambda: self.reflect('horizontal')).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(scrollable_frame, text="Flip Vertical", 
                  command=lambda: self.reflect('vertical')).pack(fill=tk.X, padx=5, pady=2)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        
    def _build_center_panel(self):
        # Image display
        self.image_label = ttk.Label(self.center_frame, anchor=tk.CENTER)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
    def _build_right_panel(self):
        self._build_histogram()
        # Create notebook for tabs
        notebook = ttk.Notebook(self.right_panel)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # ========================
        # COLOR TAB
        # ========================
        color_frame = ttk.Frame(notebook)
        notebook.add(color_frame, text="Color")
        
        # Create scrollable frame
        canvas = tk.Canvas(color_frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(color_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        # ========= COLOR ADJUSTMENTS =========
        ttk.Label(scrollable_frame, text="Color Adjustments", style='Header.TLabel').pack(pady=5)
        
        self.saturation_var = self._add_slider_with_entry(scrollable_frame, "Saturation", 'saturation', 0, 2, 1, 
                                               self._adjust_preview)
        self.brightness_var = self._add_slider_with_entry(scrollable_frame, "Brightness", 'brightness', 0.2, 2, 1, 
                                               self._adjust_preview)
        self.blacks_var = self._add_slider_with_entry(scrollable_frame, "Blacks", 'blacks', -100, 100, 0, 
                                           self._adjust_preview)
        self.whites_var = self._add_slider_with_entry(scrollable_frame, "Whites", 'whites', -100, 100, 0, 
                                           self._adjust_preview)
        self.contrast_var = self._add_slider_with_entry(scrollable_frame, "Contrast", 'contrast', 0.2, 2, 1, 
                                             self._adjust_preview)
        self.exposure_var = self._add_slider_with_entry(scrollable_frame, "Exposure", 'exposure', -2, 2, 0, 
                                             self._adjust_preview)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # ========================
        # MORPHOLOGY TAB
        # ========================
        morph_frame = ttk.Frame(notebook)
        notebook.add(morph_frame, text="Morphology")
        
        ttk.Label(morph_frame, text="Morphological Operations", style='Header.TLabel').pack(pady=10)
        
        ttk.Label(morph_frame, text="Kernel Size:").pack(pady=5)
        self.kernel_size_var = tk.IntVar(value=3)
        kernel_frame = ttk.Frame(morph_frame)
        kernel_frame.pack(fill=tk.X, padx=10, pady=5)
        
        kernel_slider = ttk.Scale(kernel_frame, from_=1, to=15, orient=tk.HORIZONTAL,
                                 variable=self.kernel_size_var)
        kernel_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        kernel_entry = ttk.Entry(kernel_frame, textvariable=self.kernel_size_var, width=5)
        kernel_entry.pack(side=tk.RIGHT, padx=5)
        
        # Store for reset
        self.slider_widgets['kernel_size'] = (kernel_slider, kernel_entry, self.kernel_size_var, 3)
        
        ttk.Button(morph_frame, text="Erosion", 
                  command=lambda: self.apply_morphology('erosion')).pack(fill=tk.X, padx=10, pady=2)
        ttk.Button(morph_frame, text="Dilation", 
                  command=lambda: self.apply_morphology('dilation')).pack(fill=tk.X, padx=10, pady=2)
        ttk.Button(morph_frame, text="Opening", 
                  command=lambda: self.apply_morphology('opening')).pack(fill=tk.X, padx=10, pady=2)
        ttk.Button(morph_frame, text="Closing", 
                  command=lambda: self.apply_morphology('closing')).pack(fill=tk.X, padx=10, pady=2)
        ttk.Button(morph_frame, text="Gradient", 
                  command=lambda: self.apply_morphology('gradient')).pack(fill=tk.X, padx=10, pady=2)
        
        # ========================
        # FILTER TAB
        # ========================
        filter_frame = ttk.Frame(notebook)
        notebook.add(filter_frame, text="Filters")
        
        ttk.Label(filter_frame, text="Filter Effects", style='Header.TLabel').pack(pady=10)
        
        self.blur_var = self._add_slider_with_entry(filter_frame, "Blur", 'blur', 0, 20, 0, self._adjust_preview)
        self.noise_var = self._add_slider_with_entry(filter_frame, "Noise", 'noise', 0, 100, 0, self._adjust_preview)
        self.vignette_var = self._add_slider_with_entry(filter_frame, "Vignette", 'vignette', 0, 100, 0, self._adjust_preview)
        
        ttk.Separator(filter_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        ttk.Label(filter_frame, text="Quick Filters", style='Header.TLabel').pack(pady=5)
        ttk.Button(filter_frame, text="Grayscale", 
                  command=lambda: self.apply_filter('grayscale')).pack(fill=tk.X, padx=10, pady=2)
        ttk.Button(filter_frame, text="Sepia", 
                  command=lambda: self.apply_filter('sepia')).pack(fill=tk.X, padx=10, pady=2)
        ttk.Button(filter_frame, text="Edge Detection", 
                  command=lambda: self.apply_filter('edge')).pack(fill=tk.X, padx=10, pady=2)
        ttk.Button(filter_frame, text="Emboss", 
                  command=lambda: self.apply_filter('emboss')).pack(fill=tk.X, padx=10, pady=2)
        ttk.Button(filter_frame, text="Sharpen", 
                  command=lambda: self.apply_filter('sharpen')).pack(fill=tk.X, padx=10, pady=2)

        
    def _add_slider_with_entry(self, parent, label, key, min_val, max_val, default, command):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(frame, text=label).pack(anchor=tk.W)
        var = tk.DoubleVar(value=default)

        slider_frame = ttk.Frame(frame)
        slider_frame.pack(fill=tk.X)

        slider = ttk.Scale(slider_frame, from_=min_val, to=max_val,
                          orient=tk.HORIZONTAL, variable=var)
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        entry = ttk.Entry(slider_frame, textvariable=var, width=6)
        entry.pack(side=tk.RIGHT, padx=5)

        # Debounce setup
        delay_ms = 300
        self._debounce_after_ids = getattr(self, "_debounce_after_ids", {})

        def schedule_update():
            if command:
                if key in self._debounce_after_ids:
                    self.after_cancel(self._debounce_after_ids[key])
                self._debounce_after_ids[key] = self.after(
                    delay_ms, lambda: command(var.get())
                )

        # Event bindings for smooth UX
        slider.bind("<ButtonRelease-1>", lambda e: schedule_update())
        slider.bind("<KeyRelease>", lambda e: schedule_update())
        entry.bind("<Return>", lambda e: schedule_update())
        entry.bind("<FocusOut>", lambda e: schedule_update())

        def validate_entry(*_):
            try:
                value = float(var.get())
                if value < min_val:
                    var.set(min_val)
                elif value > max_val:
                    var.set(max_val)
            except (ValueError, tk.TclError):
                var.set(default)

        var.trace_add("write", lambda *_: validate_entry())

        # Store for reset
        self.slider_widgets[key] = (slider, entry, var, default)
        return var

    def _build_histogram(self):
        hist_frame = ttk.Frame(self.right_panel)
        hist_frame.pack(fill=tk.X, pady=5)

        fig = Figure(figsize=(6, 2), dpi=100, facecolor='#2b2b2b')
        self.hist_ax = fig.add_subplot(111)
        self.hist_ax.set_facecolor('#2b2b2b')
        self.hist_ax.tick_params(colors='white')
        self.hist_ax.set_title("Histogram", color='white')

        self.hist_canvas = FigureCanvasTkAgg(fig, master=hist_frame)
        self.hist_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _update_histogram(self, img=None):
        """Update histogram for the current image"""
        if img is None:
            img = self.current_image
        if img is None:
            return

        img_array = np.array(img.convert('RGB'))
        self.hist_ax.clear()
        colors = ('r', 'g', 'b')
        for i, color in enumerate(colors):
            hist = cv2.calcHist([img_array], [i], None, [256], [0, 256])
            self.hist_ax.plot(hist, color=color)
        self.hist_ax.set_xlim([0, 256])
        self.hist_ax.set_facecolor('#2b2b2b')
        self.hist_ax.tick_params(colors='white')
        self.hist_ax.set_title("Histogram", color='white')
        self.hist_canvas.draw_idle()


    
    def generate_ai_image(self):
        """Generate AI image using API"""
        if not self.api_key:
            self.api_key = simpledialog.askstring("API Key", 
                                                  "Enter your image generation API key:")
            if not self.api_key:
                return
        
        prompt = simpledialog.askstring("AI Image Generation", 
                                        "Enter your image prompt:")
        if not prompt:
            return
        
        messagebox.showinfo("Note", 
                           "AI image generation requires a valid API endpoint.\n" +
                           "This is a placeholder for integration with services like:\n" +
                           "- DALL-E 2/3\n- Stable Diffusion\n- Midjourney API")
        
        # Placeholder: Create a sample generated image
        # In real implementation, you would call the API here
        width, height = 512, 512
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # Create gradient as placeholder
        for i in range(height):
            color = int(255 * (i / height))
            draw.rectangle([0, i, width, i+1], fill=(color, 100, 255-color))
        
        draw.text((width//2 - 100, height//2), "AI Generated\n(Placeholder)", 
                 fill='white')
        
        self.original_image = img
        self.current_image = img.copy()
        self.reset_all_sliders()
        self.update_image_preview()
        self.status_label.config(text=f"Generated AI image: {width}x{height}")
    
    def open_image(self):
        """Open an image file"""
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tiff")]
        )
        if not path:
            return
        
        try:
            img = Image.open(path).convert('RGBA')
            self.original_image = img
            self.current_image = img.copy()
            self.reset_all_sliders()
            self.update_image_preview()
            self.status_label.config(text=f"Loaded: {os.path.basename(path)} ({img.width}x{img.height})")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image:\n{e}")
    
    def save_image(self):
        """Save the current image"""
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image to save")
            return
        
        path = filedialog.asksaveasfilename(
            defaultextension='.png',
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp")]
        )
        if not path:
            return
        
        try:
            img = self.apply_all_adjustments()
            if path.lower().endswith('.jpg'):
                img = img.convert('RGB')
            img.save(path)
            messagebox.showinfo("Success", f"Image saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image:\n{e}")
    
    def apply_all_adjustments(self):
        """Apply all current adjustments to the image"""
        if self.current_image is None:
            return None
        
        img = self.current_image.copy()
        
        # Apply color adjustments
        # Saturation
        sat = float(self.saturation_var.get())
        if sat != 1.0:
            converter = ImageEnhance.Color(img)
            img = converter.enhance(sat)
        
        # Brightness
        bright = float(self.brightness_var.get())
        if bright != 1.0:
            converter = ImageEnhance.Brightness(img)
            img = converter.enhance(bright)
        
        # Contrast
        contrast = float(self.contrast_var.get())
        if contrast != 1.0:
            converter = ImageEnhance.Contrast(img)
            img = converter.enhance(contrast)
        
        # Exposure (simulated)
        exposure = float(self.exposure_var.get())
        if exposure != 0:
            factor = np.power(2, exposure)
            converter = ImageEnhance.Brightness(img)
            img = converter.enhance(factor)
        
        # Blacks and Whites adjustment
        blacks = float(self.blacks_var.get())
        whites = float(self.whites_var.get())
        if blacks != 0 or whites != 0:
            img = self.adjust_levels(img, blacks, whites)
        
        # Apply filters
        # Blur
        blur = float(self.blur_var.get())
        if blur > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=blur))
        
        # Noise
        noise = float(self.noise_var.get())
        if noise > 0:
            img = self.add_noise(img, noise)
        
        # Vignette
        vignette = float(self.vignette_var.get())
        if vignette > 0:
            img = self.add_vignette(img, vignette / 100)
        
        return img
    
    def adjust_levels(self, img, blacks, whites):
        """Adjust black and white levels"""
        img_array = np.array(img)
        
        # Adjust blacks (shadows)
        if blacks != 0:
            adjustment = blacks / 100 * 50
            img_array = np.where(img_array < 128, 
                                np.clip(img_array + adjustment, 0, 255), 
                                img_array)
        
        # Adjust whites (highlights)
        if whites != 0:
            adjustment = whites / 100 * 50
            img_array = np.where(img_array > 128, 
                                np.clip(img_array + adjustment, 0, 255), 
                                img_array)
        
        return Image.fromarray(img_array.astype('uint8'), mode=img.mode)
    
    def add_noise(self, img, amount):
        """Add noise to image"""
        arr = np.array(img)
        noise = np.random.normal(0, amount, arr.shape).astype(np.int16)
        noisy = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy, mode=img.mode)
    
    def add_vignette(self, img, strength):
        """Add vignette effect"""
        width, height = img.size
        
        # Create radial gradient
        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)
        X, Y = np.meshgrid(x, y)
        radius = np.sqrt(X**2 + Y**2)
        
        # Create vignette mask
        vignette = 1 - (radius * strength)
        vignette = np.clip(vignette, 0, 1)
        
        # Apply vignette
        img_array = np.array(img).astype(float)
        for i in range(min(3, img_array.shape[2])):  # RGB channels only
            img_array[:,:,i] *= vignette
        
        return Image.fromarray(img_array.astype('uint8'), mode=img.mode)
    
    def apply_morphology(self, operation):
        """Apply morphological operations"""
        if self.current_image is None:
            return
        
        # Convert to numpy array
        img_array = np.array(self.current_image.convert('RGB'))
        kernel_size = int(self.kernel_size_var.get())
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        
        # Apply operation to each channel
        result = np.zeros_like(img_array)
        for i in range(3):
            channel = img_array[:,:,i]
            
            if operation == 'erosion':
                result[:,:,i] = cv2.erode(channel, kernel, iterations=1)
            elif operation == 'dilation':
                result[:,:,i] = cv2.dilate(channel, kernel, iterations=1)
            elif operation == 'opening':
                result[:,:,i] = cv2.morphologyEx(channel, cv2.MORPH_OPEN, kernel)
            elif operation == 'closing':
                result[:,:,i] = cv2.morphologyEx(channel, cv2.MORPH_CLOSE, kernel)
            elif operation == 'gradient':
                result[:,:,i] = cv2.morphologyEx(channel, cv2.MORPH_GRADIENT, kernel)
        
        self.current_image = Image.fromarray(result, mode='RGB').convert('RGBA')
        self.update_image_preview()
    
    def apply_filter(self, filter_name):
        """Apply various filters"""
        if self.current_image is None:
            return
        
        img = self.current_image
        
        if filter_name == 'grayscale':
            img = ImageOps.grayscale(img).convert('RGBA')
        elif filter_name == 'sepia':
            img = self.apply_sepia(img)
        elif filter_name == 'edge':
            img = img.filter(ImageFilter.FIND_EDGES)
        elif filter_name == 'emboss':
            img = img.filter(ImageFilter.EMBOSS)
        elif filter_name == 'sharpen':
            img = img.filter(ImageFilter.SHARPEN)
        
        self.current_image = img
        self.update_image_preview()
    
    def apply_sepia(self, img):
        """Apply sepia tone effect"""
        img_array = np.array(img.convert('RGB'))
        
        # Sepia transformation matrix
        sepia_filter = np.array([[0.393, 0.769, 0.189],
                                 [0.349, 0.686, 0.168],
                                 [0.272, 0.534, 0.131]])
        
        sepia_img = img_array.dot(sepia_filter.T)
        sepia_img = np.clip(sepia_img, 0, 255).astype(np.uint8)
        
        return Image.fromarray(sepia_img, mode='RGB').convert('RGBA')
    
    def update_transform(self, transform_type, value):
        """Update transform values and preview"""
        self.transform_values[transform_type] = float(value)
        self.apply_transforms()
    
    def apply_transforms(self):
        """Apply all geometric transforms"""
        if self.original_image is None:
            return
        
        img = self.original_image.copy()
        width, height = img.size
        
        # Apply resize
        resize_factor = self.transform_values['resize'] / 100.0
        if resize_factor != 1.0:
            new_width = int(width * resize_factor)
            new_height = int(height * resize_factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Apply rotation
        rotate_angle = self.transform_values['rotate']
        if rotate_angle != 0:
            img = img.rotate(rotate_angle, expand=True, resample=Image.Resampling.BICUBIC)
        
        # Apply translation
        translate_x = self.transform_values['translate_x']
        translate_y = self.transform_values['translate_y']
        if translate_x != 0 or translate_y != 0:
            img = ImageOps.exif_transpose(img)
            img = img.transform(
                img.size, 
                Image.AFFINE, 
                (1, 0, translate_x, 0, 1, translate_y),
                resample=Image.Resampling.BICUBIC
            )
        
        # Apply scale
        scale_x = self.transform_values['scale_x'] / 100.0
        scale_y = self.transform_values['scale_y'] / 100.0
        if scale_x != 1.0 or scale_y != 1.0:
            new_width = int(img.width * scale_x)
            new_height = int(img.height * scale_y)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Apply shear
        shear_x = np.radians(self.transform_values['shear_x'])
        shear_y = np.radians(self.transform_values['shear_y'])
        if shear_x != 0 or shear_y != 0:
            a = 1
            b = np.tan(shear_x)
            c = 0
            d = np.tan(shear_y)
            e = 1
            f = 0
            
            img = img.transform(
                img.size,
                Image.AFFINE,
                (a, b, c, d, e, f),
                resample=Image.Resampling.BICUBIC
            )
        
        self.current_image = img
        self.update_image_preview()
    
    def interactive_crop(self):
        """Start interactive cropping mode"""
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded")
            return
        
        # Create cropping window
        crop_window = tk.Toplevel(self)
        crop_window.title("Interactive Crop")
        crop_window.geometry("800x600")
        crop_window.configure(bg='#2b2b2b')
        
        # Display image for cropping
        crop_canvas = tk.Canvas(crop_window, bg='#404040', cursor="crosshair")
        crop_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Display current image
        display_img = self.current_image.copy()
        display_img.thumbnail((700, 500), Image.Resampling.LANCZOS)
        self.crop_preview_img = ImageTk.PhotoImage(display_img)
        crop_canvas.create_image(400, 300, image=self.crop_preview_img, anchor=tk.CENTER)
        
        # Crop selection variables
        self.crop_start_x = None
        self.crop_start_y = None
        self.crop_rect = None
        
        def start_crop(event):
            self.crop_start_x = event.x
            self.crop_start_y = event.y
            self.crop_rect = crop_canvas.create_rectangle(
                event.x, event.y, event.x, event.y,
                outline='red', width=2, dash=(4, 4)
            )
        
        def update_crop(event):
            if self.crop_rect:
                crop_canvas.coords(
                    self.crop_rect,
                    self.crop_start_x, self.crop_start_y,
                    event.x, event.y
                )
        
        def apply_crop(event):
            if not self.crop_rect:
                return
            
            # Get crop coordinates
            x1, y1, x2, y2 = crop_canvas.coords(self.crop_rect)
            
            # Convert to image coordinates
            img_width, img_height = self.current_image.size
            canvas_width = crop_canvas.winfo_width()
            canvas_height = crop_canvas.winfo_height()
            
            scale_x = img_width / canvas_width
            scale_y = img_height / canvas_height
            
            # Calculate actual crop coordinates
            crop_x1 = int(min(x1, x2) * scale_x)
            crop_y1 = int(min(y1, y2) * scale_y)
            crop_x2 = int(max(x1, x2) * scale_x)
            crop_y2 = int(max(y1, y2) * scale_y)
            
            # Ensure valid crop area
            if crop_x2 - crop_x1 > 10 and crop_y2 - crop_y1 > 10:
                self.current_image = self.current_image.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                self.update_image_preview()
                crop_window.destroy()
            else:
                messagebox.showwarning("Warning", "Please select a larger crop area")
        
        # Bind mouse events
        crop_canvas.bind("<ButtonPress-1>", start_crop)
        crop_canvas.bind("<B1-Motion>", update_crop)
        crop_canvas.bind("<ButtonRelease-1>", apply_crop)
        
        # Instructions
        instructions = ttk.Label(crop_window, text="Click and drag to select crop area, release to apply", 
                                background='#2b2b2b', foreground='white')
        instructions.pack(pady=5)
    
    def reflect(self, direction):
        """Apply reflection (flip)"""
        if self.current_image is None:
            return
        
        if direction == 'horizontal':
            self.current_image = ImageOps.mirror(self.current_image)
        elif direction == 'vertical':
            self.current_image = ImageOps.flip(self.current_image)
        
        self.update_image_preview()
    
    def _adjust_preview(self, value=None):
        if self.current_image is None:
            return
        img = self.apply_all_adjustments()
        self.update_image_preview(img)
        self._update_histogram(img)
    
    def update_image_preview(self, img=None):
        self._update_histogram(img)
        if img is None:
            img = self.current_image

        if img is None:
            return

        # Set maximum display dimensions to prevent GUI breaking
        max_display_width = 800
        max_display_height = 600

        # Calculate display size
        display_width = img.width
        display_height = img.height

        # Apply maximum size limits
        if display_width > max_display_width or display_height > max_display_height:
            # Calculate scaling factor to fit within max dimensions
            scale_x = max_display_width / display_width
            scale_y = max_display_height / display_height
            scale_factor = min(scale_x, scale_y)

            display_width = int(display_width * scale_factor)
            display_height = int(display_height * scale_factor)

        # Ensure minimum display size
        display_width = max(display_width, 100)
        display_height = max(display_height, 100)

        # Resize for display
        display_img = img.copy()
        display_img.thumbnail((display_width, display_height), Image.Resampling.LANCZOS)

        # Convert to PhotoImage
        self.preview_image_tk = ImageTk.PhotoImage(display_img)
        self.image_label.configure(image=self.preview_image_tk)
    
    def reset_image(self):
        """Reset image to original state"""
        if self.original_image is not None:
            self.current_image = self.original_image.copy()
            self.reset_all_sliders()
            self.update_image_preview()
    
    def reset_all_sliders(self):
        # Reset transform values
        self.transform_values = {
            'resize': 100,
            'rotate': 0,
            'translate_x': 0,
            'translate_y': 0,
            'scale_x': 100,
            'scale_y': 100,
            'shear_x': 0,
            'shear_y': 0
        }
        
        # Reset all slider widgets
        for key, (slider, entry, var, default) in self.slider_widgets.items():
            var.set(default)
    
    def run(self):
        self.mainloop()

if __name__ == "__main__":
    app = AdvancedImageProcessor()
    app.run()