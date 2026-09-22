"""Etichette e testi fissi, in italiano e inglese."""

from __future__ import annotations

LABELS: dict[str, dict[str, str]] = {
    "it": {
        "toc": "Indice",
        "chapter": "Capitolo",
        "introduction": "Introduzione",
        "conclusion": "Conclusione",
        "about_author": "L'autore",
        "review_title": "Una richiesta",
        "review_text": (
            "Se questo libro ti è stato utile, lasciare una recensione onesta su Amazon "
            "richiede meno di un minuto e aiuta altri lettori a capire se fa al caso loro. "
            "Grazie."
        ),
        "copyright": "Tutti i diritti riservati.",
        "copyright_body": (
            "Nessuna parte di questo libro può essere riprodotta o trasmessa in alcuna forma "
            "o con alcun mezzo, elettronico o meccanico, senza il permesso scritto dell'editore, "
            "salvo brevi citazioni in recensioni o articoli."
        ),
        "disclaimer_title": "Avvertenza",
        "disclaimer_body": (
            "Le informazioni contenute in questo libro hanno finalità divulgativa e non "
            "sostituiscono una consulenza professionale personalizzata. L'autore e l'editore "
            "non rispondono di eventuali danni derivanti dall'uso dei contenuti."
        ),
        "ai_disclosure": (
            "Questo libro è stato realizzato con l'ausilio di strumenti di intelligenza "
            "artificiale, sotto supervisione, revisione e responsabilità editoriale umana."
        ),
        "first_edition": "Prima edizione",
        "printed_by": "Stampato da Amazon KDP",
        "isbn": "ISBN",
        "by": "di",
        "continues": "(segue)",
        # testi di copertina: vanno nella lingua del libro, sempre. Un
        # occhiello inglese su una copertina italiana dice al cliente che il
        # libro non è per lui, e il clic lo perdi lì.
        "cover_kicker_puzzles": "ENIGMI DI DEDUZIONE",
        "cover_pages": "{n} PAGINE",
        "cover_chapters": "{n} CAPITOLI",
        "cover_practice": "{n} SCHEDE PRATICHE",
        "cover_large_print": "Caratteri grandi",
    },
    "en": {
        "toc": "Contents",
        "chapter": "Chapter",
        "introduction": "Introduction",
        "conclusion": "Conclusion",
        "about_author": "About the Author",
        "review_title": "One request",
        "review_text": (
            "If this book helped you, leaving an honest review on Amazon takes less than a "
            "minute and helps other readers decide whether it is right for them. Thank you."
        ),
        "copyright": "All rights reserved.",
        "copyright_body": (
            "No part of this book may be reproduced or transmitted in any form or by any means, "
            "electronic or mechanical, without written permission from the publisher, except for "
            "brief quotations in reviews or articles."
        ),
        "disclaimer_title": "Disclaimer",
        "disclaimer_body": (
            "The information in this book is provided for general purposes and does not replace "
            "personalised professional advice. The author and the publisher accept no liability "
            "for any damages arising from the use of this content."
        ),
        "ai_disclosure": (
            "This book was produced with the assistance of artificial intelligence tools, under "
            "human supervision, review and editorial responsibility."
        ),
        "first_edition": "First edition",
        "printed_by": "Printed by Amazon KDP",
        "isbn": "ISBN",
        "by": "by",
        "continues": "(continued)",
        "cover_kicker_puzzles": "DEDUCTION PUZZLES",
        "cover_pages": "{n} PAGES",
        "cover_chapters": "{n} CHAPTERS",
        "cover_practice": "{n} PRACTICE SHEETS",
        "cover_large_print": "Large print",
    },
}


def L(language: str, key: str) -> str:
    """Etichetta nella lingua richiesta, con fallback sull'italiano."""
    table = LABELS.get(language, LABELS["it"])
    return table.get(key, LABELS["it"].get(key, key))
