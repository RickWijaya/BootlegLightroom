import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageFilter, ImageOps, ImageEnhance, ImageDraw
import numpy as np
import cv2
import requests
from io import BytesIO
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import colorsys
from collections import deque

class AdvancedImageProcessor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BALR - Advanced Image Processor")
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
        
        # Undo/Redo functionality
        self.undo_stack = deque(maxlen=5)  # Maximum 5 undo steps
        self.redo_stack = deque(maxlen=5)  # Maximum 5 redo steps
        
        # Transform values
        self.transform_values = {
            'resize': 100,
            'rotate': 0,
            'scale_x': 100,
            'scale_y': 100,
        }
        
        # Store slider references for reset
        self.slider_widgets = {}
        
        # API Key for image generation (user will need to provide)
        self.api_key = ""
        # Prompt for AI image generation
        self.prompt = ""

        # Color adjustment variables
        self.exposure_var = tk.DoubleVar(value=0)
        self.highlights_var = tk.DoubleVar(value=0)
        self.shadows_var = tk.DoubleVar(value=0)
        self.contrast_var = tk.DoubleVar(value=0)
        self.brightness_var = tk.DoubleVar(value=0)
        self.blacks_var = tk.DoubleVar(value=0)
        self.whites_var = tk.DoubleVar(value=0)
        self.hue_var = tk.DoubleVar(value=0)
        self.tint_var = tk.DoubleVar(value=0)
        self.saturation_var = tk.DoubleVar(value=0)
        self.temperature_var = tk.DoubleVar(value=0)
        self.vibrance_var = tk.DoubleVar(value=0)
        self.blur_var = tk.DoubleVar(value=0)
        self.noise_var = tk.DoubleVar(value=0)
        self.vignette_var = tk.DoubleVar(value=0)
        
        self._build_ui()
        
    def _setup_dark_theme(self):
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
        toolbar = ttk.Frame(parent, relief="raised", borderwidth=2)
        toolbar.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(toolbar, text="Open", command=self.open_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Generate AI Image", command=self.generate_ai_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Reset", command=self.reset_image).pack(side=tk.LEFT, padx=2)

        ttk.Button(toolbar, text="Undo", command=self.undo).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Redo", command=self.redo).pack(side=tk.LEFT, padx=2)

        self.status_label = ttk.Label(toolbar, text="No image loaded", style='Header.TLabel')
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
    def _build_left_panel(self):
        # Create a notebook inside the left panel
        notebook = ttk.Notebook(self.left_panel)
        notebook.pack(fill=tk.BOTH, expand=True)
    
        # ========================
        # TRANSFORM TAB
        # ========================
        transform_frame = ttk.Frame(notebook)
        notebook.add(transform_frame, text="Transform")
    
        # Scrollable container for transform controls
        transform_container = ttk.Frame(transform_frame)
        transform_container.pack(fill=tk.BOTH, expand=True)
    
        canvas_t = tk.Canvas(transform_container, bg='#2b2b2b', highlightthickness=0)
        scrollbar_t = ttk.Scrollbar(transform_container, orient="vertical", command=canvas_t.yview)
        scrollable_transform = ttk.Frame(canvas_t)
    
        scrollable_transform.bind(
            "<Configure>",
            lambda e: canvas_t.configure(scrollregion=canvas_t.bbox("all"))
        )
        canvas_t.create_window((0, 0), window=scrollable_transform, anchor="nw")
        canvas_t.configure(yscrollcommand=scrollbar_t.set)
    
        canvas_t.pack(side="left", fill="both", expand=True)
        scrollbar_t.pack(side="right", fill="y")
    
        # ========== Transform Controls ==========
        self._add_slider_with_entry(scrollable_transform, "Resize (%)", 'resize', 10, 200, 100,
                        lambda v: self.update_transform('resize', v))
        self._add_slider_with_entry(scrollable_transform, "Rotate (°)", 'rotate', -180, 180, 0,
                        lambda v: self.update_transform('rotate', v))
    
        ttk.Button(scrollable_transform, text="Crop (Interactive)",
                    command=self.interactive_crop).pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(scrollable_transform, text="Draw / Annotate (Interactive)",
                   command=self.interactive_draw).pack(fill=tk.X, padx=5, pady=2)

        self._add_slider_with_entry(scrollable_transform, "Scale X (%)", 'scale_x', 10, 200, 100,
                        lambda v: self.update_transform('scale_x', v))
        self._add_slider_with_entry(scrollable_transform, "Scale Y (%)", 'scale_y', 10, 200, 100,
                        lambda v: self.update_transform('scale_y', v))
    
        ttk.Button(scrollable_transform, text="Flip Horizontal",
                    command=lambda: self.reflect('horizontal')).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(scrollable_transform, text="Flip Vertical",
                    command=lambda: self.reflect('vertical')).pack(fill=tk.X, padx=5, pady=2)
    
        # ========================
        # PERSPECTIVE TAB
        # ========================
        perspective_frame = ttk.Frame(notebook)
        notebook.add(perspective_frame, text="Perspective")
    
        # Scrollable container for perspective controls
        perspective_container = ttk.Frame(perspective_frame)
        perspective_container.pack(fill=tk.BOTH, expand=True)
    
        canvas_p = tk.Canvas(perspective_container, bg='#2b2b2b', highlightthickness=0)
        scrollbar_p = ttk.Scrollbar(perspective_container, orient="vertical", command=canvas_p.yview)
        scrollable_perspective = ttk.Frame(canvas_p)
    
        scrollable_perspective.bind(
            "<Configure>",
            lambda e: canvas_p.configure(scrollregion=canvas_p.bbox("all"))
        )
        canvas_p.create_window((0, 0), window=scrollable_perspective, anchor="nw")
        canvas_p.configure(yscrollcommand=scrollbar_p.set)
    
        canvas_p.pack(side="left", fill="both", expand=True)
        scrollbar_p.pack(side="right", fill="y")
    
        # ========== Perspective Controls ==========
        ttk.Label(scrollable_perspective, text="Perspective Transform", style='Header.TLabel').pack(pady=5)
    
        corners = [
            "Top Left X", "Top Left Y", "Top Right X", "Top Right Y",
            "Bottom Left X", "Bottom Left Y", "Bottom Right X", "Bottom Right Y"
        ]
    
        self.perspective_values = {c: 0 for c in corners}
    
        for key in corners:
            self._add_slider_with_entry(
                scrollable_perspective, key, key,
                -1000, 1000, 0,
                lambda v, k=key: self.update_perspective(k, v)
            )


        
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
        # BASIC ADJUSTMENT TAB
        # ========================
        color_frame = ttk.Frame(notebook)
        notebook.add(color_frame, text="Basic")

        # Create a frame that will contain both the canvas and scrollbar
        color_container = ttk.Frame(color_frame)
        color_container.pack(fill=tk.BOTH, expand=True)

        # Create canvas and scrollbar
        canvas = tk.Canvas(color_container, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(color_container, orient="vertical", command=canvas.yview)

        # Create the scrollable frame
        scrollable_frame = ttk.Frame(canvas)

        # Configure the canvas scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # ========= COLOR ADJUSTMENTS =========
        self._add_slider_with_entry(scrollable_frame, "Exposure", 'exposure', -100, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(scrollable_frame, "Highlights", 'highlights', -100, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(scrollable_frame, "Shadows", 'shadows', -100, 100, 0, self._adjust_preview)

        self._add_slider_with_entry(scrollable_frame, "Contrast", 'contrast', -100, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(scrollable_frame, "Brightness", 'brightness', -100, 100, 0, self._adjust_preview)

        self._add_slider_with_entry(scrollable_frame, "Blacks", 'blacks', -100, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(scrollable_frame, "Whites", 'whites', -100, 100, 0, self._adjust_preview)

        # Pack canvas and scrollbar in the container
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Make sure the canvas can expand
        color_container.pack_propagate(False)
        
        # ========================
        # COLOR ADJUSTMENT TAB
        # ========================
        color_frame = ttk.Frame(notebook)
        notebook.add(color_frame, text="Color")

        # Create a frame that will contain both the canvas and scrollbar
        color_container = ttk.Frame(color_frame)
        color_container.pack(fill=tk.BOTH, expand=True)

        # Create canvas and scrollbar
        canvas = tk.Canvas(color_container, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(color_container, orient="vertical", command=canvas.yview)

        # Create the scrollable frame
        scrollable_frame = ttk.Frame(canvas)

        # Configure the canvas scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        
        self._add_slider_with_entry(scrollable_frame, "Hue", 'hue', -180, 180, 0, self._adjust_preview)
        self._add_slider_with_entry(scrollable_frame, "Tint (G/M)", 'tint', -100, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(scrollable_frame, "Saturation", 'saturation', -100, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(scrollable_frame, "Temperature", 'temperature', -100, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(scrollable_frame, "Vibrance", 'vibrance', -100, 100, 0, self._adjust_preview)

        # Pack canvas and scrollbar in the container
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Make sure the canvas can expand
        color_container.pack_propagate(False)
        # ========================
        # MORPHOLOGY TAB
        # ========================
        morph_frame = ttk.Frame(notebook)
        notebook.add(morph_frame, text="Morphology")
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
        self._add_slider_with_entry(filter_frame, "Blur", 'blur', 0, 20, 0, self._adjust_preview)
        self._add_slider_with_entry(filter_frame, "Noise", 'noise', 0, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(filter_frame, "Vignette", 'vignette', 0, 100, 0, self._adjust_preview)
        
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

        # ========================
        # FREQUENCY TAB
        # ========================
        filter_frame = ttk.Frame(notebook)
        notebook.add(filter_frame, text="Frequency")
        
        # ========================
        # Enchanment TAB
        # ========================
        filter_frame = ttk.Frame(notebook)
        notebook.add(filter_frame, text="Enchanment")
        
    def _add_slider_with_entry(self, parent, label, key, min_val, max_val, default, command):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(frame, text=label).pack(anchor=tk.W)
        
        # Get the correct variable based on key
        if key == 'exposure':
            var = self.exposure_var
        elif key == 'highlights':
            var = self.highlights_var
        elif key == 'shadows':
            var = self.shadows_var
        elif key == 'contrast':
            var = self.contrast_var
        elif key == 'brightness':
            var = self.brightness_var
        elif key == 'blacks':
            var = self.blacks_var
        elif key == 'whites':
            var = self.whites_var
        elif key == 'hue':
            var = self.hue_var
        elif key == 'tint':
            var = self.tint_var
        elif key == 'saturation':
            var = self.saturation_var
        elif key == 'temperature':
            var = self.temperature_var
        elif key == 'vibrance':
            var = self.vibrance_var
        elif key == 'blur':
            var = self.blur_var
        elif key == 'noise':
            var = self.noise_var
        elif key == 'vignette':
            var = self.vignette_var
        else:
            # For transform sliders
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

        self.hist_canvas = FigureCanvasTkAgg(fig, master=hist_frame)
        self.hist_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _update_histogram(self, img=None):
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

    # ============================
    # UNDO/REDO FUNCTIONALITY
    # ============================
    
    def save_state(self):
        """Save current image state to undo stack"""
        if self.current_image is not None:
            # Convert to bytes for efficient storage
            img_bytes = BytesIO()
            self.current_image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Save to undo stack
            self.undo_stack.append(img_bytes)
            
            # Clear redo stack when new action is performed
            self.redo_stack.clear()
            
            # Update status
            self._update_undo_redo_status()
    
    def undo(self):
        """Undo the last operation"""
        if len(self.undo_stack) > 1:  # Keep at least one state (original)
            # Save current state to redo stack
            if self.current_image is not None:
                img_bytes = BytesIO()
                self.current_image.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                self.redo_stack.append(img_bytes)
            
            # Restore previous state
            previous_state = self.undo_stack.pop()
            self.current_image = Image.open(previous_state).convert('RGBA')
            self.update_image_preview()
            
            # Update status
            self._update_undo_redo_status()
        else:
            messagebox.showinfo("Info", "Nothing to undo")
    
    def redo(self):
        """Redo the last undone operation"""
        if self.redo_stack:
            # Save current state to undo stack
            if self.current_image is not None:
                img_bytes = BytesIO()
                self.current_image.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                self.undo_stack.append(img_bytes)
            
            # Restore next state
            next_state = self.redo_stack.pop()
            self.current_image = Image.open(next_state).convert('RGBA')
            self.update_image_preview()
            
            # Update status
            self._update_undo_redo_status()
        else:
            messagebox.showinfo("Info", "Nothing to redo")
    
    def _update_undo_redo_status(self):
        """Update status label with undo/redo information"""
        undo_count = len(self.undo_stack) - 1  # Don't count current state
        redo_count = len(self.redo_stack)
        
        status_parts = []
        if hasattr(self, 'status_label') and self.status_label['text'] != "No image loaded":
            base_status = self.status_label['text'].split(' | ')[0]
            status_parts.append(base_status)
        
        if undo_count > 0:
            status_parts.append(f"Undo: {undo_count}/5")
        if redo_count > 0:
            status_parts.append(f"Redo: {redo_count}/5")
        
        if status_parts:
            self.status_label.config(text=" | ".join(status_parts))
    
    def generate_ai_image(self):
        prompt = simpledialog.askstring("AI Image Generation with Pollinations", 
                                        "Enter your image prompt:")
        if not prompt:
            return

        try:
            # Update status
            if hasattr(self, 'status_label'):
                self.status_label.config(text="Generating AI image... please wait.")
                self.status_label.update_idletasks()
    
            base_url = "https://image.pollinations.ai/prompt/"
            prompt_encoded = requests.utils.quote(prompt)
            url = f"{base_url}{prompt_encoded}?width=512&height=512&model=flux"

            response = requests.get(url, timeout=60)
            response.raise_for_status()

            img_data = BytesIO(response.content)
            img = Image.open(img_data).convert("RGB")

            # Update the app image states
            self.original_image = img
            self.current_image = img.copy()
            
            # Save initial state for undo
            self.save_state()

            if hasattr(self, 'reset_all_sliders'):
                self.reset_all_sliders()
            if hasattr(self, 'update_image_preview'):
                self.update_image_preview()

            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"AI generated image from: '{prompt}'")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate image:\n{e}")
            if hasattr(self, 'status_label'):
                self.status_label.config(text="AI image generation failed.")
    
    def open_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tiff")]
        )
        if not path:
            return
        
        try:
            img = Image.open(path).convert('RGBA')
            self.original_image = img
            self.current_image = img.copy()
            
            # Clear undo/redo stacks and save initial state
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.save_state()
            
            self.reset_all_sliders()
            self.update_image_preview()
            self.status_label.config(text=f"Loaded: {os.path.basename(path)} ({img.width}x{img.height})")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image:\n{e}")
    
    def save_image(self):
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
        if self.current_image is None:
            return None
            
        # Start with the current image (which has geometric transforms applied)
        img = self.current_image.copy()
        
        # 1. Exposure
        exposure = float(self.exposure_var.get())
        if exposure != 0:
            factor = np.power(2, exposure / 100)  # normalize exposure
            img = ImageEnhance.Brightness(img).enhance(factor)

        # 2. Highlights & Shadows
        highlights = float(self.highlights_var.get())
        shadows = float(self.shadows_var.get())
        if highlights != 0 or shadows != 0:
            img = self.adjust_highlights_shadows(img, highlights, shadows)

        # 3. Contrast & Brightness
        contrast = float(self.contrast_var.get())
        brightness = float(self.brightness_var.get())
        if contrast != 0:
            img = ImageEnhance.Contrast(img).enhance(1 + (contrast / 100))
        if brightness != 0:
            img = ImageEnhance.Brightness(img).enhance(1 + (brightness / 100))

        # 4. Blacks & Whites
        blacks = float(self.blacks_var.get())
        whites = float(self.whites_var.get())
        if blacks != 0 or whites != 0:
            img = self.adjust_levels(img, blacks, whites)

        # 5. Color adjustments
        hue_shift = float(self.hue_var.get())
        tint = float(self.tint_var.get())
        vibrance = float(self.vibrance_var.get())
        saturation = float(self.saturation_var.get())
        temperature = float(self.temperature_var.get())

        if hue_shift != 0:
            img = self.adjust_hue(img, hue_shift)
        if tint != 0:
            img = self.adjust_tint(img, tint)
        if vibrance != 0:
            img = self.adjust_vibrance(img, vibrance)
        if saturation != 0:
            img = ImageEnhance.Color(img).enhance(1 + (saturation / 100))
        if temperature != 0:
            img = self.adjust_temperature(img, temperature)

        # 6. Filters
        blur = float(self.blur_var.get())
        noise = float(self.noise_var.get())
        vignette = float(self.vignette_var.get())

        if blur > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=blur))
        if noise > 0:
            img = self.add_noise(img, noise)
        if vignette > 0:
            img = self.add_vignette(img, vignette / 100)

        return img

    def update_perspective(self, key, value):
        self.perspective_values[key] = float(value)
        # Live preview
        self.apply_perspective(preview=True)

    def apply_perspective(self, preview=False):
        if self.original_image is None:
            return

        img = np.array(self.original_image.convert("RGB"))
        h, w = img.shape[:2]

        # Define original corners (rectangle)
        src_pts = np.float32([[0, 0], [w, 0], [0, h], [w, h]])

        # Get user offsets
        tl_x = self.perspective_values["Top Left X"]
        tl_y = self.perspective_values["Top Left Y"]
        tr_x = self.perspective_values["Top Right X"]
        tr_y = self.perspective_values["Top Right Y"]
        bl_x = self.perspective_values["Bottom Left X"]
        bl_y = self.perspective_values["Bottom Left Y"]
        br_x = self.perspective_values["Bottom Right X"]
        br_y = self.perspective_values["Bottom Right Y"]

        # Destination points
        dst_pts = np.float32([
            [0 + tl_x, 0 + tl_y],
            [w + tr_x, 0 + tr_y],
            [0 + bl_x, h + bl_y],
            [w + br_x, h + br_y]
        ])

        # Compute transform matrix and warp
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped = cv2.warpPerspective(img, M, (w, h))

        result = Image.fromarray(warped).convert("RGBA")
        self.current_image = result
        self.update_image_preview(result)

        # Save to undo stack only when user presses the button
        if not preview:
            self.save_state()


    def adjust_temperature(self, img, temperature):
        img_array = np.array(img.convert('RGB'), dtype=np.float32)
        
        # Temperature adjustment: positive = warmer (more red/yellow), negative = cooler (more blue)
        if temperature > 0:
            # Warmer: increase red, slight increase in green
            img_array[:,:,0] = np.clip(img_array[:,:,0] + temperature * 2.55, 0, 255)
            img_array[:,:,1] = np.clip(img_array[:,:,1] + temperature * 1.27, 0, 255)
        else:
            # Cooler: increase blue
            img_array[:,:,2] = np.clip(img_array[:,:,2] - temperature * 2.55, 0, 255)
        
        return Image.fromarray(img_array.astype('uint8'), mode='RGB').convert('RGBA')
    
    def adjust_hue(self, img, shift_degrees):
        # Convert to HSV (or HSL, but PIL uses HSL for color ops)
        img_hsv = img.convert('HSV')
        img_array = np.array(img_hsv, dtype=np.uint8)
        
        # PIL's 'H' is 0-255, where 255 = 360 degrees.
        # Shift degrees is -180 to 180, so we scale it.
        shift_pil_units = int(shift_degrees * (255 / 360)) % 256
        
        # Get the H channel (index 0)
        hue_channel = img_array[:,:,0]
        
        # Apply the circular shift
        new_hue = (hue_channel.astype(np.int16) + shift_pil_units) % 256
        
        # Update array
        img_array[:,:,0] = new_hue.astype(np.uint8)
        
        # Convert back to RGBA
        return Image.fromarray(img_array, mode='HSV').convert('RGBA')
        
    def adjust_tint(self, img, tint_value):
        img_rgb = img.convert('RGB')
        img_array = np.array(img_rgb, dtype=np.int16) # Use int16 to handle potential overflow/underflow
        
        # Normalize adjustment factor to a small fraction, e.g., max 50 units (out of 255)
        # 100 slider value = 50 unit change.
        adj_factor = tint_value / 100.0 * 50
        
        # Positive tint = Magenta. Boost R and B, reduce G.
        # Negative tint = Green. Boost G, reduce R and B.
        
        # R and B channels (index 0 and 2) get the positive factor
        img_array[:,:,0] = np.clip(img_array[:,:,0] + adj_factor, 0, 255)
        img_array[:,:,2] = np.clip(img_array[:,:,2] + adj_factor, 0, 255)
        
        # G channel (index 1) gets the opposite factor
        img_array[:,:,1] = np.clip(img_array[:,:,1] - adj_factor, 0, 255)
        
        return Image.fromarray(img_array.astype('uint8'), mode='RGB').convert('RGBA')
    
    def adjust_vibrance(self, img, vibrance_value):
        if vibrance_value == 0:
            return img

        img_rgb = img.convert('RGB')
        factor = vibrance_value / 100.0 * 0.5 
        
        img_list = img_rgb.getdata()
        
        def adjust_vibrance_pixel(r, g, b, factor):
            # Convert to HSV (normalized 0-1)
            h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
            
            # Vibrance adjustment logic:
            # 1 - s gives a higher weight to low-saturation pixels.
            # 1.5 power provides a stronger curve.
            adjustment = factor * (1 - s)**1.5
            new_s = np.clip(s + adjustment, 0, 1)
            
            # Convert back to RGB
            r_out, g_out, b_out = colorsys.hsv_to_rgb(h, new_s, v)
            return (int(r_out * 255), int(g_out * 255), int(b_out * 255))
        
        # Apply the function to all pixels
        new_img_list = [adjust_vibrance_pixel(r, g, b, factor) for r, g, b in img_list]

        # Create new image from the list
        new_img = Image.new('RGB', img_rgb.size)
        new_img.putdata(new_img_list)
        return new_img.convert('RGBA')

    
    def adjust_highlights_shadows(self, img, highlights, shadows):
        img_array = np.array(img.convert('RGB')) / 255.0  # Normalize to 0-1
        
        # Calculate Luminance (L)
        luminance = 0.2126 * img_array[:,:,0] + 0.7152 * img_array[:,:,1] + 0.0722 * img_array[:,:,2]
        
        # Shadows adjustment
        if shadows != 0:
            # Map shadows (low luminance values) to a multiplier. 
            # sigmoid function helps create a smooth roll-off.
            # The closer to 0, the higher the mask value (up to 1).
            shadow_mask = 1 / (1 + np.exp( (luminance - 0.25) / 0.1 ))
            shadow_adj = (shadows / 100.0) * shadow_mask * 0.5 
            
            # Apply to image
            for i in range(3):
                img_array[:,:,i] = np.clip(img_array[:,:,i] + shadow_adj, 0, 1)
                
        # Highlights adjustment
        if highlights != 0:
            # Map highlights (high luminance values) to a multiplier
            # The closer to 1, the higher the mask value (up to 1).
            highlight_mask = 1 / (1 + np.exp( (0.75 - luminance) / 0.1 ))
            highlight_adj = (highlights / 100.0) * highlight_mask * 0.5
            
            # Apply to image
            for i in range(3):
                img_array[:,:,i] = np.clip(img_array[:,:,i] + highlight_adj, 0, 1)

        # Convert back to PIL image
        return Image.fromarray((img_array * 255).astype(np.uint8), mode='RGB').convert('RGBA')

    
    def adjust_levels(self, img, blacks, whites):
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
        arr = np.array(img)
        noise = np.random.normal(0, amount, arr.shape).astype(np.int16)
        noisy = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy, mode=img.mode)
    
    def add_vignette(self, img, strength):
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
        if self.current_image is None:
            return
        
        # Convert to numpy array
        img_array = np.array(self.current_image.convert('RGB'))
        kernel_size = int(self.kernel_size_var.get())
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        # Ask user for confirmation
        confirm = messagebox.askyesno(
            "Apply Filter",
            f"Are you sure you want to apply the '{operation}' filter?"
        )
        if not confirm:
            return
        
        # Save state before applying filter
        self.save_state()
        
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
        
        if self.current_image is None:
            return
        
        img = self.current_image

        # Ask user for confirmation
        confirm = messagebox.askyesno(
            "Apply Filter",
            f"Are you sure you want to apply the '{filter_name}' filter?"
        )
        if not confirm:
            return
            
        # Save state before applying filter
        self.save_state()
        
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
        img_array = np.array(img.convert('RGB'))
        
        # Sepia transformation matrix
        sepia_filter = np.array([[0.393, 0.769, 0.189],
                                 [0.349, 0.686, 0.168],
                                 [0.272, 0.534, 0.131]])
        
        sepia_img = img_array.dot(sepia_filter.T)
        sepia_img = np.clip(sepia_img, 0, 255).astype(np.uint8)
        
        return Image.fromarray(sepia_img, mode='RGB').convert('RGBA')
    
    def update_transform(self, transform_type, value):
        self.transform_values[transform_type] = float(value)
        self.apply_transforms()
    
    def apply_transforms(self):
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
        
        # Apply scale
        scale_x = self.transform_values['scale_x'] / 100.0
        scale_y = self.transform_values['scale_y'] / 100.0
        if scale_x != 1.0 or scale_y != 1.0:
            new_width = int(img.width * scale_x)
            new_height = int(img.height * scale_y)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        self.current_image = img
        self.update_image_preview()
    
    def interactive_crop(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded")
            return
        
        # Save state before cropping
        self.save_state()
        
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

    def interactive_draw(self):
        """Interactive drawing popup — optimized, with working color picker and text size."""
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded")
            return

        # Save pre-draw state for undo
        self.save_state()

        draw_window = tk.Toplevel(self)
        draw_window.title("Interactive Drawing & Annotation")
        draw_window.geometry("900x700")
        draw_window.configure(bg="#2b2b2b")

        # Full-size working copy (real image) and scaled preview
        working_img = self.current_image.convert("RGBA").copy()
        preview_img = working_img.copy()
        preview_img.thumbnail((800, 600), Image.Resampling.LANCZOS)

        self.draw_preview_img = preview_img
        self.draw_preview_tk = ImageTk.PhotoImage(preview_img)

        canvas = tk.Canvas(draw_window, bg="#404040", cursor="crosshair")
        canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # initial create - actual center drawing happens in refresh
        canvas.create_image(450, 350, image=self.draw_preview_tk, anchor=tk.CENTER)

        # ===== Toolbar =====
        toolbar = ttk.Frame(draw_window)
        toolbar.pack(fill=tk.X, pady=5)

        self.drawing_tool = tk.StringVar(value="freehand")
        self.draw_color = "#ff0000"
        self.brush_size = tk.IntVar(value=3)
        self.text_to_add = tk.StringVar(value="Sample Text")
        self.text_size = tk.IntVar(value=36)  # default text size

        # Tools radio buttons
        for tool in ["freehand", "line", "rectangle", "circle", "text", "fill"]:
            ttk.Radiobutton(toolbar, text=tool.title(),
                            variable=self.drawing_tool, value=tool).pack(side=tk.LEFT, padx=4)

        # Brush size
        ttk.Label(toolbar, text="Brush:").pack(side=tk.LEFT, padx=(8, 0))
        ttk.Spinbox(toolbar, from_=1, to=50, textvariable=self.brush_size, width=4).pack(side=tk.LEFT, padx=4)

        # Color swatch + button
        color_swatch = tk.Canvas(toolbar, width=28, height=18, highlightthickness=1)
        color_swatch.create_rectangle(0, 0, 28, 18, fill=self.draw_color, outline="black")
        color_swatch.pack(side=tk.LEFT, padx=(8, 4))
        ttk.Button(toolbar, text="Color", command=lambda: self.pick_color(draw_window, color_swatch)).pack(side=tk.LEFT)

        # Text input and size
        ttk.Entry(toolbar, textvariable=self.text_to_add, width=20).pack(side=tk.LEFT, padx=6)
        ttk.Label(toolbar, text="Text size:").pack(side=tk.LEFT, padx=(6, 0))
        ttk.Spinbox(toolbar, from_=8, to=200, textvariable=self.text_size, width=5).pack(side=tk.LEFT, padx=4)

        # Apply / Cancel
        ttk.Button(toolbar, text="Apply",
                   command=lambda: self._apply_direct_drawing(working_img, draw_window)).pack(side=tk.RIGHT, padx=6)
        ttk.Button(toolbar, text="Cancel", command=draw_window.destroy).pack(side=tk.RIGHT)

        # ===== Drawing setup =====
        draw_layer = Image.new("RGBA", working_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(draw_layer)

        scale_x = working_img.width / preview_img.width
        scale_y = working_img.height / preview_img.height
        self._draw_layer = draw_layer
        self._working_img = working_img

        self.last_point = None
        self._refresh_pending = False
        self._temp_shape = None

        def canvas_to_image_coords(x, y):
            # Map canvas coords to original image coords (account for centered preview)
            offset_x = (canvas.winfo_width() - preview_img.width) // 2
            offset_y = (canvas.winfo_height() - preview_img.height) // 2
            return int((x - offset_x) * scale_x), int((y - offset_y) * scale_y)

        def refresh_preview_debounced():
            """Throttled preview updater for smoother drawing."""
            if self._refresh_pending:
                return
            self._refresh_pending = True

            def _update():
                merged = Image.alpha_composite(working_img, draw_layer)
                preview = merged.copy()
                preview.thumbnail((800, 600), Image.Resampling.LANCZOS)
                self.draw_preview_tk = ImageTk.PhotoImage(preview)
                canvas.delete("all")
                canvas.create_image(canvas.winfo_width() / 2, canvas.winfo_height() / 2,
                                    image=self.draw_preview_tk, anchor=tk.CENTER)
                self._refresh_pending = False

            canvas.after(50, _update)  # redraw ~20fps

        def on_press(e):
            self.last_point = (e.x, e.y)
            tool = self.drawing_tool.get()
            if tool == "text":
                ix, iy = canvas_to_image_coords(e.x, e.y)
                font = self._get_font(self.text_size.get())
                draw.text((ix, iy), self.text_to_add.get(), fill=self.draw_color, font=font)
                refresh_preview_debounced()
            elif tool == "fill":
                ix, iy = canvas_to_image_coords(e.x, e.y)
                self._bucket_fill(draw_layer, ix, iy, self.draw_color)
                refresh_preview_debounced()

        def on_drag(e):
            tool = self.drawing_tool.get()
            if not self.last_point:
                return

            if tool == "freehand":
                x1, y1 = canvas_to_image_coords(*self.last_point)
                x2, y2 = canvas_to_image_coords(e.x, e.y)
                draw.line((x1, y1, x2, y2), fill=self.draw_color, width=self.brush_size.get())
                self.last_point = (e.x, e.y)
                refresh_preview_debounced()

            elif tool in ("rectangle", "circle", "line"):
                if self._temp_shape:
                    canvas.delete(self._temp_shape)
                if tool == "rectangle":
                    self._temp_shape = canvas.create_rectangle(self.last_point[0], self.last_point[1], e.x, e.y,
                                                               outline=self.draw_color, width=self.brush_size.get())
                elif tool == "circle":
                    self._temp_shape = canvas.create_oval(self.last_point[0], self.last_point[1], e.x, e.y,
                                                          outline=self.draw_color, width=self.brush_size.get())
                elif tool == "line":
                    self._temp_shape = canvas.create_line(self.last_point[0], self.last_point[1], e.x, e.y,
                                                          fill=self.draw_color, width=self.brush_size.get())

        def on_release(e):
            tool = self.drawing_tool.get()
            if tool in ("rectangle", "circle", "line"):
                x1, y1 = canvas_to_image_coords(*self.last_point)
                x2, y2 = canvas_to_image_coords(e.x, e.y)
                if tool == "rectangle":
                    draw.rectangle([x1, y1, x2, y2], outline=self.draw_color, width=self.brush_size.get())
                elif tool == "circle":
                    draw.ellipse([x1, y1, x2, y2], outline=self.draw_color, width=self.brush_size.get())
                elif tool == "line":
                    draw.line([x1, y1, x2, y2], fill=self.draw_color, width=self.brush_size.get())
                refresh_preview_debounced()
                if self._temp_shape:
                    canvas.delete(self._temp_shape)
            self.last_point = None

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)

    def pick_color(self, parent, swatch_widget=None):
        """Open color chooser and update swatch + active color."""
        from tkinter import colorchooser
        color = colorchooser.askcolor(title="Choose Color", parent=parent)
        if color and color[1]:
            self.draw_color = color[1]  # e.g. "#rrggbb"
            if swatch_widget is not None:
                swatch_widget.delete("all")
                swatch_widget.create_rectangle(0, 0, 28, 18, fill=self.draw_color, outline="black")

    def _get_font(self, size):
        """Return a PIL.ImageFont (try common TTFs, fall back to default)."""
        from PIL import ImageFont
        candidates = ["arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
        for f in candidates:
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                continue
        # fallback: default font (size won't change)
        return ImageFont.load_default()

    def _apply_direct_drawing(self, working_img, window):
        """Merge drawn layer directly with image and save state."""
        if hasattr(self, "_draw_layer"):
            merged = Image.alpha_composite(working_img.convert("RGBA"), self._draw_layer.convert("RGBA"))
            self.current_image = merged
            self.update_image_preview()
            # Save the new state so Undo works
            self.save_state()
        window.destroy()

    def _bucket_fill(self, img, x, y, color):
        """Fast flood fill using NumPy (works on RGBA Image pasted as array)."""
        import numpy as np
        pixels = np.array(img)  # shape (h, w, 4)
        h, w = pixels.shape[:2]
        if not (0 <= x < w and 0 <= y < h):
            return

        target = pixels[y, x].copy()
        # parse color "#rrggbb" to RGBA
        fill_rgb = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
        fill = np.array(fill_rgb + [255], dtype=np.uint8)

        if np.all(target == fill):
            return

        mask = np.zeros((h, w), dtype=bool)
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if 0 <= cx < w and 0 <= cy < h and not mask[cy, cx] and np.all(pixels[cy, cx] == target):
                mask[cy, cx] = True
                stack.extend([(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)])
        pixels[mask] = fill
        img.paste(Image.fromarray(pixels, "RGBA"))

    def reflect(self, direction):
        """Apply reflection (flip)"""
        if self.current_image is None:
            return
        
        # Save state before reflection
        self.save_state()
        
        if direction == 'horizontal':
            self.current_image = ImageOps.mirror(self.current_image)
        elif direction == 'vertical':
            self.current_image = ImageOps.flip(self.current_image)
        
        self.update_image_preview()
    
    def _adjust_preview(self, value=None):
        """Apply color adjustments and update preview"""
        if self.current_image is None:
            return
        img = self.apply_all_adjustments()
        self.update_image_preview(img)
        self._update_histogram(img)
    
    def update_image_preview(self, img=None):
        """Update the image display with optional custom image"""
        self._update_histogram(img)
        if img is None:
            img = self.current_image

        if img is None:
            return

        # Get current size of the center frame
        try:
            max_display_width = self.center_frame.winfo_width() - 20 # Padding
            max_display_height = self.center_frame.winfo_height() - 20 # Padding
        except:
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
        if self.original_image is not None:
            self.current_image = self.original_image.copy()
            self.reset_all_sliders()
            self.update_image_preview()
    
    def reset_all_sliders(self):
        # Reset transform values
        self.transform_values = {
            'resize': 100,
            'rotate': 0,
            'scale_x': 100,
            'scale_y': 100,
        }
        
        # Reset all slider widgets
        for key, (slider, entry, var, default) in self.slider_widgets.items():
            var.set(default)
        
        # Reset color adjustment variables
        self.exposure_var.set(0)
        self.highlights_var.set(0)
        self.shadows_var.set(0)
        self.contrast_var.set(0)
        self.brightness_var.set(0)
        self.blacks_var.set(0)
        self.whites_var.set(0)
        self.hue_var.set(0)
        self.tint_var.set(0)
        self.saturation_var.set(0)
        self.temperature_var.set(0)
        self.vibrance_var.set(0)
        self.blur_var.set(0)
        self.noise_var.set(0)
        self.vignette_var.set(0)
        if hasattr(self, "perspective_values"):
            for k in self.perspective_values:
                self.perspective_values[k] = 0

    def run(self):
        self.mainloop()

if __name__ == "__main__":
    app = AdvancedImageProcessor()
    app.run()