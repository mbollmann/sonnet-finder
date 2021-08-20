#!/usr/bin/env python3

"""Usage: sonnet-finder.py TEXTFILE [options]

Finds snippets in iambic pentameter in an English-language text and tries to
combine them to a rhyming sonnet.

Arguments:
  TEXTFILE                 Text file to produce a sonnet from.

Options:
  -o, --output TSVFILE     If given, writes all found candidate phrases along with
                           their slant rhyme classes to OUTFILE, in tsv format.
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
import string
import random
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import track

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(markup=True)],
)
log = logging.getLogger("rich")
console = Console()

from g2p_en import G2p
from g2p_en.expand import normalize_numbers
import re
import unicodedata
import nltk
from nltk.tokenize import TweetTokenizer

word_tokenize = TweetTokenizer().tokenize

try:
    nltk.data.find("tokenizers/punkt/english.pickle")
except LookupError:
    nltk.download("punkt")
sent_splitter = nltk.data.load("tokenizers/punkt/english.pickle")
sentence_split = sent_splitter.tokenize

iambic_pentameter = re.compile(r"(?=(01){5})")

# Similarity scores for non-equal phoneme pairs, taken from Hirjee & Brown (2010),
# Tables 1 & 2.  I only wrote down pairs with a score of -1.0 or higher.
# Used to determine which phoneme pairs are "similar enough" to produce slant
# rhymes.  Paper:
# <https://kb.osu.edu/bitstream/handle/1811/48548/1/EMR000091a-Hirjee_Brown.pdf>
SIMILARITY_SCORES = {
    ("AA", "AH"): -0.8,
    ("AA", "AO"): 1.6,
    ("AA", "ER"): -0.6,
    ("AA", "OW"): -1.0,
    ("AH", "EH"): -0.6,
    ("AH", "ER"): -0.2,
    ("AH", "IH"): -0.3,
    ("AH", "OW"): -1.0,
    ("AH", "OY"): -0.6,
    ("AH", "UH"): -0.9,
    ("AO", "AW"): -1.0,
    ("AO", "OW"): -0.3,
    ("AO", "OY"): -0.4,
    ("AO", "UH"): 1.1,
    ("AW", "AY"): -0.3,
    ("EH", "IH"): 0.2,
    ("IH", "IY"): -0.9,
    ("IH", "OY"): 0.2,
    ("OY", "UH"): 0.1,
    ("UH", "UW"): -0.5,
    ("B", "D"): 1.1,
    ("B", "DH"): 0.4,
    ("B", "G"): 1.9,
    ("B", "JH"): 1.9,
    ("B", "L"): -0.3,
    ("B", "M"): -0.5,
    ("B", "P"): 0.1,
    ("B", "R"): -0.9,
    ("B", "T"): -1.0,
    ("B", "V"): 2.3,
    ("B", "Z"): 0.3,
    ("CH", "F"): -0.3,
    ("CH", "G"): 0.2,
    ("CH", "JH"): 0.4,
    ("CH", "K"): 1.5,
    ("CH", "P"): 1.1,
    ("CH", "S"): 0.3,
    ("CH", "SH"): 0.6,
    ("CH", "T"): 0.9,
    ("CH", "TH"): 1.4,
    ("D", "G"): 0.1,
    ("D", "JH"): 0.2,
    ("D", "R"): -0.9,
    ("D", "T"): 0.2,
    ("D", "TH"): 0.0,
    ("D", "V"): -0.2,
    ("D", "Z"): 0.0,
    ("DH", "K"): -0.4,
    ("DH", "L"): -0.2,
    ("DH", "T"): -0.3,
    ("DH", "TH"): 1.3,
    ("DH", "V"): 2.3,
    ("DH", "Z"): 1.1,
    ("F", "K"): -0.3,
    ("F", "P"): 1.1,
    ("F", "S"): 1.0,
    ("F", "SH"): 1.2,
    ("F", "T"): -0.9,
    ("F", "TH"): 4.0,
    ("F", "V"): 0.6,
    ("G", "JH"): 1.8,
    ("G", "K"): 0.0,
    ("G", "L"): -0.2,
    ("G", "M"): -1.0,
    ("G", "P"): -0.7,
    ("G", "R"): -0.8,
    ("G", "V"): 0.3,
    ("G", "Z"): -0.3,
    ("JH", "M"): 0.1,
    ("JH", "N"): -0.5,
    ("JH", "P"): -0.2,
    ("JH", "R"): -0.3,
    ("JH", "S"): -0.6,
    ("JH", "SH"): 0.6,
    ("JH", "V"): 1.4,
    ("JH", "Z"): 1.0,
    ("JH", "ZH"): 4.1,
    ("K", "P"): 1.7,
    ("K", "S"): -0.7,
    ("K", "SH"): -0.6,
    ("K", "T"): 0.9,
    ("K", "TH"): 0.5,
    ("L", "R"): -0.5,
    ("M", "N"): 1.8,
    ("M", "NG"): 0.7,
    ("M", "TH"): 0.4,
    ("M", "V"): -0.6,
    ("N", "NG"): 1.2,
    ("N", "R"): -1.0,
    ("N", "SH"): -0.7,
    ("N", "TH"): -0.6,
    ("P", "SH"): -0.7,
    ("P", "T"): 1.1,
    ("P", "TH"): 0.9,
    ("P", "V"): -0.5,
    ("R", "SH"): -0.8,
    ("S", "SH"): 2.4,
    ("S", "T"): -1.0,
    ("S", "TH"): 1.0,
    ("S", "Z"): 0.5,
    ("S", "ZH"): 0.0,
    ("SH", "T"): -0.6,
    ("SH", "Z"): -0.2,
    ("SH", "ZH"): 3.6,
    ("T", "TH"): 1.6,
    ("T", "V"): -0.8,
    ("TH", "V"): 0.5,
    ("V", "Z"): -0.4,
    ("V", "ZH"): 1.6,
    ("Z", "ZH"): 3.0,
}

SIMILARITY_LIMIT = -0.05


def is_natural_language(line):
    """Determine if a line is likely to be actual natural language text, as
    opposed to, e.g., LaTeX formulas or tables.  Pretty crude heuristic, but as
    long as it filters out most of the bad stuff it's okay, I guess."""
    line = line.strip()
    if len(line) < 5:
        return False
    if "\\" in line or line[0] == "$" or line[-1] == "$":
        # probably contains a LaTeX formula; skip
        return False
    if line.count(" ") < 2:
        # maybe a headline, or a fragment
        return False
    if "   " in line or not line.replace("-", "").strip():
        # table?
        return False
    return True


