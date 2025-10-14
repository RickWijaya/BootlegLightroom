import io
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageFilter, ImageOps, ImageEnhance, ImageDraw, ImageFont
import numpy as np
import cv2
import requests
from io import BytesIO
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import colorsys
from collections import deque


# ===========================================================
# BALR - Advanced Image Processor (tidy & collapsible panels)
# ===========================================================
class AdvancedImageProcessor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BALR - Advanced Image Processor")
        self.geometry("1400x850")
        self.minsize(1200, 720)

        # base bg
        self.configure(bg="#0b1220")

        # ttk style
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self._setup_dark_theme()
        self._setup_dpi_awareness()

        # ====== STATE ======
        self.original_image = None
        self.current_image = None
        self.preview_image_tk = None

        # Undo/Redo (simpan sebagai PNG bytes)
        self.undo_stack = deque(maxlen=5)
        self.redo_stack = deque(maxlen=5)

        # Transform values
        self.transform_values = {"resize": 100, "rotate": 0, "scale_x": 100, "scale_y": 100}

        # Store slider refs & debounce map
        self.slider_widgets = {}
        self._debounce_after_ids = {}

        # API Key placeholder
        self.api_key = ""
        self.prompt = ""

        # Color/adjustment variables
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

        # Morphology
        self.kernel_size_var = tk.IntVar(value=3)

        # Perspective values
        self.perspective_values = {
            "Top Left X": 0.0, "Top Left Y": 0.0,
            "Top Right X": 0.0, "Top Right Y": 0.0,
            "Bottom Left X": 0.0, "Bottom Left Y": 0.0,
            "Bottom Right X": 0.0, "Bottom Right Y": 0.0,
        }

        # collapse flags
        self.left_collapsed = False
        self.right_collapsed = False

        # Build UI
        self._overlay = None
        self._build_ui()

        # resize preview on window resize
        self.bind("<Configure>", lambda e: self.update_image_preview())

    # =========================
    # THEME & DPI
    # =========================
    def _setup_dark_theme(self):
        bg = "#0b1220"
        pane = "#0f1629"
        fg = "#e6e9ef"
        soft = "#94a3b8"
        accent = "#5661b3"
        accent_hover = "#2ca7a4"
        accent_press = "#3c537a"
        tab_bg = "#10182a"
        tab_sel = "#1a2238"

        self.style.configure("TFrame", background=bg)
        self.style.configure("Pane.TFrame", background=pane)
        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("TLabelframe", background=bg, foreground=fg)
        self.style.configure("TLabelframe.Label", background=bg, foreground=fg)
        self.style.configure("Header.TLabel", font=("Inter", 10, "bold"), foreground="#dce3f0", background="#0e1117")

        # Buttons (ttk)
        self.style.configure(
            "Accent.TButton",
            font=("Inter", 10, "bold"),
            padding=8,
            background=accent,
            foreground="white",
            borderwidth=0,
        )
        self.style.map(
            "Accent.TButton",
            background=[("active", accent_hover), ("pressed", accent_press)],
            relief=[("pressed", "sunken")],
            foreground=[("disabled", soft)],
        )

        # Sliders / Entries / Notebook
        self.style.configure("TScale", background=bg, troughcolor="#273449")
        self.style.configure("TEntry", fieldbackground="#172033", foreground="white",
                             insertcolor="white", borderwidth=1)
        self.style.configure("TNotebook", background=bg, borderwidth=0, tabmargins=(6, 4, 6, 0))
        self.style.configure("TNotebook.Tab", background=tab_bg, foreground="#e8eefc",
                             padding=(12, 8), font=("Inter", 9, "bold"))
        self.style.map("TNotebook.Tab",
                       background=[("selected", tab_sel)],
                       foreground=[("selected", "#ffffff")])

    def _setup_dpi_awareness(self):
        try:
            if self.tk.call('tk', 'windowingsystem') == 'win32':
                self.tk.call('tk', 'scaling', self.winfo_fpixels('1i') / 72.0)
        except Exception:
            pass

    # =========================
    # UI BUILD
    # =========================
    def _build_ui(self):
        # ---------- Top bar (HITAM, no glass) ----------
        topbar = tk.Frame(self, height=56, bg="#0e1117")
        topbar.pack(fill=tk.X, side=tk.TOP)
        topbar.pack_propagate(False)

        btn_frame = tk.Frame(topbar, bg="#0e1117")
        btn_frame.pack(side=tk.LEFT, padx=5, pady=4)

        self.btns = {}
        def add_btn(key, text, cmd):
            b = self._create_rounded_button(btn_frame, text=text, command=cmd)
            b.pack(side=tk.LEFT, padx=8)
            self.btns[key] = b

        add_btn("open", "Open", self.open_image)
        add_btn("save", "Save", self.save_image)
        add_btn("gen", "Generate AI Image", self.generate_ai_image)
        add_btn("reset", "Reset", self.reset_image)
        add_btn("undo", "Undo", self.undo)
        add_btn("redo", "Redo", self.redo)
        add_btn("enchance" ,"Enchance Image", self.enhance_image)
        add_btn("remove","Remove Background",self.remove_background)
        self.filter_var = tk.StringVar(value="Oil Paint")
        filters = [
            "winterblues",
            "wispy",
            "geode",
            "sketchy",
            "dystopia",
            "pastel",
            "moonlight",
            "rainbow",
            "popsketch",
            "badlands",
            "flora",
            "galaxy",
            "crushedmarble",
            "haze",
            "shamrock",
            "flare",
            "rosegold",
            "nightcore",
            "soul",
            "rosequartz",
            "animation",
            "feast",
            "undead",
            "highlight",
            "neopop",
            "midnight",
            "colorbright",
            "cartoon1",
            "cartoon2",
        ]

        ttk.Label(topbar, text="Artistic Filter:").pack(side=tk.LEFT, padx=5)
        filter_menu = ttk.OptionMenu(topbar, self.filter_var, filters[0], *filters)
        filter_menu.pack(side=tk.LEFT, padx=2)
        ttk.Button(topbar, text="Apply Artistic Filter", command=self.apply_artistic_filter).pack(side=tk.LEFT, padx=4)
        self.status_label = ttk.Label(topbar, text="No image loaded", style="Header.TLabel")
        self.status_label.pack(side=tk.RIGHT, padx=12)
        content = tk.Frame(self, bg="#0b1220")
        content.pack(fill=tk.BOTH, expand=True)
        content.grid_columnconfigure(0, weight=0)  # left
        content.grid_columnconfigure(1, weight=0)  # left toggle
        content.grid_columnconfigure(2, weight=1)  # center
        content.grid_columnconfigure(3, weight=0)  # right toggle
        content.grid_columnconfigure(4, weight=0)  # right
        content.grid_rowconfigure(0, weight=1)

        # Left panel (scrollable)
        self.left_wrap = tk.Frame(content, bg="#0b1220")
        self.left_wrap.grid(row=0, column=0, sticky="ns", padx=(10, 4), pady=10)

        self.left_inner = self._make_vscroll_area(self.left_wrap, width=320, bg="#0b1220")
        self._build_left_panel(self.left_inner)

        # Left toggle
        left_toggle_col = tk.Frame(content, bg="#0b1220", width=26)
        left_toggle_col.grid(row=0, column=1, sticky="ns", pady=10)
        left_toggle_col.grid_propagate(False)
        self.left_toggle_btn = ttk.Button(left_toggle_col, text="◀", width=2,
                                          style="Accent.TButton", command=self.toggle_left_panel)
        self.left_toggle_btn.pack(pady=6)

        # Center (preview)
        self.center_frame = tk.Frame(content, bg="#0f1826", highlightthickness=3, highlightbackground="#4c86a8")
        self.center_frame.grid(row=0, column=2, sticky="nsew", padx=4, pady=10)

        self.image_label = tk.Label(self.center_frame, bg="#0f1826")
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Right toggle
        right_toggle_col = tk.Frame(content, bg="#0b1220", width=26)
        right_toggle_col.grid(row=0, column=3, sticky="ns", pady=10)
        right_toggle_col.grid_propagate(False)
        self.right_toggle_btn = ttk.Button(right_toggle_col, text="▶", width=2,
                                           style="Accent.TButton", command=self.toggle_right_panel)
        self.right_toggle_btn.pack(pady=6)

        # Right panel
        self.right_wrap = tk.Frame(content, bg="#0b1220")
        self.right_wrap.grid(row=0, column=4, sticky="ns", padx=(4, 10), pady=10)

        # Histogram (kotak)
        hist_group = ttk.Labelframe(self.right_wrap, text="Histogram")
        hist_group.pack(fill=tk.X, pady=(0, 8))

        fig = Figure(figsize=(4.4, 3.1), dpi=100, facecolor="#0f1826")
        self.hist_ax = fig.add_subplot(111)
        self.hist_ax.set_facecolor("#0f1826")
        self.hist_ax.tick_params(colors="white")
        self.hist_ax.set_title("Histogram", color="white", fontsize=10)
        self.hist_canvas = FigureCanvasTkAgg(fig, master=hist_group)
        self.hist_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Controls (tabs)
        control_box = tk.Frame(self.right_wrap, bg="#0b1220")
        control_box.pack(fill=tk.BOTH, expand=True)

        nav = tk.Frame(control_box, bg="#0b1220")
        nav.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(nav, text="◀", width=2, style="Accent.TButton",
                   command=lambda: self._cycle_tab(self.adjust_nb, -1)).pack(side=tk.LEFT)
        ttk.Button(nav, text="▶", width=2, style="Accent.TButton",
                   command=lambda: self._cycle_tab(self.adjust_nb, 1)).pack(side=tk.RIGHT)

        self.adjust_nb = ttk.Notebook(control_box)
        self.adjust_nb.pack(fill=tk.BOTH, expand=True)

        # Tabs (scrollable)
        # Basic
        basic_outer = tk.Frame(self.adjust_nb, bg="#0b1220")
        self.adjust_nb.add(basic_outer, text="Basic")
        basic_inner, _ = self._make_vscroll_area(basic_outer, return_canvas=True)
        self._build_basic_tab(basic_inner)

        # Color
        color_outer = tk.Frame(self.adjust_nb, bg="#0b1220")
        self.adjust_nb.add(color_outer, text="Color")
        color_inner, _ = self._make_vscroll_area(color_outer, return_canvas=True)
        self._build_color_tab(color_inner)

        # Morphology
        morph_outer = tk.Frame(self.adjust_nb, bg="#0b1220")
        self.adjust_nb.add(morph_outer, text="Morphology")
        morph_inner, _ = self._make_vscroll_area(morph_outer, return_canvas=True)
        self._build_morphology_tab(morph_inner)

        # Filters
        filt_outer = tk.Frame(self.adjust_nb, bg="#0b1220")
        self.adjust_nb.add(filt_outer, text="Filters")
        filt_inner, _ = self._make_vscroll_area(filt_outer, return_canvas=True)
        self._build_filters_tab(filt_inner)

        # Frequency
        freq_outer = tk.Frame(self.adjust_nb, bg="#0b1220")
        self.adjust_nb.add(freq_outer, text="Frequency")
        freq_inner, _ = self._make_vscroll_area(freq_outer, return_canvas=True)
        self._build_frequency_tab(freq_inner)

        # Enhancement
        ench_outer = tk.Frame(self.adjust_nb, bg="#0b1220")
        self.adjust_nb.add(ench_outer, text="Enhancement")
        ench_inner, _ = self._make_vscroll_area(ench_outer, return_canvas=True)
        self._build_enhancement_tab(ench_inner)

        # Set awal state toolbar
        self._update_toolbar_state(has_image=False)

    # ---------- COLLAPSE TOGGLES ----------
    def toggle_left_panel(self):
        if not self.left_collapsed:
            # hide
            self.left_wrap.grid_remove()
            self.left_collapsed = True
            self.left_toggle_btn.configure(text="▶")
        else:
            # show
            self.left_wrap.grid()
            self.left_collapsed = False
            self.left_toggle_btn.configure(text="◀")
        self.update_image_preview()

    def toggle_right_panel(self):
        if not self.right_collapsed:
            self.right_wrap.grid_remove()
            self.right_collapsed = True
            self.right_toggle_btn.configure(text="◀")
        else:
            self.right_wrap.grid()
            self.right_collapsed = False
            self.right_toggle_btn.configure(text="▶")
        self.update_image_preview()

    # ---------- helpers: scrollable area ----------
    def _make_vscroll_area(self, parent, width=None, bg="#0b1220", return_canvas=False):
        """
        Create vertical scroll area inside parent.
        Return: inner frame (and canvas if return_canvas=True)
        """
        holder = tk.Frame(parent, bg=bg)
        holder.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(holder, bg=bg, highlightthickness=0, bd=0)
        vbar = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        holder.grid_rowconfigure(0, weight=1)
        holder.grid_columnconfigure(0, weight=1)

        inner = ttk.Frame(canvas)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        if width:
            canvas.config(width=width)

        def _on_inner_config(_=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        inner.bind("<Configure>", _on_inner_config)

        def _on_canvas_config(event):
            # keep inner width == canvas width
            canvas.itemconfigure(win_id, width=event.width)
        canvas.bind("<Configure>", _on_canvas_config)

        # Enable mouse wheel scrolling
        self._enable_mousewheel(inner, canvas)

        if return_canvas:
            return inner, canvas
        return inner
    #Uh -Rick
    def _enable_mousewheel(self, widget, canvas):
        def _on_mousewheel(event):
            if sys.platform == "darwin":
                delta = 1 if event.delta > 0 else -1
                canvas.yview_scroll(-delta, "units")
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"

        widget.bind("<Enter>", lambda e: widget.bind_all("<MouseWheel>", _on_mousewheel))
        widget.bind("<Leave>", lambda e: widget.unbind_all("<MouseWheel>"))

    # =========================
    # BUILD PANELS
    # =========================
    def _build_left_panel(self, parent):
        # Transform
        tf = ttk.Labelframe(parent, text="Transform")
        tf.pack(fill=tk.X, padx=6, pady=6)

        self._add_slider_with_entry(tf, "Resize (%)", "resize", 10, 200, 100, lambda v: self.update_transform("resize", v))
        self._add_slider_with_entry(tf, "Rotate (°)", "rotate", -180, 180, 0, lambda v: self.update_transform("rotate", v))

        ttk.Button(tf, text="Crop (Interactive)", style="Accent.TButton",
                   command=self.interactive_crop).pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(tf, text="Draw / Annotate (Interactive)", style="Accent.TButton",
                   command=self.interactive_draw).pack(fill=tk.X, padx=4, pady=4)

        self._add_slider_with_entry(tf, "Scale X (%)", "scale_x", 10, 200, 100, lambda v: self.update_transform("scale_x", v))
        self._add_slider_with_entry(tf, "Scale Y (%)", "scale_y", 10, 200, 100, lambda v: self.update_transform("scale_y", v))

        ttk.Button(tf, text="Flip Horizontal", style="Accent.TButton",
                   command=lambda: self.reflect("horizontal")).pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(tf, text="Flip Vertical", style="Accent.TButton",
                   command=lambda: self.reflect("vertical")).pack(fill=tk.X, padx=4, pady=4)

        # Perspective
        pf = ttk.Labelframe(parent, text="Perspective")
        pf.pack(fill=tk.X, padx=6, pady=6)

        corners = [
            "Top Left X", "Top Left Y",
            "Top Right X", "Top Right Y",
            "Bottom Left X", "Bottom Left Y",
            "Bottom Right X", "Bottom Right Y",
        ]
        for key in corners:
            self._add_slider_with_entry(pf, key, key, -1000, 1000, 0, lambda v, k=key: self.update_perspective(k, v))

    def _build_basic_tab(self, parent):
        self._add_slider_with_entry(parent, "Exposure", "exposure", -100, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(parent, "Highlights", "highlights", -100, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(parent, "Shadows", "shadows", -100, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(parent, "Contrast", "contrast", -100, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(parent, "Brightness", "brightness", -100, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(parent, "Blacks", "blacks", -100, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(parent, "Whites", "whites", -100, 100, 0, self._adjust_preview)

    def _build_color_tab(self, parent):
        self._add_slider_with_entry(parent, "Hue", "hue", -180, 180, 0, self._adjust_preview)
        self._add_slider_with_entry(parent, "Tint (G/M)", "tint", -100, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(parent, "Saturation", "saturation", -100, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(parent, "Temperature", "temperature", -100, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(parent, "Vibrance", "vibrance", -100, 100, 0, self._adjust_preview)

    def _build_morphology_tab(self, parent):
        ttk.Label(parent, text="Kernel Size (odd):").pack(pady=5)
        krow = ttk.Frame(parent)
        krow.pack(fill=tk.X, padx=10, pady=(0, 8))

        k_slider = ttk.Scale(krow, from_=1, to=15, orient=tk.HORIZONTAL)
        k_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        k_entry = ttk.Entry(krow, width=5)
        k_entry.pack(side=tk.RIGHT, padx=6)
        k_entry.insert(0, "3")

        def _to_odd(v):
            v = int(round(float(v)))
            return v if v % 2 == 1 else v + 1

        def _sync_from_scale(_=None):
            v = _to_odd(k_slider.get())
            if self.kernel_size_var.get() != v:
                self.kernel_size_var.set(v)
            k_entry.delete(0, tk.END)
            k_entry.insert(0, str(v))

        def _sync_from_entry(_=None):
            try:
                v = _to_odd(k_entry.get())
            except Exception:
                v = 3
            k_slider.set(v)
            self.kernel_size_var.set(v)

        k_slider.configure(command=_sync_from_scale)
        k_entry.bind("<Return>", _sync_from_entry)
        k_entry.bind("<FocusOut>", _sync_from_entry)

        self.slider_widgets["kernel_size"] = (k_slider, k_entry, self.kernel_size_var, 3)

        for text, op, title in [
            ("Erosion",  'erosion',  "Applying Erosion..."),
            ("Dilation", 'dilation', "Applying Dilation..."),
            ("Opening",  'opening',  "Applying Opening..."),
            ("Closing",  'closing',  "Applying Closing..."),
            ("Gradient", 'gradient', "Applying Gradient..."),
            ("Mean", 'mean', "Applying Mean Morphology..."),
            ("Median", 'median', "Applying Median Morphology..."),
            ("Max", 'max', "Applying Max Morphology..."),
            ("Min", 'min', "Applying Min Morphology...")
        ]:
            ttk.Button(parent, text=text, style="Accent.TButton",
                       command=lambda op=op, title=title: self._with_overlay(self.apply_morphology, op, title=title)
                       ).pack(fill=tk.X, padx=10, pady=4)

    def _build_filters_tab(self, parent):
        self._add_slider_with_entry(parent, "Blur", "blur", 0, 20, 0, self._adjust_preview)
        self._add_slider_with_entry(parent, "Noise", "noise", 0, 100, 0, self._adjust_preview)
        self._add_slider_with_entry(parent, "Vignette", "vignette", 0, 100, 0, self._adjust_preview)

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, pady=10)
        ttk.Label(parent, text="Quick Filters").pack(pady=(0, 6))

        ttk.Button(parent, text="Grayscale", style="Accent.TButton",
                   command=lambda: self._with_overlay(self.apply_filter, "grayscale", title="Applying Grayscale...")
                   ).pack(fill=tk.X, padx=10, pady=4)
        ttk.Button(parent, text="Sepia", style="Accent.TButton",
                   command=lambda: self._with_overlay(self.apply_filter, "sepia", title="Applying Sepia...")
                   ).pack(fill=tk.X, padx=10, pady=4)
        ttk.Button(parent, text="Edge Detection", style="Accent.TButton",
                   command=lambda: self._with_overlay(self.apply_filter, "edge", title="Detecting Edges...")
                   ).pack(fill=tk.X, padx=10, pady=4)
        ttk.Button(parent, text="Emboss", style="Accent.TButton",
                   command=lambda: self._with_overlay(self.apply_filter, "emboss", title="Applying Emboss...")
                   ).pack(fill=tk.X, padx=10, pady=4)
        ttk.Button(parent, text="Sharpen", style="Accent.TButton",
                   command=lambda: self._with_overlay(self.apply_filter, "sharpen", title="Sharpening...")
                   ).pack(fill=tk.X, padx=10, pady=4)
        ttk.Button(parent, text="Sobel", style="Accent.TButton",
                   command=lambda: self._with_overlay(self.apply_filter, "sobel", title="Applying Sobel...")
                   ).pack(fill=tk.X, padx=10, pady=4)
        ttk.Button(parent, text="Prewitt", style="Accent.TButton",
                   command=lambda: self._with_overlay(self.apply_filter, "prewitt", title="Applying Prewitt...")
                   ).pack(fill=tk.X, padx=10, pady=4)
        ttk.Button(parent, text="Laplacian", style="Accent.TButton",
                   command=lambda: self._with_overlay(self.apply_filter, "laplacian", title="Applying Laplacian...")
                   ).pack(fill=tk.X, padx=10, pady=4)
        
    def _build_frequency_tab(self, parent):
        ttk.Label(parent, text="Apply Frequency Transformations:").pack(anchor="w", padx=10, pady=(4, 6))
        ttk.Button(parent, text="Fourier Transform (FFT)", style="Accent.TButton",
                   command=lambda: self._with_overlay(self._apply_fft, title="Computing FFT...")
                   ).pack(fill=tk.X, padx=10, pady=4)
        ttk.Button(parent, text="Inverse FFT", style="Accent.TButton",
                   command=lambda: self._with_overlay(self._apply_ifft, title="Computing Inverse FFT...")
                   ).pack(fill=tk.X, padx=10, pady=4)
        ttk.Button(parent, text="High Pass Filter", style="Accent.TButton",
                   command=lambda: self._with_overlay(self._apply_high_pass, title="Applying High Pass...")
                   ).pack(fill=tk.X, padx=10, pady=4)
        ttk.Button(parent, text="Low Pass Filter", style="Accent.TButton",
                   command=lambda: self._with_overlay(self._apply_low_pass, title="Applying Low Pass...")
                   ).pack(fill=tk.X, padx=10, pady=4)

    def _build_enhancement_tab(self, parent):
        ttk.Label(parent, text="Apply Enhancement Techniques:").pack(anchor="w", padx=10, pady=(4, 6))
        ttk.Button(parent, text="Auto Enhance", style="Accent.TButton",
                   command=lambda: self._with_overlay(self._auto_enhance, title="Auto Enhancing...")
                   ).pack(fill=tk.X, padx=10, pady=4)
        ttk.Button(parent, text="Sharpen", style="Accent.TButton",
                   command=lambda: self._with_overlay(self._sharpen_image, title="Sharpening...")
                   ).pack(fill=tk.X, padx=10, pady=4)
        ttk.Button(parent, text="Denoise", style="Accent.TButton",
                   command=lambda: self._with_overlay(self._denoise_image, title="Denoising...")
                   ).pack(fill=tk.X, padx=10, pady=4)
        ttk.Button(parent, text="Detail Boost", style="Accent.TButton",
                   command=lambda: self._with_overlay(self._boost_detail, title="Boosting Detail...")
                   ).pack(fill=tk.X, padx=10, pady=4)
        ttk.Separator(parent).pack(fill=tk.X, padx=10, pady=8)
        ttk.Label(parent, text="Additional Enhancements:").pack(anchor="w", padx=10, pady=(4, 6))

        # === Gamma Correction ===
        self._add_slider_with_entry(parent, "Gamma", "gamma", 0.1, 3.0, 1.0, None)
        ttk.Button(parent, text="Apply Gamma Correction", style="Accent.TButton",
                   command=self._apply_gamma_correction).pack(fill=tk.X, padx=10, pady=(4, 8))

        # === Global Thresholding ===
        self._add_slider_with_entry(parent, "Threshold", "threshold", 0, 255, 127, None)
        ttk.Button(parent, text="Apply Global Thresholding", style="Accent.TButton",
                   command=self._apply_global_threshold).pack(fill=tk.X, padx=10, pady=(4, 8))

        # === Adaptive Thresholding ===
        ttk.Button(parent, text="Apply Adaptive Thresholding", style="Accent.TButton",
                   command=self._apply_adaptive_threshold).pack(fill=tk.X, padx=10, pady=(4, 8))

        # === Smoothing ===
        self._add_slider_with_entry(parent, "Smoothing Kernel", "smooth_kernel", 1, 15, 5, None)
        ttk.Button(parent, text="Apply Smoothing", style="Accent.TButton",
                   command=self._apply_smoothing).pack(fill=tk.X, padx=10, pady=(4, 8))
    def _auto_enhance(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded!")
            return

        confirm = messagebox.askyesno(
            "Auto Enhance",
            "Apply automatic enhancement (lighting, contrast, color, sharpness, gamma correction)?"
        )
        if not confirm:
            return
        self.save_state()
        img = self.current_image.convert("RGB")
        img = ImageOps.autocontrast(img, cutoff=2)

        img_np = np.array(img).astype(np.float32)
        mean_per_channel = img_np.mean(axis=(0, 1), keepdims=True)
        img_np = np.clip(img_np / (mean_per_channel / 128), 0, 255).astype(np.uint8)
        img = Image.fromarray(img_np)

        img = ImageEnhance.Color(img).enhance(1.4)

        img = ImageEnhance.Contrast(img).enhance(1.3)

        img = ImageEnhance.Brightness(img).enhance(1.1)

        img = ImageEnhance.Sharpness(img).enhance(1.2)

        gamma = 1.05
        lut = [pow(x / 255.0, 1 / gamma) * 255 for x in range(256)]
        img = img.point(lut * 3)

        self.current_image = img.convert("RGBA")
        self.update_image_preview(self.current_image)
        self._update_toolbar_state()

    def _apply_gamma_correction(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded!")
            return

        confirm = messagebox.askyesno("Apply Gamma Correction", "Are you sure you want to apply Gamma Correction?")
        if not confirm:
            return

        gamma = float(self.slider_widgets.get("gamma", [None, None, None, 1.0])[2].get())
        invGamma = 1.0 / gamma
        table = np.array([(i / 255.0) ** invGamma * 255 for i in np.arange(256)]).astype("uint8")

        img_array = np.array(self.current_image)
        corrected = cv2.LUT(img_array, table)

        self.save_state()
        self.current_image = Image.fromarray(corrected).convert("RGBA")
        self.update_image_preview()
        self._update_toolbar_state()

    def _apply_global_threshold(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded!")
            return

        confirm = messagebox.askyesno("Apply Global Threshold", "Are you sure you want to apply Thresholding?")
        if not confirm:
            return

        val = int(self.slider_widgets.get("threshold", [None, None, None, 127])[2].get())
        gray = cv2.cvtColor(np.array(self.current_image), cv2.COLOR_RGBA2GRAY)
        _, thresh = cv2.threshold(gray, val, 255, cv2.THRESH_BINARY)

        self.save_state()
        self.current_image = Image.fromarray(thresh).convert("RGBA")
        self.update_image_preview()
        self._update_toolbar_state()

    def _apply_adaptive_threshold(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded!")
            return

        confirm = messagebox.askyesno("Apply Adaptive Threshold", "Are you sure you want to apply Adaptive Thresholding?")
        if not confirm:
            return

        gray = cv2.cvtColor(np.array(self.current_image), cv2.COLOR_RGBA2GRAY)
        adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY, 11, 2)

        self.save_state()
        self.current_image = Image.fromarray(adaptive).convert("RGBA")
        self.update_image_preview()
        self._update_toolbar_state()


    def _apply_smoothing(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded!")
            return

        confirm = messagebox.askyesno("Apply Smoothing", "Are you sure you want to apply Smoothing?")
        if not confirm:
            return

        k = int(self.slider_widgets.get("smooth_kernel", [None, None, None, 5])[2].get())
        if k % 2 == 0:
            k += 1

        result = cv2.GaussianBlur(np.array(self.current_image), (k, k), 0)

        self.save_state()
        self.current_image = Image.fromarray(result).convert("RGBA")
        self.update_image_preview()
        self._update_toolbar_state()

    def _cycle_tab(self, nb, step):
        try:
            count = nb.index('end')
        except Exception:
            return
        if count <= 0:
            return
        try:
            cur = nb.index(nb.select())
        except Exception:
            cur = 0
        nb.select((cur + step) % count)

    # =========================
    # HISTOGRAM
    # =========================
    def _update_histogram(self, img=None):
        if img is None:
            img = self.current_image
        if img is None:
            return
        img_array = np.array(img.convert("RGB"))
        self.hist_ax.clear()
        colors = ("r", "g", "b")
        for i, color in enumerate(colors):
            hist = cv2.calcHist([img_array], [i], None, [256], [0, 256])
            self.hist_ax.plot(hist, color=color)
        self.hist_ax.set_xlim([0, 256])
        self.hist_ax.set_facecolor("#0f1826")
        self.hist_ax.tick_params(colors="white")
        self.hist_ax.set_title("Histogram", color="white", fontsize=10)
        self.hist_canvas.draw_idle()

    # =========================
    # UNDO/REDO
    # =========================
    def save_state(self):
        if self.current_image is not None:
            img_bytes = BytesIO()
            self.current_image.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            self.undo_stack.append(img_bytes)
            self.redo_stack.clear()
            self._update_undo_redo_status()

    def undo(self):
        if len(self.undo_stack) > 1:
            if self.current_image is not None:
                img_bytes = BytesIO()
                self.current_image.save(img_bytes, format="PNG")
                img_bytes.seek(0)
                self.redo_stack.append(img_bytes)
            previous_state = self.undo_stack.pop()
            self.current_image = Image.open(previous_state).convert("RGBA")
            self.update_image_preview()
            self._update_undo_redo_status()
        else:
            messagebox.showinfo("Info", "Nothing to undo")

    def redo(self):
        if self.redo_stack:
            if self.current_image is not None:
                img_bytes = BytesIO()
                self.current_image.save(img_bytes, format="PNG")
                img_bytes.seek(0)
                self.undo_stack.append(img_bytes)
            next_state = self.redo_stack.pop()
            self.current_image = Image.open(next_state).convert("RGBA")
            self.update_image_preview()
            self._update_undo_redo_status()
        else:
            messagebox.showinfo("Info", "Nothing to redo")
    def _update_undo_redo_status(self):
        undo_count = len(self.undo_stack) - 1
        redo_count = len(self.redo_stack)
        status_parts = []
        if hasattr(self, "status_label") and self.status_label["text"] != "No image loaded":
            base_status = self.status_label["text"].split(" | ")[0]
            status_parts.append(base_status)
        if undo_count > 0:
            status_parts.append(f"Undo: {undo_count}/5")
        if redo_count > 0:
            status_parts.append(f"Redo: {redo_count}/5")
        if status_parts:
            self.status_label.config(text=" | ".join(status_parts))
        self._update_toolbar_state()

    def _update_toolbar_state(self, has_image=None):
        if not hasattr(self, 'btns'):
            return
        img_loaded = bool(self.current_image) if has_image is None else bool(has_image)

        self.btns["open"].set_enabled(True)
        self.btns["gen"].set_enabled(True)
        self.btns["save"].set_enabled(img_loaded)
        self.btns["reset"].set_enabled(img_loaded)
        self.btns["undo"].set_enabled(len(self.undo_stack) > 1)
        self.btns["redo"].set_enabled(len(self.redo_stack) > 0)

    # =========================
    # FILE OPS / AI GENERATION
    # =========================
    def enhance_image(self):
        API_KEY = "46440a95-8bee-4c5f-8fbc-ea9937e33a14" 

        if not hasattr(self, "original_image") or self.original_image is None:
            messagebox.showwarning("No Image", "Please open an image first.")
            return

        try:
            # Update status to show that it's processing
            self.status_label.config(text="Enhancing image... please wait.")
            self.status_label.update_idletasks()

            # Convert the current image to bytes (in memory)
            img_bytes = io.BytesIO()
            self.original_image.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            # Prepare request
            url = "https://api.topazlabs.com/image/v1/enhance"
            headers = {
                "X-API-Key": API_KEY,
                "accept": "image/jpeg"
            }

            # Prepare multipart/form-data body
            files = {
                "image": ("input.jpg", img_bytes, "image/jpeg")
            }
            data = {
                "model": "Standard V2",
                "face_enhancement": "true",
                "face_enhancement_strength": "0.8",
                "output_format": "jpeg"
            }

            # Send POST request
            response = requests.post(url, headers=headers, files=files, data=data)

            # Handle response
            if response.status_code == 200:
                # Read the enhanced image directly from memory
                enhanced_image = Image.open(io.BytesIO(response.content)).convert("RGB")

                # Replace current image in memory
                self.save_state()
                self.current_image = enhanced_image.copy()

                # Refresh UI
                self.reset_all_sliders()
                self.update_image_preview()
                self.status_label.config(text="✅ Image enhanced successfully!")

            else:
                messagebox.showerror("Error", f"Enhancement failed:\n{response.text}")
                self.status_label.config(text="❌ Enhancement failed.")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{e}")
            self.status_label.config(text="❌ Error during enhancement.")
    
    def remove_background(self):

        API_KEY = "QBNYHoxDwcRozkRNauzuH2Rp"

        # ✅ Check if an image is loaded
        if not hasattr(self, "original_image") or self.original_image is None:
            messagebox.showwarning("No Image", "Please open an image first.")
            return

        try:
            # Update status to show that it's processing
            self.status_label.config(text="Removing background... please wait.")
            self.status_label.update_idletasks()

            # Convert the current image to bytes (in memory)
            img_bytes = io.BytesIO()
            self.original_image.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            # Send the image to remove.bg API
            response = requests.post(
                "https://api.remove.bg/v1.0/removebg",
                files={"image_file": ("image.png", img_bytes, "image/png")},
                data={"size": "auto"},
                headers={"X-Api-Key": API_KEY},
            )

            # Handle response
            if response.status_code == requests.codes.ok:
                # Load the processed image directly from memory
                result_image = Image.open(io.BytesIO(response.content)).convert("RGBA")
                
                self.save_state()
                self.current_image = result_image.copy()

                # Reset sliders, refresh preview
                self.reset_all_sliders()
                self.update_image_preview()

                # Update status label
                self.status_label.config(text="✅ Background removed successfully!")

            else:
                messagebox.showerror("Error", f"Failed to remove background:\n{response.text}")
                self.status_label.config(text="❌ Background removal failed.")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{e}")
            self.status_label.config(text="❌ Error during background removal.")
            
    def apply_artistic_filter(self):
        selected_filter = self.filter_var.get().lower().replace(" ", "")
        if not self.current_image:
            messagebox.showwarning("No Image", "Please open an image first.")
            return
        confirm = messagebox.askyesno("Apply Filter", f"Are you sure you want to apply '{selected_filter}'?")
        if not confirm:
            return
        try:
            # Show loading overlay while processing
            self._show_loading_overlay(f"Applying '{selected_filter}' filter...")
            self.status_label.config(text=f"Applying Picsart effect: {selected_filter}...")
            self.status_label.update_idletasks()

            # Convert the current image in memory to binary data (JPG)
            img_buffer = BytesIO()
            img_to_send = self.current_image.convert("RGB")
            img_to_send.save(img_buffer, format="JPEG")
            img_buffer.seek(0)

            url = "https://api.picsart.io/tools/1.0/effects/ai"

            # Prepare multipart form-data payload
            files = {
                "image": ("image.jpg", img_buffer, "image/jpeg"),
            }
            data = {
                "effect_name": selected_filter,  # The chosen AI effect (like 'cartoon', 'pastel', etc.)
                "format": "PNG"
            }
            headers = {
            "accept": "application/json",
            "X-Picsart-API-key": "paat-sqWPSobBXjxFi8v6AFxA5NbTMmv",
            }
            # Send request to Picsart API
            response = requests.post(url, files=files, data=data, headers=headers, timeout=120)
            response.raise_for_status()
            result = response.json()

            # The API returns a URL for the processed image
            if "data" in result and "url" in result["data"]:
                image_url = result["data"]["url"]
            else:
                raise Exception(f"Unexpected response format:\n{result}")

            # Download the processed image
            img_response = requests.get(image_url, timeout=60)
            img_response.raise_for_status()

            # Open and display the image
            processed_img = Image.open(BytesIO(img_response.content)).convert("RGB")
            self.current_image = processed_img
            self.save_state()
            self.update_image_preview()
            self.status_label.config(text=f"Applied '{selected_filter}' effect successfully.")
            self._update_toolbar_state(True)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply filter:\n{e}")
            self.status_label.config(text="Filter application failed.")

        finally:
            self._hide_loading_overlay()

    def generate_ai_image(self):
        prompt = simpledialog.askstring("AI Image Generation with Pollinations", "Enter your image prompt:")
        if not prompt:
            return
        try:
            self._show_loading_overlay("Generating with Pollinations...")
            self.status_label.config(text="Generating AI image...")
            self.status_label.update_idletasks()

            base_url = "https://image.pollinations.ai/prompt/"
            prompt_encoded = requests.utils.quote(prompt)
            url = f"{base_url}{prompt_encoded}?width=512&height=512&model=flux"
            response = requests.get(url, timeout=60)
            response.raise_for_status()

            img_data = BytesIO(response.content)
            img = Image.open(img_data).convert("RGB")

            self.original_image = img
            self.current_image = img.copy()
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.save_state()
            self.reset_all_sliders()
            self.update_image_preview()
            self.status_label.config(text=f"AI generated image from: '{prompt}'")
            self._update_toolbar_state(True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate image:\n{e}")
            self.status_label.config(text="AI image generation failed.")
        finally:
            self._hide_loading_overlay()

    def open_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tiff")]
        )
        if not path:
            return
        try:
            img = Image.open(path).convert("RGBA")
            self.original_image = img
            self.current_image = img.copy()
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.save_state()
            self.reset_all_sliders()
            self.update_image_preview()
            self.status_label.config(text=f"Loaded: {os.path.basename(path)} ({img.width}x{img.height})")
            self._update_toolbar_state(True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image:\n{e}")

    def save_image(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image to save")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp")]
        )
        if not path:
            return
        try:
            self._show_loading_overlay("Saving image...")
            img = self.apply_all_adjustments()
            if path.lower().endswith(".jpg") or path.lower().endswith(".jpeg"):
                img = img.convert("RGB")
            img.save(path)
            messagebox.showinfo("Success", f"Image saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image:\n{e}")
        finally:
            self._hide_loading_overlay()

    # =========================
    # ADJUSTMENTS PIPELINE
    # =========================
    def apply_all_adjustments(self):
        if self.current_image is None:
            return None
        img = self.current_image.copy()

        # Exposure
        exposure = float(self.exposure_var.get())
        if exposure != 0:
            factor = np.power(2, exposure / 100)
            img = ImageEnhance.Brightness(img).enhance(factor)

        # Highlights/Shadows
        highlights = float(self.highlights_var.get())
        shadows = float(self.shadows_var.get())
        if highlights != 0 or shadows != 0:
            img = self.adjust_highlights_shadows(img, highlights, shadows)

        # Contrast/Brightness
        contrast = float(self.contrast_var.get())
        brightness = float(self.brightness_var.get())
        if contrast != 0:
            img = ImageEnhance.Contrast(img).enhance(1 + (contrast / 100))
        if brightness != 0:
            img = ImageEnhance.Brightness(img).enhance(1 + (brightness / 100))

        # Blacks/Whites
        blacks = float(self.blacks_var.get())
        whites = float(self.whites_var.get())
        if blacks != 0 or whites != 0:
            img = self.adjust_levels(img, blacks, whites)

        # Color
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

        # Filters
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
        self.apply_perspective(preview=True)

    def apply_perspective(self, preview=False):
        if self.original_image is None:
            return
        img = np.array(self.original_image.convert("RGB"))
        h, w = img.shape[:2]
        src_pts = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
        tl_x = self.perspective_values["Top Left X"];     tl_y = self.perspective_values["Top Left Y"]
        tr_x = self.perspective_values["Top Right X"];    tr_y = self.perspective_values["Top Right Y"]
        bl_x = self.perspective_values["Bottom Left X"];  bl_y = self.perspective_values["Bottom Left Y"]
        br_x = self.perspective_values["Bottom Right X"]; br_y = self.perspective_values["Bottom Right Y"]
        dst_pts = np.float32([
            [0 + tl_x, 0 + tl_y],
            [w + tr_x, 0 + tr_y],
            [0 + bl_x, h + bl_y],
            [w + br_x, h + br_y],
        ])
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped = cv2.warpPerspective(img, M, (w, h))
        result = Image.fromarray(warped).convert("RGBA")
        self.current_image = result
        self.update_image_preview(result)
        if not preview:
            self.save_state()

    # =========================
    # ADJUSTMENT HELPERS
    # =========================
    def adjust_temperature(self, img, temperature):
        img_array = np.array(img.convert("RGB"), dtype=np.float32)
        if temperature > 0:
            img_array[:, :, 0] = np.clip(img_array[:, :, 0] + temperature * 2.55, 0, 255)
            img_array[:, :, 1] = np.clip(img_array[:, :, 1] + temperature * 1.27, 0, 255)
        else:
            img_array[:, :, 2] = np.clip(img_array[:, :, 2] - temperature * 2.55, 0, 255)
        return Image.fromarray(img_array.astype("uint8"), mode="RGB").convert("RGBA")

    def adjust_hue(self, img, shift_degrees):
        img_hsv = img.convert("HSV")
        img_array = np.array(img_hsv, dtype=np.uint8)
        shift_pil_units = int(shift_degrees * (255 / 360)) % 256
        hue_channel = img_array[:, :, 0]
        new_hue = (hue_channel.astype(np.int16) + shift_pil_units) % 256
        img_array[:, :, 0] = new_hue.astype(np.uint8)
        return Image.fromarray(img_array, mode="HSV").convert("RGBA")

    def adjust_tint(self, img, tint_value):
        img_rgb = img.convert("RGB")
        img_array = np.array(img_rgb, dtype=np.int16)
        adj_factor = tint_value / 100.0 * 50
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] + adj_factor, 0, 255)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] + adj_factor, 0, 255)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] - adj_factor, 0, 255)
        return Image.fromarray(img_array.astype("uint8"), mode="RGB").convert("RGBA")

    def adjust_vibrance(self, img, vibrance_value):
        if vibrance_value == 0:
            return img
        img_rgb = img.convert("RGB")
        factor = vibrance_value / 100.0 * 0.5
        img_list = img_rgb.getdata()

        def adjust_vibrance_pixel(r, g, b, f):
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            adjustment = f * (1 - s) ** 1.5
            new_s = np.clip(s + adjustment, 0, 1)
            r_out, g_out, b_out = colorsys.hsv_to_rgb(h, new_s, v)
            return int(r_out * 255), int(g_out * 255), int(b_out * 255)

        new_img_list = [adjust_vibrance_pixel(r, g, b, factor) for r, g, b in img_list]
        new_img = Image.new("RGB", img_rgb.size)
        new_img.putdata(new_img_list)
        return new_img.convert("RGBA")

    def adjust_highlights_shadows(self, img, highlights, shadows):
        img_array = np.array(img.convert("RGB")) / 255.0
        luminance = 0.2126 * img_array[:, :, 0] + 0.7152 * img_array[:, :, 1] + 0.0722 * img_array[:, :, 2]
        if shadows != 0:
            shadow_mask = 1 / (1 + np.exp((luminance - 0.25) / 0.1))
            shadow_adj = (shadows / 100.0) * shadow_mask * 0.5
            for i in range(3):
                img_array[:, :, i] = np.clip(img_array[:, :, i] + shadow_adj, 0, 1)
        if highlights != 0:
            highlight_mask = 1 / (1 + np.exp((0.75 - luminance) / 0.1))
            highlight_adj = (highlights / 100.0) * highlight_mask * 0.5
            for i in range(3):
                img_array[:, :, i] = np.clip(img_array[:, :, i] + highlight_adj, 0, 1)
        return Image.fromarray((img_array * 255).astype(np.uint8), mode="RGB").convert("RGBA")

    def adjust_levels(self, img, blacks, whites):
        img_array = np.array(img)
        if blacks != 0:
            adjustment = blacks / 100 * 50
            img_array = np.where(img_array < 128, np.clip(img_array + adjustment, 0, 255), img_array)
        if whites != 0:
            adjustment = whites / 100 * 50
            img_array = np.where(img_array > 128, np.clip(img_array + adjustment, 0, 255), img_array)
        return Image.fromarray(img_array.astype("uint8"), mode=img.mode)

    def add_noise(self, img, amount):
        arr = np.array(img)
        noise = np.random.normal(0, amount, arr.shape).astype(np.int16)
        noisy = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy, mode=img.mode)

    def add_vignette(self, img, strength):
        width, height = img.size
        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)
        X, Y = np.meshgrid(x, y)
        radius = np.sqrt(X ** 2 + Y ** 2)
        vignette = 1 - (radius * strength)
        vignette = np.clip(vignette, 0, 1)
        img_array = np.array(img).astype(float)
        for i in range(min(3, img_array.shape[2])):  # apply ke RGB saja
            img_array[:, :, i] *= vignette
        return Image.fromarray(img_array.astype("uint8"), mode=img.mode)

    # =========================
    # MORPH / FILTERS
    # =========================
    def apply_morphology(self, operation):
        if self.current_image is None:
            return
        img_array = np.array(self.current_image.convert("RGB"))
        kernel_size = int(self.kernel_size_var.get())
        if kernel_size < 1:
            kernel_size = 1
        if kernel_size % 2 == 0:
            kernel_size += 1
            self.kernel_size_var.set(kernel_size)
        kernel = np.ones((kernel_size, kernel_size), np.uint8)

        confirm = messagebox.askyesno("Apply Filter", f"Are you sure you want to apply '{operation}'?")
        if not confirm:
            return

        self.save_state()
        result = np.zeros_like(img_array)
        for i in range(3):
            channel = img_array[:, :, i]
            if operation == "erosion":
                result[:, :, i] = cv2.erode(channel, kernel, iterations=1)
            elif operation == "dilation":
                result[:, :, i] = cv2.dilate(channel, kernel, iterations=1)
            elif operation == "opening":
                result[:, :, i] = cv2.morphologyEx(channel, cv2.MORPH_OPEN, kernel)
            elif operation == "closing":
                result[:, :, i] = cv2.morphologyEx(channel, cv2.MORPH_CLOSE, kernel)
            elif operation == "gradient":
                result[:, :, i] = cv2.morphologyEx(channel, cv2.MORPH_GRADIENT, kernel)
            elif operation == 'mean':
                result[:,:,i] = cv2.blur(channel, (kernel_size, kernel_size))
            elif operation == 'median':
                ksize = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
                result[:,:,i] = cv2.medianBlur(channel, ksize)
            elif operation == 'max':
                kernel = np.ones((kernel_size, kernel_size), np.uint8)
                result[:,:,i] = cv2.dilate(channel, kernel)
            elif operation == 'min':
                kernel = np.ones((kernel_size, kernel_size), np.uint8)
                result[:,:,i] = cv2.erode(channel, kernel)

        self.current_image = Image.fromarray(result, mode="RGB").convert("RGBA")
        self.update_image_preview()
        self._update_toolbar_state()

    def apply_filter(self, filter_name):
        if self.current_image is None:
            return
        img = self.current_image
        confirm = messagebox.askyesno("Apply Filter", f"Are you sure you want to apply '{filter_name}'?")
        if not confirm:
            return

        self.save_state()
        if filter_name == "grayscale":
            img = ImageOps.grayscale(img).convert("RGBA")
        elif filter_name == "sepia":
            img = self.apply_sepia(img)
        elif filter_name == "edge":
            img = img.filter(ImageFilter.FIND_EDGES)
        elif filter_name == "emboss":
            img = img.filter(ImageFilter.EMBOSS)
        elif filter_name == "sharpen":
            img = img.filter(ImageFilter.SHARPEN)
        elif filter_name == 'sobel':
            img = self.apply_sobel(img)
        elif filter_name == 'prewitt':
            img = self.apply_prewitt(img)
        elif filter_name == 'laplacian':
            img = self.apply_laplacian(img)

        self.current_image = img
        self.update_image_preview()
        self._update_toolbar_state()

    def apply_sobel(self, img):
        # Convert to grayscale first
        img_gray = img.convert('L')
        img_array = np.array(img_gray, dtype=np.float32)

        # Apply Sobel operators
        sobel_x = cv2.Sobel(img_array, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(img_array, cv2.CV_64F, 0, 1, ksize=3)

        # Calculate magnitude
        magnitude = np.sqrt(sobel_x**2 + sobel_y**2)

        # Normalize to 0-255
        magnitude = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)

        # Convert back to PIL Image
        return Image.fromarray(magnitude.astype(np.uint8)).convert('RGBA')

    def apply_prewitt(self, img):
        # Convert to grayscale first
        img_gray = img.convert('L')
        img_array = np.array(img_gray, dtype=np.float32)

        # Prewitt kernels
        kernel_x = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]])
        kernel_y = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]])

        # Apply Prewitt operators
        prewitt_x = cv2.filter2D(img_array, cv2.CV_64F, kernel_x)
        prewitt_y = cv2.filter2D(img_array, cv2.CV_64F, kernel_y)

        # Calculate magnitude
        magnitude = np.sqrt(prewitt_x**2 + prewitt_y**2)

        # Normalize to 0-255
        magnitude = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)

        # Convert back to PIL Image
        return Image.fromarray(magnitude.astype(np.uint8)).convert('RGBA')

    def apply_laplacian(self, img):
        # Convert to grayscale first
        img_gray = img.convert('L')
        img_array = np.array(img_gray, dtype=np.float32)

        # Apply Laplacian
        laplacian = cv2.Laplacian(img_array, cv2.CV_64F, ksize=3)

        # Take absolute value and normalize
        laplacian = np.absolute(laplacian)
        laplacian = cv2.normalize(laplacian, None, 0, 255, cv2.NORM_MINMAX)

        # Convert back to PIL Image
        return Image.fromarray(laplacian.astype(np.uint8)).convert('RGBA')
    
    def apply_sepia(self, img):
        img_array = np.array(img.convert("RGB"))
        sepia_filter = np.array([[0.393, 0.769, 0.189],
                                 [0.349, 0.686, 0.168],
                                 [0.272, 0.534, 0.131]])
        sepia_img = img_array.dot(sepia_filter.T)
        sepia_img = np.clip(sepia_img, 0, 255).astype(np.uint8)
        return Image.fromarray(sepia_img, mode="RGB").convert("RGBA")

    def update_transform(self, transform_type, value):
        self.transform_values[transform_type] = float(value)
        self.apply_transforms()

    def apply_transforms(self):
        if self.original_image is None:
            return
        img = self.original_image.copy()
        width, height = img.size

        resize_factor = self.transform_values["resize"] / 100.0
        if resize_factor != 1.0:
            new_width = int(width * resize_factor)
            new_height = int(height * resize_factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        rotate_angle = self.transform_values["rotate"]
        if rotate_angle != 0:
            img = img.rotate(rotate_angle, expand=True, resample=Image.Resampling.BICUBIC)

        scale_x = self.transform_values["scale_x"] / 100.0
        scale_y = self.transform_values["scale_y"] / 100.0
        if scale_x != 1.0 or scale_y != 1.0:
            new_width = int(img.width * scale_x)
            new_height = int(img.height * scale_y)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        self.current_image = img
        self.update_image_preview()

    # =========================
    # INTERACTIVE TOOLS
    # =========================
    def interactive_crop(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded")
            return
        self.save_state()

        crop_window = tk.Toplevel(self)
        crop_window.title("Interactive Crop")
        crop_window.geometry("800x600")
        crop_window.configure(bg="#1b2230")

        crop_canvas = tk.Canvas(crop_window, bg="#273449", cursor="crosshair", highlightthickness=0)
        crop_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        display_img = self.current_image.copy()
        display_img.thumbnail((700, 500), Image.Resampling.LANCZOS)
        self._crop_preview_tk = ImageTk.PhotoImage(display_img)
        img_id = crop_canvas.create_image(0, 0, image=self._crop_preview_tk, anchor=tk.NW)

        def center_image(_=None):
            cw, ch = crop_canvas.winfo_width(), crop_canvas.winfo_height()
            x = (cw - display_img.width) // 2
            y = (ch - display_img.height) // 2
            crop_canvas.coords(img_id, x, y)

        crop_canvas.bind("<Configure>", center_image)
        center_image()

        self.crop_start = None
        self.crop_rect = None

        def start_crop(event):
            self.crop_start = (event.x, event.y)
            if self.crop_rect:
                crop_canvas.delete(self.crop_rect)
            self.crop_rect = crop_canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                                          outline="cyan", width=2, dash=(4, 4))

        def update_crop(event):
            if self.crop_rect and self.crop_start:
                crop_canvas.coords(self.crop_rect, self.crop_start[0], self.crop_start[1], event.x, event.y)

        def apply_crop(_):
            if not self.crop_rect or not self.crop_start:
                return
            x1, y1, x2, y2 = crop_canvas.coords(self.crop_rect)
            cw, ch = crop_canvas.winfo_width(), crop_canvas.winfo_height()
            off_x = (cw - display_img.width) // 2
            off_y = (ch - display_img.height) // 2
            sx = self.current_image.width / display_img.width
            sy = self.current_image.height / display_img.height

            rx1 = int(max(0, min(self.current_image.width, (min(x1, x2) - off_x) * sx)))
            ry1 = int(max(0, min(self.current_image.height, (min(y1, y2) - off_y) * sy)))
            rx2 = int(max(0, min(self.current_image.width, (max(x1, x2) - off_x) * sx)))
            ry2 = int(max(0, min(self.current_image.height, (max(y1, y2) - off_y) * sy)))

            if rx2 - rx1 > 10 and ry2 - ry1 > 10:
                self.current_image = self.current_image.crop((rx1, ry1, rx2, ry2))
                self.update_image_preview()
                crop_window.destroy()
                self._update_toolbar_state()
            else:
                messagebox.showwarning("Warning", "Please select a larger crop area")

        crop_canvas.bind("<ButtonPress-1>", start_crop)
        crop_canvas.bind("<B1-Motion>", update_crop)
        crop_canvas.bind("<ButtonRelease-1>", apply_crop)

        ttk.Label(crop_window, text="Click & drag to select, release to crop", style="TLabel").pack(pady=5)

    def interactive_draw(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded")
            return
        self.save_state()

        draw_window = tk.Toplevel(self)
        draw_window.title("Interactive Drawing & Annotation")
        draw_window.geometry("900x700")
        draw_window.configure(bg="#1b2230")

        working_img = self.current_image.convert("RGBA").copy()
        preview_img = working_img.copy()
        preview_img.thumbnail((800, 600), Image.Resampling.LANCZOS)
        self.draw_preview_img = preview_img
        self.draw_preview_tk = ImageTk.PhotoImage(preview_img)

        canvas = tk.Canvas(draw_window, bg="#273449", cursor="crosshair", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        canvas.create_image(450, 350, image=self.draw_preview_tk, anchor=tk.CENTER)

        toolbar = ttk.Frame(draw_window)
        toolbar.pack(fill=tk.X, pady=5)

        self.drawing_tool = tk.StringVar(value="freehand")
        self.draw_color = "#ff0000"
        self.brush_size = tk.IntVar(value=3)
        self.text_to_add = tk.StringVar(value="Sample Text")
        self.text_size = tk.IntVar(value=36)

        for tool in ["freehand", "line", "rectangle", "circle", "text", "fill"]:
            ttk.Radiobutton(toolbar, text=tool.title(), variable=self.drawing_tool, value=tool).pack(side=tk.LEFT, padx=4)

        ttk.Label(toolbar, text="Brush:").pack(side=tk.LEFT, padx=(8, 0))
        ttk.Spinbox(toolbar, from_=1, to=50, textvariable=self.brush_size, width=4).pack(side=tk.LEFT, padx=4)

        color_swatch = tk.Canvas(toolbar, width=28, height=18, highlightthickness=1)
        color_swatch.create_rectangle(0, 0, 28, 18, fill=self.draw_color, outline="black")
        color_swatch.pack(side=tk.LEFT, padx=(8, 4))
        ttk.Button(toolbar, text="Color", style="Accent.TButton",
                   command=lambda: self.pick_color(draw_window, color_swatch)).pack(side=tk.LEFT)

        ttk.Entry(toolbar, textvariable=self.text_to_add, width=20).pack(side=tk.LEFT, padx=6)
        ttk.Label(toolbar, text="Text size:").pack(side=tk.LEFT, padx=(6, 0))
        ttk.Spinbox(toolbar, from_=8, to=200, textvariable=self.text_size, width=5).pack(side=tk.LEFT, padx=4)

        ttk.Button(toolbar, text="Apply", style="Accent.TButton",
                   command=lambda: self._apply_direct_drawing(working_img, draw_window)
                   ).pack(side=tk.RIGHT, padx=6)
        ttk.Button(toolbar, text="Cancel", style="Accent.TButton", command=draw_window.destroy).pack(side=tk.RIGHT)

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
            offset_x = (canvas.winfo_width() - preview_img.width) // 2
            offset_y = (canvas.winfo_height() - preview_img.height) // 2
            return int((x - offset_x) * scale_x), int((y - offset_y) * scale_y)

        def refresh_preview_debounced():
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

            canvas.after(50, _update)

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
                    self._temp_shape = canvas.create_rectangle(self.last_point[0], self.last_point[1],
                                                               e.x, e.y, outline=self.draw_color,
                                                               width=self.brush_size.get())
                elif tool == "circle":
                    self._temp_shape = canvas.create_oval(self.last_point[0], self.last_point[1],
                                                          e.x, e.y, outline=self.draw_color,
                                                          width=self.brush_size.get())
                elif tool == "line":
                    self._temp_shape = canvas.create_line(self.last_point[0], self.last_point[1],
                                                          e.x, e.y, fill=self.draw_color,
                                                          width=self.brush_size.get())

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
        from tkinter import colorchooser
        color = colorchooser.askcolor(title="Choose Color", parent=parent)
        if color and color[1]:
            self.draw_color = color[1]
            if swatch_widget is not None:
                swatch_widget.delete("all")
                swatch_widget.create_rectangle(0, 0, 28, 18, fill=self.draw_color, outline="black")

    def _get_font(self, size):
        candidates = ["arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
        for f in candidates:
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                continue
        return ImageFont.load_default()

    def _apply_direct_drawing(self, working_img, window):
        if hasattr(self, "_draw_layer"):
            merged = Image.alpha_composite(working_img.convert("RGBA"), self._draw_layer.convert("RGBA"))
            self.current_image = merged
            self.update_image_preview()
            self.save_state()
            self._update_toolbar_state()
            window.destroy()

    def _bucket_fill(self, img, x, y, color):
        pixels = np.array(img)  # (h, w, 4)
        h, w = pixels.shape[:2]
        if not (0 <= x < w and 0 <= y < h):
            return
        target = pixels[y, x].copy()
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
        if self.current_image is None:
            return
        self.save_state()
        if direction == "horizontal":
            self.current_image = ImageOps.mirror(self.current_image)
        elif direction == "vertical":
            self.current_image = ImageOps.flip(self.current_image)
        self.update_image_preview()
        self._update_toolbar_state()

    def _adjust_preview(self, value=None):
        if self.current_image is None:
            return
        img = self.apply_all_adjustments()
        self.update_image_preview(img)

    def update_image_preview(self, img=None):
        if img is None:
            img = self.current_image
        if img is None:
            return
        try:
            max_display_width = max(100, self.center_frame.winfo_width() - 40)
            max_display_height = max(100, self.center_frame.winfo_height() - 40)
        except Exception:
            max_display_width = 800
            max_display_height = 600

        display_img = img.copy()
        display_img.thumbnail((max_display_width, max_display_height), Image.Resampling.LANCZOS)
        self.preview_image_tk = ImageTk.PhotoImage(display_img)
        self.image_label.configure(image=self.preview_image_tk)

        self._update_histogram(img)

    def reset_image(self):
        if self.original_image is not None:
            self.current_image = self.original_image.copy()
            self.reset_all_sliders()
            self.update_image_preview()
            self._update_toolbar_state()

    def reset_all_sliders(self):
        self.transform_values = {"resize": 100, "rotate": 0, "scale_x": 100, "scale_y": 100}
        for key, (slider, entry, var, default) in self.slider_widgets.items():
            var.set(default)
            try:
                entry.delete(0, tk.END)
                entry.insert(0, str(default))
            except Exception:
                pass
        for var in [
            self.exposure_var, self.highlights_var, self.shadows_var, self.contrast_var,
            self.brightness_var, self.blacks_var, self.whites_var, self.hue_var, self.tint_var,
            self.saturation_var, self.temperature_var, self.vibrance_var, self.blur_var,
            self.noise_var, self.vignette_var
        ]:
            var.set(0)
        for k in self.perspective_values:
            self.perspective_values[k] = 0.0

    # =========================
    # FREQUENCY DOMAIN
    # =========================
    def _apply_fft(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded!")
            return
        
        confirm = messagebox.askyesno("Apply Filter", f"Are you sure you want to apply 'fourier transform'?")
        if not confirm:
            return
        
        img_gray = self.current_image.convert("L")
        arr = np.array(img_gray)
        f = np.fft.fft2(arr)
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1)
        mag_img = Image.fromarray(np.uint8(magnitude_spectrum / np.max(magnitude_spectrum) * 255))
        self.current_image = mag_img.convert("RGBA")
        self.update_image_preview(self.current_image)
        self._update_toolbar_state()

    def _apply_ifft(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded!")
            return
        
        confirm = messagebox.askyesno("Apply Filter", f"Are you sure you want to apply 'inverse fourier transform'?")
        if not confirm:
            return
        img_gray = self.current_image.convert("L")
        arr = np.array(img_gray)
        f = np.fft.fft2(arr)
        fshift = np.fft.fftshift(f)
        ishift = np.fft.ifftshift(fshift)
        img_back = np.fft.ifft2(ishift)
        img_back = np.abs(img_back)
        result = Image.fromarray(np.uint8(img_back))
        self.current_image = result.convert("RGBA")
        self.update_image_preview(self.current_image)
        self._update_toolbar_state()

    def _apply_high_pass(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded!")
            return

        confirm = messagebox.askyesno("Apply Filter", f"Are you sure you want to apply 'High Pass'?")
        if not confirm:
            return
        
        img_gray = self.current_image.convert("L")
        arr = np.array(img_gray)
        h, w = arr.shape
        f = np.fft.fft2(arr)
        fshift = np.fft.fftshift(f)

        mask = np.ones((h, w), np.uint8)
        r = max(1, min(h, w) // 20)
        crow, ccol = h // 2, w // 2
        mask[crow - r:crow + r, ccol - r:ccol + r] = 0

        fshift = fshift * mask
        img_back = np.fft.ifft2(np.fft.ifftshift(fshift))
        img_back = np.abs(img_back)
        result = Image.fromarray(np.uint8(np.clip(img_back, 0, 255)))
        self.save_state()
        self.current_image = result.convert("RGBA")
        self.update_image_preview(self.current_image)
        self._update_toolbar_state()

    def _apply_low_pass(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded!")
            return

        confirm = messagebox.askyesno("Apply Filter", f"Are you sure you want to apply 'low pass'?")
        if not confirm:
            return
        img_gray = self.current_image.convert("L")
        arr = np.array(img_gray)
        h, w = arr.shape
        f = np.fft.fft2(arr)
        fshift = np.fft.fftshift(f)

        mask = np.zeros((h, w), np.uint8)
        r = max(1, min(h, w) // 20)
        crow, ccol = h // 2, w // 2
        mask[crow - r:crow + r, ccol - r:ccol + r] = 1

        fshift = fshift * mask
        img_back = np.fft.ifft2(np.fft.ifftshift(fshift))
        img_back = np.abs(img_back)
        result = Image.fromarray(np.uint8(np.clip(img_back, 0, 255)))
        self.current_image = result.convert("RGBA")
        self.save_state()
        self.update_image_preview(self.current_image)
        self._update_toolbar_state()

    # =========================
    # SLIDER HELPER
    # =========================
    def _add_slider_with_entry(self, parent, label, key, min_val, max_val, default, command):
        """Bikin baris kontrol: Label + Slider + Entry, sinkron + debounce."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=6)
        ttk.Label(frame, text=label).pack(anchor="w")

        key_to_var = {
            "exposure": self.exposure_var,
            "highlights": self.highlights_var,
            "shadows": self.shadows_var,
            "contrast": self.contrast_var,
            "brightness": self.brightness_var,
            "blacks": self.blacks_var,
            "whites": self.whites_var,
            "hue": self.hue_var,
            "tint": self.tint_var,
            "saturation": self.saturation_var,
            "temperature": self.temperature_var,
            "vibrance": self.vibrance_var,
            "blur": self.blur_var,
            "noise": self.noise_var,
            "vignette": self.vignette_var,
            "resize": tk.DoubleVar(value=self.transform_values["resize"]),
            "rotate": tk.DoubleVar(value=self.transform_values["rotate"]),
            "scale_x": tk.DoubleVar(value=self.transform_values["scale_x"]),
            "scale_y": tk.DoubleVar(value=self.transform_values["scale_y"]),
        }
        var = key_to_var.get(key, tk.DoubleVar(value=default))

        row = ttk.Frame(frame)
        row.pack(fill=tk.X)
        slider = ttk.Scale(row, from_=min_val, to=max_val, orient=tk.HORIZONTAL, variable=var)
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        entry = ttk.Entry(row, width=6)
        entry.pack(side=tk.RIGHT, padx=6)
        try:
            entry.insert(0, f"{float(var.get()):.0f}")
        except Exception:
            entry.insert(0, str(default))

        def _schedule():
            if not callable(command):
                return
            aid = self._debounce_after_ids.get(key)
            if aid:
                try:
                    self.after_cancel(aid)
                except Exception:
                    pass
            self._debounce_after_ids[key] = self.after(120, lambda: command(var.get()))

        def _on_var_change(*_):
            try:
                v = float(var.get())
            except Exception:
                v = default
            v = max(min(v, max_val), min_val)
            entry.delete(0, tk.END)
            entry.insert(0, f"{int(v) if float(v).is_integer() else v}")

        var.trace_add("write", _on_var_change)

        def _commit_from_entry(_=None):
            try:
                v = float(entry.get())
            except Exception:
                v = default
            v = max(min(v, max_val), min_val)
            if var.get() != v:
                var.set(v)
            _schedule()

        entry.bind("<Return>", _commit_from_entry)
        entry.bind("<FocusOut>", _commit_from_entry)
        slider.bind("<ButtonRelease-1>", lambda e: _schedule())
        slider.bind("<KeyRelease>", lambda e: _schedule())

        self.slider_widgets[key] = (slider, entry, var, default)
        return var

    # =========================
    # ENHANCEMENT
    # =========================

    def _sharpen_image(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded!")
            return

        confirm = messagebox.askyesno("Apply Filter", f"Are you sure you want to apply 'sharpen'?")
        if not confirm:
            return
        
        img_sharp = self.current_image.filter(ImageFilter.SHARPEN)
        self.current_image = img_sharp.convert("RGBA")
        self.save_state()
        self.update_image_preview(self.current_image)
        self._update_toolbar_state()

    def _denoise_image(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded!")
            return
        confirm = messagebox.askyesno("Apply Filter", f"Are you sure you want to apply 'denoise'?")
        if not confirm:
            return
        img_denoised = self.current_image.filter(ImageFilter.GaussianBlur(radius=1.5))
        self.current_image = img_denoised.convert("RGBA")
        self.save_state()
        self.update_image_preview(self.current_image)
        self._update_toolbar_state()

    def _boost_detail(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image loaded!")
            return
        confirm = messagebox.askyesno("Apply Filter", f"Are you sure you want to apply 'boost detail'?")
        if not confirm:
            return
        
        img_detail = self.current_image.filter(ImageFilter.DETAIL)
        self.current_image = img_detail.convert("RGBA")
        self.save_state()
        self.update_image_preview(self.current_image)
        self._update_toolbar_state()

    # =========================
    # OVERLAY (global method)
    # =========================
    def _with_overlay(self, fn, *args, title="Processing..."):
        try:
            self._show_loading_overlay(title)
            self.update_idletasks()
            return fn(*args)
        finally:
            self._hide_loading_overlay()

    def _show_loading_overlay(self, text="Processing..."):
        if self._overlay is not None:
            return
        self._overlay = tk.Toplevel(self)
        self._overlay.transient(self)
        self._overlay.grab_set()
        self._overlay.overrideredirect(True)
        self._overlay.configure(bg="#0f1a24")

        self.update_idletasks()
        w, h = 320, 140
        x = self.winfo_rootx() + (self.winfo_width() - w) // 2
        y = self.winfo_rooty() + (self.winfo_height() - h) // 2
        self._overlay.geometry(f"{w}x{h}+{x}+{y}")

        inner = tk.Frame(self._overlay, bg="#122235", highlightthickness=3, highlightbackground="#2ca7a4")
        inner.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.8)

        ttk.Label(inner, text=text, style="Header.TLabel").pack(pady=(18, 10))
        pb = ttk.Progressbar(inner, mode="indeterminate", length=220)
        pb.pack(pady=(6, 10))
        pb.start(12)

        border_colors = ["#2ca7a4", "#4c86a8", "#5661b3"]
        idx = {"i": 0}

        def pulse():
            if not self._overlay:
                return
            inner.config(highlightbackground=border_colors[idx["i"] % len(border_colors)])
            idx["i"] += 1
            self.after(250, pulse)
        pulse()
        self._overlay.update()

    def _hide_loading_overlay(self):
        if self._overlay is not None:
            try:
                self._overlay.grab_release()
            except Exception:
                pass
            self._overlay.destroy()
            self._overlay = None

    # =========================
    # CANVAS BUTTON
    # =========================
    def _create_rounded_button(self, parent, text, command=None):
    # Smaller width and height
        canvas = tk.Canvas(parent, width=100, height=26, bg="#0e1117",
                           bd=0, highlightthickness=0, relief="flat")

        base_color = "#4b5563"
        hover_color = "#64748b"
        active_color = "#374151"
        disabled_color = "#2b2f3a"
        text_color = "white"
        canvas._enabled = True

        def draw_rounded_rect(cnv, x1, y1, x2, y2, r, color):
            cnv.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, fill=color, outline=color)
            cnv.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, fill=color, outline=color)
            cnv.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, fill=color, outline=color)
            cnv.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, fill=color, outline=color)
            cnv.create_rectangle(x1 + r, y1, x2 - r, y2, fill=color, outline=color)
            cnv.create_rectangle(x1, y1 + r, x2, y2 - r, fill=color, outline=color)

        def paint(color):
            canvas.delete("all")
            # smaller rounded area
            draw_rounded_rect(canvas, 2, 2, 98, 24, 8, color)
            canvas.create_text(50, 13, text=text, fill=text_color, font=("Inter", 6, "bold"))

        def on_enter(_):
            if canvas._enabled:
                paint(hover_color)

        def on_leave(_):
            paint(base_color if canvas._enabled else disabled_color)

        def on_press(_):
            if canvas._enabled:
                paint(active_color)

        def on_release(_):
            if canvas._enabled:
                paint(hover_color)
                if command:
                    command()

        def set_enabled(enabled: bool):
            canvas._enabled = bool(enabled)
            paint(base_color if canvas._enabled else disabled_color)

        canvas.set_enabled = set_enabled
        paint(base_color)

        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<ButtonRelease-1>", on_release)

        return canvas



    # =========================
    # MAIN LOOP
    # =========================
    def run(self):
        self.mainloop()


if __name__ == "__main__":
    app = AdvancedImageProcessor()
    app.run()
