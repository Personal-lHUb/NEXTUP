"""Preparazione dell'immagine di copertina fornita dall'autore.

KDP stampa a 300 DPI: un'immagine che sullo schermo sembra ottima può risultare
sgranata sul cartaceo. Qui l'immagine viene misurata, ritagliata sulle
proporzioni esatte della prima di copertina (abbondanza inclusa), portata alla
risoluzione di stampa e ripulita.

Nessun miracolo: se i pixel non ci sono, ingrandire non li inventa. In quel caso
il rapporto lo dice e il controllo qualità lo segnala.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from . import kdpspecs

PRINT_DPI = 300
MIN_ACCEPTABLE_DPI = 200  # sotto questa soglia la stampa si vede sgranata

#: Velatura scura in alto e in basso: senza, titolo e nome dell'autore
#: diventano illeggibili appena la foto ha una zona chiara.
SCRIM_TOP = (0.46, 0.78)     # (quota dell'altezza, opacità massima)
SCRIM_BOTTOM = (0.34, 0.82)


@dataclass
class ImageReport:
    """Che cosa è stato fatto all'immagine, in modo verificabile."""

    source: str
    prepared: str
    source_px: tuple[int, int]
    prepared_px: tuple[int, int]
    target_in: tuple[float, float]
    effective_dpi: int
    upscaled: bool
    enhanced: bool
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)

    def describe(self) -> str:
        lines = [
            f"  origine   : {self.source} ({self.source_px[0]}x{self.source_px[1]} px)",
            f"  preparata : {self.prepared_px[0]}x{self.prepared_px[1]} px "
            f"per {self.target_in[0]:.2f}x{self.target_in[1]:.2f} pollici",
            f"  risoluzione effettiva: {self.effective_dpi} DPI"
            + ("  (ingrandita)" if self.upscaled else ""),
        ]
        lines += [f"  ! {w}" for w in self.warnings]
        return "\n".join(lines)


def _apply_scrim(image, top=SCRIM_TOP, bottom=SCRIM_BOTTOM):
    """Sfuma il nero dai bordi verso il centro, pixel per pixel.

    Fatta con rettangoli sovrapposti nel PDF si vedrebbero le bande: qui la
    sfumatura è continua e finisce dentro il JPEG, così quello che si vede in
    anteprima è esattamente quello che va in stampa.
    """
    from PIL import Image

    width, height = image.size
    top_share, top_strength = top
    bottom_share, bottom_strength = bottom

    column = Image.new("L", (1, height))
    pixels = column.load()
    top_band = max(int(height * top_share), 1)
    bottom_band = max(int(height * bottom_share), 1)
    for y in range(height):
        alpha = 0.0
        if y < top_band:
            alpha = top_strength * (1 - y / top_band) ** 1.6
        distance_from_bottom = height - 1 - y
        if distance_from_bottom < bottom_band:
            alpha = max(
                alpha, bottom_strength * (1 - distance_from_bottom / bottom_band) ** 1.6
            )
        pixels[0, y] = int(round(alpha * 255))

    mask = column.resize((width, height))
    return Image.composite(Image.new("RGB", (width, height), (0, 0, 0)), image, mask)


def front_panel_size_in(trim: str) -> tuple[float, float]:
    """Area coperta dall'immagine: prima di copertina più abbondanza."""
    width, height = kdpspecs.trim_size_in(trim)
    return (width + kdpspecs.BLEED_IN, height + kdpspecs.COVER_BLEED_TOTAL)


def prepare(
    source: Path,
    output: Path,
    trim: str,
    *,
    enhance: bool = True,
    scrim: bool = True,
    dpi: int = PRINT_DPI,
) -> ImageReport:
    """Ritaglia, ridimensiona e ripulisce l'immagine per la prima di copertina."""
    try:
        from PIL import Image, ImageEnhance, ImageOps
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Serve Pillow per usare un'immagine di copertina: pip install pillow"
        ) from exc

    target_w_in, target_h_in = front_panel_size_in(trim)
    target_w = round(target_w_in * dpi)
    target_h = round(target_h_in * dpi)
    warnings: list[str] = []

    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image)  # raddrizza le foto da telefono
        source_px = image.size
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        elif image.mode == "L":
            image = image.convert("RGB")
            warnings.append("L'immagine era in scala di grigi: convertita in RGB.")

        effective_dpi = int(min(source_px[0] / target_w_in, source_px[1] / target_h_in))
        upscaled = source_px[0] < target_w or source_px[1] < target_h

        # Ritaglio centrale sulle proporzioni della copertina, poi scala.
        prepared = ImageOps.fit(
            image, (target_w, target_h), method=Image.LANCZOS, centering=(0.5, 0.42)
        )

        if enhance:
            prepared = ImageOps.autocontrast(prepared, cutoff=0.5)
            prepared = ImageEnhance.Color(prepared).enhance(1.06)
            prepared = ImageEnhance.Contrast(prepared).enhance(1.04)
            # Una passata leggera di nitidezza: di più si vedrebbe in stampa.
            prepared = ImageEnhance.Sharpness(prepared).enhance(1.25 if upscaled else 1.1)

        if scrim:
            prepared = _apply_scrim(prepared)

        output.parent.mkdir(parents=True, exist_ok=True)
        prepared.save(output, format="JPEG", quality=95, dpi=(dpi, dpi), subsampling=0)
        prepared_px = prepared.size

    if effective_dpi < MIN_ACCEPTABLE_DPI:
        warnings.append(
            f"Risoluzione insufficiente per la stampa: {effective_dpi} DPI reali contro i "
            f"{dpi} richiesti. Serve un'immagine di almeno {target_w}x{target_h} px."
        )
    elif effective_dpi < dpi:
        warnings.append(
            f"Risoluzione sotto i {dpi} DPI ({effective_dpi} reali): stampabile, ma i "
            "dettagli fini si ammorbidiscono."
        )

    ratio_source = source_px[0] / source_px[1]
    ratio_target = target_w / target_h
    if abs(ratio_source - ratio_target) / ratio_target > 0.25:
        warnings.append(
            "Le proporzioni dell'originale sono molto diverse da quelle della copertina: "
            "il ritaglio centrale può aver tagliato parti importanti."
        )

    return ImageReport(
        source=str(source),
        prepared=str(output),
        source_px=source_px,
        prepared_px=prepared_px,
        target_in=(round(target_w_in, 3), round(target_h_in, 3)),
        effective_dpi=effective_dpi,
        upscaled=upscaled,
        enhanced=enhance,
        warnings=warnings,
    )