def get_stress_and_boundaries(pron):
    """Determines stress patterns and word boundaries."""

    # For stress pattern, look at all vowel phonemes, and preserve word
    # boundaries (for now)
    pattern = [phon[-1] for phon in pron if phon[-1] in "012" or phon == " "]
    pattern = (
        "".join(pattern)
        .replace("2", "1")  # treat secondary stress like primary stress
        .replace("100 ", "101 ")  # treat 100 at the end of a word like 101,
        # cf. https://aclanthology.org/D16-1126, §3
    )
    if pattern[-3:] == "100":  # same as above
        pattern = pattern[:-3] + "101"

    # For each vowel, produce "1" if it's at the beginning of a word and "0"
    # otherwise; used to make sure the candidates we extract coincide with word
    # boundaries
    bound = "".join(
        "1" if b == " " else "0" for (a, b) in zip(pattern, " " + pattern) if a != " "
    )

    # For each vowel, remember which word (by index) it belongs to so we can
    # more easily extract the corresponding words later
    i = 0
    wordidx = []
    for p in pattern:
        if p == " ":
            i += 1
        else:
            wordidx.append(i)
    wordidx.append(len(pattern))

    pattern = pattern.replace(" ", "")

    return pattern, bound, wordidx


def extract_phrases(line, pron):
    """Finds candidate phrases in iambic pentameter from a given line and its
    pronunciation."""

    # First, extract the stress pattern and scan for iambic pentameter
    stress, bound, wordidx = get_stress_and_boundaries(pron)
    words, phon_by_word = None, None
    for match in iambic_pentameter.finditer(stress):
        idx = match.start()
        # Distinguish two possible types of rhyme: masculine (ends in stressed
        # vowel) and feminine (ends in an additional unstressed vowel);
        # depending on where the word boundaries fall, a candidate phrase can be
        # suitable for only one of these or both
        has_masc, has_fem = False, False
        if bound[idx] != "1":
            continue  # start of the pattern does not coincide with word
            # boundary; discard
        if len(bound) <= (idx + 10):  # pattern is at the end of the line; can
            # use for masc rhyme but not fem
            has_masc = True
        else:
            if bound[idx + 10] == "1":
                has_masc = True  # pattern ends at word boundary, can use for masc rhyme
            if stress[idx + 10] == "0" and (
                len(bound) <= (idx + 11) or bound[idx + 11] == "1"
            ):
                has_fem = True  # there is another unstressed vowel after the
                # pattern and it ends at word boundary, can use
                # for fem rhyme
        if not (has_masc or has_fem):
            continue

        # The rest of this function just reconstructs the matched section from
        # `line` and `pron`.  We also return the pronunciation in order to check
        # for rhyme later.
        if words is None:
            words = g2p_preprocess(line)
            phon_by_word = "÷".join(pron).split(" ")

        if has_masc:
            phrase = words[wordidx[idx] : wordidx[idx + 10]]
            if phrase[-1] in string.punctuation:
                phrase = phrase[:-1]
            phrase_phon = (
                "".join(phon_by_word[wordidx[idx] : wordidx[idx + 10]])
                .replace("÷", " ")
                .split()
            )
            log.debug(" ".join(phrase))
            yield (phrase, phrase_phon)

        if has_fem:
            phrase = words[wordidx[idx] : wordidx[idx + 11]]
            if phrase[-1] in string.punctuation:
                phrase = phrase[:-1]
            phrase_phon = (
                "".join(phon_by_word[wordidx[idx] : wordidx[idx + 11]])
                .replace("÷", " ")
                .split()
            )
            log.debug(" ".join(phrase))
            yield (phrase, phrase_phon)


