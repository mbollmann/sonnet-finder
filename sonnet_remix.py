#!/usr/bin/env python3

"""Usage: sonnet-remix.py TSVFILE [options]

Tries to combine lines to a rhyming sonnet, based on a TSVFILE previously saved
by sonnet-finder.py

Arguments:
  TSVFILE                  TSV file with candidate phrases previously saved by
                           sonnet-finder.py

Options:
  -s, --similarity SCORE   Similarity threshold for slant rhymes; suggested values:
                            *  0.0 for more conservative rhyming
                            * -0.6 for the value used by Ghazvininejad et al.
                           [default: -0.6]
  --debug                  Output debug-level info about what the script is doing.
  --help                   This helpful text.
"""

from docopt import docopt
import logging
from collections import defaultdict
import random
from rich.console import Console
from rich.logging import RichHandler

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(markup=True)],
)
log = logging.getLogger("rich")
console = Console()

from sonnet_finder import can_rhyme


def main(args):
    h_slant = defaultdict(set)

    with open(args["TSVFILE"], "r") as f:
        for line in f:
            if not line.strip():
                continue
            phrase, rhyme_class, pron = line.strip().split("\t")
            h_slant[rhyme_class].add((tuple(phrase.split(" ")), tuple(pron.split(" "))))

    log.debug(
        f"Trying to find rhyming pairs using similarity limit {SIMILARITY_LIMIT} ..."
    )

    rhyme_pairs = defaultdict(list)
    for (rhyme_class, phrases) in h_slant.items():
        if len(phrases) < 2:
            continue
        phrases = list(phrases)
        random.shuffle(phrases)

        while len(phrases) > 1:
            p_1 = phrases.pop()
            for p_2 in phrases:
                if can_rhyme(p_1, p_2):
                    rhyme_pairs[rhyme_class].append((p_1[0], p_2[0]))
                    break

    log.debug(f"Found {len(rhyme_pairs)} rhyme classes with paired phrases.")

    classes = list(rhyme_pairs.keys())
    random.shuffle(classes)

    stanzas = 0
    while stanzas < 3 and len(classes) > 1:
        pair_a = random.choice(rhyme_pairs[classes.pop()])
        pair_b = random.choice(rhyme_pairs[classes.pop()])
        console.print("")
        console.print(" ".join(pair_a[0]), style="yellow italic")
        console.print(" ".join(pair_b[0]), style="yellow italic")
        console.print(" ".join(pair_a[1]), style="yellow italic")
        console.print(" ".join(pair_b[1]), style="yellow italic")
        stanzas += 1

    if classes:
        pair = random.choice(rhyme_pairs[classes.pop()])
        console.print("")
        console.print(" ".join(pair[0]), style="yellow italic")
        console.print(" ".join(pair[1]), style="yellow italic")

    console.print("")
    return 0


if __name__ == "__main__":
    args = docopt(__doc__)
    if args["--debug"]:
        log.setLevel("DEBUG")

    SIMILARITY_LIMIT = float(args["--similarity"])

    r = main(args)
    exit(r)
