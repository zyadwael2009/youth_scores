"""Grouping the free-text venue names typed on matches into likely-same venues.

Match venues were entered as free text for years, so one ground appears under
many spellings ("بلاك ستار ٢" / "بلك ستار ٢" / "ملعب بلاك ستار ٢"). This module
only *suggests* groups for the admin cleanup screen — nothing is merged without a
person confirming it, because similar spellings are sometimes different grounds
("زد الشيخ زايد" vs "مركز شباب الشيخ زايد").

Two rules keep the suggestions honest:
- compare the *distinctive* part of a name: generic words (ملعب، نادي، مركز شباب،
  التنمية الشبابية …) and Arabic spelling variants are stripped first;
- a spelling joins a group only if it is close to that group's MAIN (most-used)
  spelling, so similarity never chains A≈B≈C into one group.
Looser relations (one name's words contained in another's, e.g. "دار الوقود" and
"دار الوقود التجمع الخامس") are returned separately as "maybe" pairs.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

_DIACRITICS = re.compile(r"[ً-ْٰـ]")  # harakat + tatweel
_PUNCT = re.compile(r"[\-_.,،()\"'/\\]+")
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_GENERIC = {
    "مركز", "شباب", "تنميه", "شبابيه", "شبابه", "شباببه", "نادي", "ملعب", "استاد",
    "ستاد", "مش", "تش", "م", "ش", "ت", "مدينه", "رئيسي", "لل", "و",
}


def normalize(s: str | None) -> str:
    """Spelling-insensitive form of an Arabic/English name (alef/ya/ta-marbuta
    variants, diacritics, Arabic-Indic digits, punctuation, case)."""
    s = _DIACRITICS.sub("", (s or "").strip().lower())
    s = re.sub("[أإآٱ]", "ا", s)
    s = s.replace("ة", "ه").replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي")
    s = s.translate(_DIGITS)
    s = re.sub(r"(\d)(?=[^\d\s])", r"\1 ", s)  # "6اكتوبر" -> "6 اكتوبر"
    s = _PUNCT.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def core_tokens(s: str | None) -> list[str]:
    """The distinctive words of a venue name: generic words and the definite
    article / "ب" preposition prefixes removed."""
    out = []
    for t in normalize(s).split():
        if len(t) > 4 and t.startswith("بال"):
            t = t[3:]
        elif len(t) > 3 and t.startswith("ال"):
            t = t[2:]
        elif len(t) > 4 and t[0] == "ب":
            t = t[1:]
        if t in _GENERIC or t.startswith("شباب") or t.startswith("تنمي"):
            continue
        out.append(t)
    return out


def core(s: str | None) -> str:
    return " ".join(core_tokens(s))


def is_close(a: str, b: str, threshold: float = 0.86) -> bool:
    """Two cores name the same ground: identical ignoring spaces, or a near
    spelling (a typo or a missing letter)."""
    a2, b2 = a.replace(" ", ""), b.replace(" ", "")
    if not a2 or not b2:
        return False
    if a2 == b2:
        return True
    if min(len(a2), len(b2)) < 4:
        return False
    m = SequenceMatcher(None, a2, b2)
    return (m.real_quick_ratio() >= threshold and m.quick_ratio() >= threshold
            and m.ratio() >= threshold)


# A spelling may also join through an existing member of a group, but only when
# nearly identical to it — a typo of a typo — so chains stay one short hop.
_MEMBER_THRESHOLD = 0.92


def group_names(counts: dict[str, int]) -> tuple[list[list[str]], list[tuple[int, int]]]:
    """Group venue spellings. ``counts`` maps each spelling to its match count.

    Returns ``(groups, maybe)``: ``groups`` is a list of spelling lists, each with
    its most-used spelling first, ordered by total matches; ``maybe`` holds index
    pairs into ``groups`` whose names might be the same ground."""
    found: list[tuple[str, list[str]]] = []  # (main core, spellings)
    member_cores: list[list[str]] = []
    for name in sorted(counts, key=lambda k: (-counts[k], k)):
        c = core(name)
        for gi, (main, names) in enumerate(found):
            if is_close(c, main) or any(
                    is_close(c, mc, _MEMBER_THRESHOLD) for mc in member_cores[gi]):
                names.append(name)
                member_cores[gi].append(c)
                break
        else:
            found.append((c, [name]))
            member_cores.append([c])

    found.sort(key=lambda g: (-sum(counts[n] for n in g[1]), g[1][0]))
    groups = [names for _, names in found]

    tok = [set(main.split()) for main, _ in found]
    maybe = [
        (i, j)
        for i in range(len(found)) for j in range(i + 1, len(found))
        if tok[i] and tok[j] and (tok[i] < tok[j] or tok[j] < tok[i])
    ]
    return groups, maybe


def best_venue(names: list[str], venues: list[tuple[int, str | None, str | None]]) -> int | None:
    """The directory venue (id, name_ar, name_en) whose name matches any of a
    group's spellings, preferring the earliest (most-used) spelling."""
    cores = [core(n) for n in names]
    for c in cores:
        for vid, ar, en in venues:
            if any(is_close(c, core(v)) for v in (ar, en) if v):
                return vid
    return None