def g2p_preprocess(text):
    """Preprocess text like the g2p_en library does.

    Unfortunately the library does not encapsulate this in its own function, so
    we copy the relevant passage here.  Used in order to map the stress patterns
    (detected from the g2p_en output) back to orthographic words.

    Adapted with minimal changes from
    <https://github.com/Kyubyong/g2p/blob/c6439c274c42b9724a7fee1dc07ca6a4c68a0538/g2p_en/g2p.py#L148-L161>
    by Kyubyong Park & Jongseok Kim, licensed under Apache 2.0
    <https://www.apache.org/licenses/LICENSE-2.0>
    """
    text = normalize_numbers(text)
    text = "".join(
        char
        for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )  # Strip accents
    text = text.lower()
    text = re.sub("[^ a-z'.,?!\-]", "", text)
    text = text.replace("i.e.", "that is")
    text = text.replace("e.g.", "for example")

    # tokenization
    words = word_tokenize(text)
    return words


def hash_by_strict_rhyme(candidates):
    """Computes a dictionary with strict rhyme classes as keys and candidate
    phrases as values."""

    rhyme = defaultdict(set)
    for (phrase, pron) in candidates:
        rhyme_class = []
        for phoneme in pron[::-1]:
            if phoneme[0] not in "ABCDEFGHIJKLMNOPRSTUVWYZ":
                continue
            phoneme = phoneme.replace("2", "1")
            rhyme_class.insert(0, phoneme)
            if phoneme[-1] == "1":
                break
        rhyme_class = "—".join(rhyme_class)
        rhyme[rhyme_class].add(tuple(phrase))

    return rhyme


def hash_by_slant_rhyme(candidates):
    """Computes a dictionary with slant rhyme classes as keys and candidate
    phrases as values.

    Candidate phrases here actually means a tuple of the orthographic phrase and
    its full phonemes, in order to be able to analyze the rhyme further later.
    """

    rhyme = defaultdict(set)
    for (phrase, pron) in candidates:
        rhyme_class = []
        rhyme_phonemes = []
        vowels_seen = 0
        inserted_placeholder = False
        for phoneme in pron[::-1]:
            if phoneme[0] not in "ABCDEFGHIJKLMNOPRSTUVWYZ":
                continue
            phoneme = phoneme.replace("2", "1")
            rhyme_phonemes.insert(0, phoneme)

            if phoneme[-1] not in "01":
                if vowels_seen == 0:
                    rhyme_class.insert(0, phoneme)
                elif vowels_seen == 1 and not inserted_placeholder:
                    rhyme_class.insert(0, "*")
                    inserted_placeholder = True
                else:
                    pass
            else:  # vowel
                if vowels_seen < 2:
                    rhyme_class.insert(0, phoneme)
                if phoneme[-1] == "1":
                    vowels_seen = 2
                else:
                    vowels_seen = 1

            if vowels_seen > 1:
                break

        rhyme_class = "—".join(rhyme_class)
        rhyme[rhyme_class].add((tuple(phrase), tuple(rhyme_phonemes)))

    return rhyme


