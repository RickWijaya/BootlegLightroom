import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageFilter, ImageOps, ImageEnhance
import numpy as np
# Cara Edit
# 1. UI
# UI hanya bisa ditambahkan di def _build_ui(self):
# 2. Fungsi bisa ditambahkan di manapun selain build ui
# -- Ricky Wijaya

class SimpleImageProcessor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bootleg Lightroom (Tkinter Edition)")
        self.geometry("1100x700")
        self.minsize(800, 500)

        # Image state
        self.original_image = None
        self.current_image = None
        self.preview_image_tk = None

        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Left image area
        self.left_frame = ttk.Frame(container)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.image_label = ttk.Label(self.left_frame, anchor=tk.CENTER)
        self.image_label.pack(fill=tk.BOTH, expand=True)

        self.status = ttk.Label(self.left_frame, text="No image loaded", anchor=tk.W)
        self.status.pack(fill=tk.X, pady=(4, 0))

        # Right controls
        self.right_frame = ttk.Frame(container, width=300)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))

        # File section
        file_frame = ttk.LabelFrame(self.right_frame, text="File")
        file_frame.pack(fill=tk.X, pady=6)
        ttk.Button(file_frame, text="Open", command=self.open_image).pack(side=tk.LEFT, padx=4, pady=6)
        ttk.Button(file_frame, text="Save As...", command=self.save_image).pack(side=tk.LEFT, padx=4, pady=6)
        ttk.Button(file_frame, text="Reset", command=self.reset_image).pack(side=tk.LEFT, padx=4, pady=6)

        # Adjustments (Lightroom-style sliders)
        adjust_frame = ttk.LabelFrame(self.right_frame, text="Adjustments")
        adjust_frame.pack(fill=tk.X, pady=6)

        self._add_slider(adjust_frame, "Brightness", 0.2, 2.0, 1.0, 'brightness')
        self._add_slider(adjust_frame, "Contrast", 0.2, 2.0, 1.0, 'contrast')
        self._add_slider(adjust_frame, "Sharpness", 0.0, 3.0, 1.0, 'sharpness')
        self._add_slider(adjust_frame, "Blur", 0.0, 10.0, 0.0, 'blur')
        self._add_slider(adjust_frame, "Noise", 0.0, 100.0, 0.0, 'noise')

        # Transforms
        trans_frame = ttk.LabelFrame(self.right_frame, text="Transform")
        trans_frame.pack(fill=tk.X, pady=6)
        ttk.Button(trans_frame, text="Rotate 90°", command=lambda: self.transform('rotate')).pack(fill=tk.X, pady=3)
        ttk.Button(trans_frame, text="Flip Horizontal", command=lambda: self.transform('flip_h')).pack(fill=tk.X, pady=3)
        ttk.Button(trans_frame, text="Flip Vertical", command=lambda: self.transform('flip_v')).pack(fill=tk.X, pady=3)

        # Filters
        filter_frame = ttk.LabelFrame(self.right_frame, text="One-click Filters")
        filter_frame.pack(fill=tk.X, pady=6)
        ttk.Button(filter_frame, text="Grayscale", command=self.confirm_grayscale).pack(fill=tk.X, pady=3)
        ttk.Button(filter_frame, text="Emboss", command=self.confirm_emboss).pack(fill=tk.X, pady=3)
        ttk.Button(filter_frame, text="Edge Detect", command=self.confirm_edge).pack(fill=tk.X, pady=3) 
        self.left_frame.bind('<Configure>', self._on_left_frame_resize)

        # ------------------ Confirmation wrappers ------------------
    def confirm_grayscale(self):
        if self.current_image is None:
            return
        result = messagebox.askyesno(
            "Confirm Grayscale",
            "This change can't be undone. Do you want to continue?"
        )
        if result:
            self.apply_filter("grayscale")

    def confirm_edge(self):
        if self.current_image is None:
            return
        result = messagebox.askyesno(
            "Confirm Edge Detect",
            "This change can't be undone. Do you want to continue?"
        )
        if result:
            self.apply_filter("edge")

    def confirm_emboss(self):
        if self.current_image is None:
            return
        result = messagebox.askyesno(
            "Confirm Emboss",
            "This change can't be undone. Do you want to continue?"
        )
        if result:
            self.apply_filter("emboss")

    def _add_slider(self, parent, label, min_val, max_val, default, attr):
        ttk.Label(parent, text=label).pack(anchor=tk.W, padx=6)
        var = tk.DoubleVar(value=default)
        slider = ttk.Scale(parent, from_=min_val, to=max_val, orient=tk.HORIZONTAL,
                           variable=var, command=self._adjust_preview)
        slider.pack(fill=tk.X, padx=6, pady=2)
        setattr(self, f"{attr}_var", var)

    # ------------------ File Ops ------------------
    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
        if not path:
            return
        try:
            img = Image.open(path).convert('RGBA')
        except Exception as e:
            messagebox.showerror("Open error", f"Unable to open image:\n{e}")
            return
        self.original_image = img
        self.current_image = img.copy()
        self._reset_sliders()
        self.update_image_preview()
        self.status.config(text=f"Loaded: {os.path.basename(path)} ({img.width}x{img.height})")

    def save_image(self):
        if self.current_image is None:
            messagebox.showinfo("No image", "Nothing to save.")
            return
        path = filedialog.asksaveasfilename(defaultextension='.png',
                                            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg;*.jpeg")])
        if not path:
            return
        img = self.apply_all_effects()
        if path.lower().endswith(('.jpg', '.jpeg')):
            img = img.convert('RGB')
        img.save(path)
        messagebox.showinfo("Saved", f"Image saved to:\n{path}")

    def reset_image(self):
        if self.original_image is None:
            return
        self.current_image = self.original_image.copy()
        self._reset_sliders()
        self.update_image_preview()
        self.status.config(text="Reset to original")

    def _reset_sliders(self):
        self.brightness_var.set(1.0)
        self.contrast_var.set(1.0)
        self.sharpness_var.set(1.0)
        self.blur_var.set(0.0)
        self.noise_var.set(0.0)

    # ------------------ Processing ------------------
    def apply_all_effects(self):
        img = self.current_image.copy()

        # Brightness
        b = float(self.brightness_var.get())
        if b != 1.0:
            img = ImageEnhance.Brightness(img).enhance(b)

        # Contrast
        c = float(self.contrast_var.get())
        if c != 1.0:
            img = ImageEnhance.Contrast(img).enhance(c)

        # Sharpness
        s = float(self.sharpness_var.get())
        if s != 1.0:
            img = ImageEnhance.Sharpness(img).enhance(s)

        # Blur
        blur = float(self.blur_var.get())
        if blur > 0.0:
            img = img.filter(ImageFilter.GaussianBlur(radius=blur))

        # Noise
        noise = float(self.noise_var.get())
        if noise > 0.0:
            img = self.add_noise(img, noise)

        return img

    def add_noise(self, img, amount):
        arr = np.array(img)
        noise = np.random.normal(0, amount, arr.shape).astype(np.int16)
        noisy = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy, mode=img.mode)

    def update_image_preview(self):
        if self.current_image is None:
            self.image_label.config(image='')
            return

        img = self.apply_all_effects()

        max_w = max(200, self.left_frame.winfo_width() - 10)
        max_h = max(200, self.left_frame.winfo_height() - 40)
        img_for_display = self._fit_image(img, max_w, max_h)

        self.preview_image_tk = ImageTk.PhotoImage(img_for_display)
        self.image_label.config(image=self.preview_image_tk)

    def _fit_image(self, img, max_w, max_h):
        w, h = img.size
        ratio = min(max_w / w, max_h / h, 1.0)
        return img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    def _on_left_frame_resize(self, event):
        self.update_image_preview()

    def apply_filter(self, filter_name):
        if self.current_image is None:
            return
        img = self.current_image
        if filter_name == 'grayscale':
            img = ImageOps.grayscale(img).convert('RGBA')
        elif filter_name == 'emboss':
            img = img.filter(ImageFilter.EMBOSS)
        elif filter_name == 'edge':
            edge = img.convert('L').filter(ImageFilter.FIND_EDGES)
            img = Image.merge('RGBA', (edge, edge, edge, Image.new('L', edge.size, 255)))
        self.current_image = img
        self.update_image_preview()

    def transform(self, op):
        if self.current_image is None:
            return
        img = self.current_image
        if op == 'rotate':
            img = img.rotate(-90, expand=True)
        elif op == 'flip_h':
            img = ImageOps.mirror(img)
        elif op == 'flip_v':
            img = ImageOps.flip(img)
        self.current_image = img
        self.update_image_preview()

    def _adjust_preview(self, _=None):
        self.update_image_preview()


if __name__ == '__main__':
    app = SimpleImageProcessor()
    app.mainloop()
