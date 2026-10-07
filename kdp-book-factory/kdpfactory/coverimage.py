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
#: Quanto si può scurire in più la zona del titolo, a passi, finché il titolo
#: bianco non stacca: oltre, l'immagine sotto non si vede più e la copertina
#: va ripensata, non velata.
ZONE_SCRIM_STEPS = (0.0, 0.15, 0.3, 0.45, 0.6)
#: Il contrasto si misura contro i pixel più chiari della zona, non contro la
#: media: una lettera bianca si perde dove l'immagine è chiara, non in media.
ZONE_PERCENTILE = 0.9
#: Quanto dettaglio fine può avere l'immagine dietro il titolo: è lo scarto
#: medio fra l'immagine e la sua versione sfocata, in frazione della scala.
#: Oltre, lo sfondo è «rumoroso» e le scritte non si distinguono (video A, 12:42).
MAX_ZONE_NOISE = 0.08
#: Oltre questa quota di pixel giallo-ocra spenti, l'immagine ha la «classica
#: trama gialla senapina» delle immagini generate (video B, 2:24).
MAX_MUSTARD = 0.4


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
    #: composizione per cui è stata preparata (velature diverse)
    layout: str = "alto"
    #: contrasto del titolo bianco contro la zona che ha dietro, dopo la velatura
    title_contrast: float = 0.0
    #: dettaglio fine nella zona del titolo (0 = piatta)
    title_noise: float = 0.0
    #: velatura aggiunta alla zona del titolo per farlo staccare
    title_scrim: float = 0.0
    #: quota dell'immagine con la dominante giallo-senape
    mustard: float = 0.0

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
        if self.title_contrast:
            lines.append(
                f"  titolo sull'immagine: contrasto {self.title_contrast:.1f}:1, dettaglio "
                f"{self.title_noise:.3f}" + (f", velatura +{self.title_scrim:.0%}"
                                            if self.title_scrim else "")
            )
        lines += [f"  ! {w}" for w in self.warnings]
        return "\n".join(lines)


def title_zone(box, front_x0: float, front_width: float, height: float, pad: float = 0.025):
    """Il rettangolo del blocco del titolo in frazioni dell'immagine, origine in alto a sinistra.

    `box` è in punti sulla pagina, con l'origine in basso (x0, y0, x1, y1);
    l'immagine copre la prima con la sua abbondanza, da `front_x0` per
    `front_width` e per tutta l'altezza.
    """
    x0, y0, x1, y1 = box
    fx0 = (x0 - front_x0) / front_width - pad
    fx1 = (x1 - front_x0) / front_width + pad
    fy0 = 1 - y1 / height - pad
    fy1 = 1 - y0 / height + pad
    return (max(fx0, 0.0), max(fy0, 0.0), min(fx1, 1.0), min(fy1, 1.0))


def _linear(value: int) -> float:
    value /= 255.0
    return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4


_LINEAR = [_linear(v) for v in range(256)]


def _pixels(image) -> list:
    """I pixel in fila, con l'accessorio che questa versione di Pillow preferisce."""
    leggi = getattr(image, "get_flattened_data", None) or image.getdata
    return list(leggi())


def _crop(image, zone):
    width, height = image.size
    return image.crop((int(zone[0] * width), int(zone[1] * height),
                       max(int(zone[2] * width), int(zone[0] * width) + 1),
                       max(int(zone[3] * height), int(zone[1] * height) + 1)))


#: In quante fasce orizzontali si divide la zona per misurarla: ogni riga di
#: testo ha la sua, e una macchia chiara dietro il gancio non si annacqua nella
#: media di tutto il blocco.
ZONE_STRIPS = 8


