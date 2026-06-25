from PIL import Image
import os
from typing import Callable


class ImageService:

    @staticmethod
    def images_to_pdf(
        image_paths: list[str],
        output_path: str,
        progress_cb: Callable[[int], None] = None
    ) -> None:
        if not image_paths:
            raise ValueError("At least one image is required.")

        total = len(image_paths)
        pil_images: list[Image.Image] = []

        for i, path in enumerate(image_paths):
            if not os.path.isfile(path):
                raise RuntimeError(f"File not found: {path}")

            img = Image.open(path)

            # Composite transparent images onto white before converting to RGB
            # (naive .convert("RGB") turns transparent pixels black)
            if img.mode in ("RGBA", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                alpha = img.split()[-1]
                background.paste(img.convert("RGBA"), mask=alpha)
                img = background
            elif img.mode == "P":
                img = img.convert("RGBA")
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            pil_images.append(img)

            if progress_cb:
                progress_cb(int((i + 1) / total * 80))

        if len(pil_images) == 1:
            pil_images[0].save(output_path, "PDF", resolution=150)
        else:
            pil_images[0].save(
                output_path,
                "PDF",
                resolution=150,
                save_all=True,
                append_images=pil_images[1:]
            )

        if progress_cb:
            progress_cb(100)