def are_similar(phoneme1, phoneme2):
    """Check if two phonemes are similar enough as determined by the similarity
    scores and limit (see above)."""

    if phoneme1 == phoneme2:
        return True
    score = SIMILARITY_SCORES.get(
        (phoneme1, phoneme2), SIMILARITY_SCORES.get((phoneme2, phoneme1), -99)
    )
    return score > SIMILARITY_LIMIT


def can_rhyme(phrase1, phrase2):
    """Check if two phrases can rhyme.

    This largely attempts to implement the algorithm by Ghazvininejad et
    al. (2016) <https://aclanthology.org/D16-1126>, Sec. 5.2.  I also assume
    that we know that the two phrases belong to the same slant rhyme class as
    returned by `hash_by_slant_rhyme`.
    """
    words1, pron1 = phrase1
    words2, pron2 = phrase2
    assert pron1[0][-1] == "1", " ".join(pron1)
    assert pron2[0][-1] == "1", " ".join(pron2)

    # We don't want to "rhyme" identical words
    if words1[-1] == words2[-1]:
        return False
    # Identical, strict rhymes?
    if "*" not in pron1 and pron1 == pron2:
        return True
    # Step 2. Replace ER with UH R
    while "ER" in pron1:
        idx = pron1.index("ER")
        pron1 = pron1[:idx] + ["UH", "R"] + pron1[idx + 1 :]
    while "ER" in pron2:
        idx = pron2.index("ER")
        pron2 = pron2[:idx] + ["UH", "R"] + pron2[idx + 1 :]
    # Step 3,4,5. Find v-x-w
    v1, v2 = pron1[0], pron2[0]
    if v1 != v2:
        return False  # Step 6a; shouldn't happen
    x1, x2 = [], []
    w1, w2 = None, None
    for phoneme in pron1[:0:-1]:
        if phoneme[-1] == "0":
            if w1 is None:
                w1 = phoneme
        elif w1 is not None:
            x1.insert(0, phoneme)
    for phoneme in pron2[:0:-1]:
        if phoneme[-1] == "0":
            if w2 is None:
                w2 = phoneme
        elif w2 is not None:
            x2.insert(0, phoneme)
    if w1 != w2:
        return False  # Step 6b; shouldn't happen
    if (not x1) or (not x2):
        return False
    # Step 7.
    if len(x1) == 1 and len(x2) == 1:
        return are_similar(x1[0], x2[0])
    # Step 8.
    if sum(1 for x in x1 if x[-1] == "0") != sum(1 for x in x2 if x[-1] == "0"):
        return False
    # Step 10.
    if x1[0] == x2[0] and are_similar(x1[-1], x2[-1]):
        return True
    # Step 11.
    if x1[-1] == x2[-1] and are_similar(x1[0], x2[0]):
        return True
    return False


def main(args):
    g2p = G2p()

    with open(args["TEXTFILE"], "r") as f:
        lines = [l.strip() for l in f if l.strip()]
    log.debug(f"Read {len(lines)} lines from {args['TEXTFILE']}")

    candidates = []

    for line in track(lines, description="Scanning for iambic pentameter..."):
        for sentence in sentence_split(line):
            if not is_natural_language(sentence):
                continue

            # split up hyphenated words, as this typically improves the
            # pronunciation prediction on these words
            sentence = sentence.replace("-", " - ")

            pron = g2p(sentence)
            candidates.extend(phrase for phrase in extract_phrases(sentence, pron))

    log.info(f"Extracted {len(candidates)} candidate phrases.")

    # h_strict = hash_by_strict_rhyme(candidates)
    # log.info(f"Found {len(h_strict)} different strict rhyme classes.")
    h_slant = hash_by_slant_rhyme(candidates)
    log.debug(f"Found {len(h_slant)} different slant rhyme classes.")

    if args["--output"]:
        with open(args["--output"], "w") as f:
            for rhyme_class, examples in h_slant.items():
                for phrase, pron in examples:
                    phrase = " ".join(phrase)
                    pron = " ".join(pron)
                    print(f"{phrase}\t{rhyme_class}\t{pron}", file=f)
        log.info(f"Wrote candidates to [magenta]{args['--output']}[/]")

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

    log.info(f"Found {len(rhyme_pairs)} rhyme classes with paired phrases.")

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