def zone_contrast(image, zone) -> float:
    """Contrasto del bianco contro i pixel chiari della zona, nella fascia peggiore.

    In ogni fascia si prende il 90° percentile della luminanza (i pixel chiari,
    dove una lettera bianca si perde), e vale la fascia più chiara.
    """
    area = _crop(image, zone).convert("RGB")
    area.thumbnail((240, 240))
    width, height = area.size
    pixels = _pixels(area)
    peggiore = 21.0
    fascia = max(height // ZONE_STRIPS, 1)
    for top in range(0, height, fascia):
        luminanze = sorted(
            0.2126 * _LINEAR[r] + 0.7152 * _LINEAR[g] + 0.0722 * _LINEAR[b]
            for r, g, b in pixels[top * width:min(top + fascia, height) * width]
        )
        if not luminanze:
            continue
        chiara = luminanze[min(int(len(luminanze) * ZONE_PERCENTILE), len(luminanze) - 1)]
        peggiore = min(peggiore, 1.05 / (chiara + 0.05))
    return peggiore


def zone_noise(image, zone) -> float:
    """Quanto dettaglio fine c'è nella zona: scarto medio dalla sua versione sfocata."""
    from PIL import ImageChops, ImageFilter, ImageStat

    area = _crop(image, zone).convert("L")
    area.thumbnail((400, 400))
    sfocata = area.filter(ImageFilter.GaussianBlur(3))
    return ImageStat.Stat(ImageChops.difference(area, sfocata)).mean[0] / 255


def mustard_share(image) -> float:
    """La quota di pixel giallo-ocra spenti: la dominante delle immagini generate.

    Un giallo pieno e acceso (l'accento di una palette) non conta: conta il
    giallo smorzato, fra l'ocra e la senape, steso su tutta l'immagine.
    """
    piccola = image.convert("RGB")
    piccola.thumbnail((160, 240))
    hsv = _pixels(piccola.convert("HSV"))
    # In PIL la tinta va da 0 a 255: 38°-62° sono 27-44.
    senape = sum(1 for h, sat, val in hsv if 27 <= h <= 44 and 64 <= sat <= 204 and 89 <= val <= 230)
    return senape / max(len(hsv), 1)


def _zone_scrim(image, zone, opacity: float):
    """Scurisce la zona del titolo con i bordi sfumati: niente riquadro visibile."""
    from PIL import Image, ImageDraw, ImageFilter

    width, height = image.size
    raggio = max(8, int(height * 0.03))
    mask = Image.new("L", (width, height), 0)
    # Il rettangolo si allarga quanto la sfumatura: dentro la zona l'opacità è
    # piena, e a sfumare è solo il bordo che sta fuori.
    ImageDraw.Draw(mask).rectangle(
        (int(zone[0] * width) - raggio, int(zone[1] * height) - raggio,
         int(zone[2] * width) + raggio, int(zone[3] * height) + raggio),
        fill=int(round(opacity * 255)),
    )
    mask = mask.filter(ImageFilter.GaussianBlur(raggio))
    return Image.composite(Image.new("RGB", (width, height), (0, 0, 0)), image, mask)


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
    layout: str = "alto",
    title_zone: tuple[float, float, float, float] | None = None,
) -> ImageReport:
    """Ritaglia, ridimensiona e ripulisce l'immagine per la prima di copertina.

    Con `title_zone` (dove cadrà il blocco del titolo, in frazioni) la velatura
    si adatta: si scurisce quella zona a passi finché il titolo bianco non
    stacca di 4,5:1 contro i pixel chiari che ha dietro, e il rapporto dice il
    contrasto ottenuto, il dettaglio dello sfondo e la dominante di colore.
    Con il titolo al centro la velatura in alto non serve: resta quella in basso
    per il nome dell'autore.
    """
    from .coverdesign import MIN_CONTRAST_ON_IMAGE
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
            top = SCRIM_TOP if layout != "centro" else (SCRIM_TOP[0], 0.0)
            prepared = _apply_scrim(prepared, top=top)

        title_contrast = title_noise = title_scrim = 0.0
        if title_zone is not None:
            base = prepared
            for extra in ZONE_SCRIM_STEPS if scrim else (0.0,):
                prepared = _zone_scrim(base, title_zone, extra) if extra else base
                title_contrast = zone_contrast(prepared, title_zone)
                title_scrim = extra
                if title_contrast >= MIN_CONTRAST_ON_IMAGE:
                    break
            title_noise = zone_noise(prepared, title_zone)
        mustard = mustard_share(prepared)

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
        layout=layout,
        title_contrast=round(title_contrast, 2),
        title_noise=round(title_noise, 4),
        title_scrim=title_scrim,
        mustard=round(mustard, 3),
    )


def title_problems(report: ImageReport) -> list[str]:
    """Quello che l'immagine fa al titolo: contrasto, sfondo rumoroso, dominante."""
    from .coverdesign import MIN_CONTRAST_ON_IMAGE

    problemi = []
    if report.title_contrast and report.title_contrast < MIN_CONTRAST_ON_IMAGE:
        problemi.append(
            f"Contrasto del titolo sull'immagine {report.title_contrast:.1f}:1 anche con la "
            f"velatura al massimo (minimo {MIN_CONTRAST_ON_IMAGE:g}:1): dietro il titolo "
            "l'immagine è troppo chiara."
        )
    if report.title_noise > MAX_ZONE_NOISE:
        problemi.append(
            f"Sfondo rumoroso dietro il titolo (dettaglio {report.title_noise:.3f}, massimo "
            f"{MAX_ZONE_NOISE}): le scritte si confondono con l'immagine."
        )
    if report.mustard > MAX_MUSTARD:
        problemi.append(
            f"Dominante giallo-senape sul {report.mustard:.0%} dell'immagine: è il segno "
            "riconoscibile di un'immagine generata senza direzione."
        )
    return problemi
