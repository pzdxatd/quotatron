"""Hardcoded ~30 quotes used when content/ JSON files are missing or corrupt.

This is the safety net for the scheduler: if ``ContentLibrary.from_disk``
raises (SD card error, accidental ``rm -rf``, JSON parse failure on boot),
the scheduler falls back to ``emergency_library()`` so the device keeps
displaying *something* until the operator fixes the corpus.

All entries are intentionally well-known, public-domain (pre-1953) quotes
attributed to historical figures. All use ``category="philosophy"`` per
spec — this fallback corpus is not balanced; it just needs to exist.
"""
from __future__ import annotations

from quotatron.models import ContentItem

EMERGENCY: list[ContentItem] = [
    ContentItem(kind="quote", text=t, author=a, category="philosophy", source="emergency")
    for t, a in [
        ("The unexamined life is not worth living.", "Socrates"),
        ("Know thyself.", "Inscription at Delphi"),
        ("Cogito, ergo sum.", "René Descartes"),
        ("All men by nature desire to know.", "Aristotle"),
        ("The journey of a thousand miles begins with a single step.", "Lao Tzu"),
        ("Veni, vidi, vici.", "Julius Caesar"),
        ("To be, or not to be: that is the question.", "William Shakespeare"),
        ("All the world's a stage, and all the men and women merely players.", "William Shakespeare"),
        ("I think, therefore I am.", "René Descartes"),
        ("That which does not kill us makes us stronger.", "Friedrich Nietzsche"),
        ("He who has a why to live can bear almost any how.", "Friedrich Nietzsche"),
        ("The life of man is solitary, poor, nasty, brutish, and short.", "Thomas Hobbes"),
        ("The only thing necessary for the triumph of evil is for good men to do nothing.", "Edmund Burke"),
        ("Liberty consists in doing what one desires.", "John Stuart Mill"),
        ("I have nothing to declare except my genius.", "Oscar Wilde"),
        ("The mass of men lead lives of quiet desperation.", "Henry David Thoreau"),
        ("In wildness is the preservation of the world.", "Henry David Thoreau"),
        ("A foolish consistency is the hobgoblin of little minds.", "Ralph Waldo Emerson"),
        ("Whatever you can do, or dream you can, begin it.", "Johann Wolfgang von Goethe"),
        ("Give me liberty, or give me death!", "Patrick Henry"),
        ("The only true wisdom is in knowing you know nothing.", "Socrates"),
        ("Beware lest you lose the substance by grasping at the shadow.", "Aesop"),
        ("Genius is one percent inspiration and ninety-nine percent perspiration.", "Thomas Edison"),
        ("It is dangerous to be right when the government is wrong.", "Voltaire"),
        ("Common sense is not so common.", "Voltaire"),
        ("All men are created equal.", "Thomas Jefferson"),
        ("To live is the rarest thing in the world. Most people exist, that is all.", "Oscar Wilde"),
        ("The only way to do great work is to love what you do.", "anonymous"),
        ("Waste no more time arguing what a good man should be. Be one.", "Marcus Aurelius"),
        ("You have power over your mind — not outside events. Realize this, and you will find strength.", "Marcus Aurelius"),
    ]
]


def emergency_library():
    """Return a ContentLibrary backed by the hardcoded EMERGENCY list.

    The import is intentionally lazy/inside-function to avoid any risk of a
    circular import — content.py already imports models.py, and this module
    also imports models.py, so there is no real cycle today, but keeping the
    ContentLibrary import deferred is defensive against future refactors.
    """
    from quotatron.content import ContentLibrary

    return ContentLibrary(items=list(EMERGENCY))
