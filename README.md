# Sonnet finder

Finds snippets in iambic pentameter in English-language text and tries to
combine them to a rhyming sonnet.

## Usage

This is a Python script that should run without a GPU or any other special
hardware requirements.

1. Install the required packages, e.g. via: `pip install -r requirements.txt`

2. Prepare a plain text file, say `input.txt`, with text you want to make a
   sonnet out of (sonnet-ize? sonnet-ify?).  It can have multiple sentences on
   the same line, but a sentence should _not_ be split across multiple lines.

   For example, I used `pandoc --to=plain --wrap=none` to generate a text file
   from my LaTeX papers.  You could also start by grabbing some text files from
   [Project Gutenberg](https://www.gutenberg.org/).

3. Run sonnet finder: `python sonnet_finder.py input.txt -o output.tsv`

   Using `-o` will save a list of all extracted candidate phrases, sorted by
   rhyme pattern, to the specified output file, so you can browse and
   cherry-pick them to make your own sonnet out of these lines.

   Either way, the script will output a full example sonnet to STDOUT (provided
   enough rhyming pairs in iambic pentameter were found).

4. If you've saved an `output.tsv` file before, you can quickly generate new
   sonnets via `python sonnet_remix.py output.tsv`.  Since the stress and
   pronunciation prediction can be slow on larger files, this is much better
   than re-running `sonnet_finder.py` if you want more automatically generated
   suggestions.

## Examples

This is a sonnet (with cherry-picked lines) made out of [**my PhD
thesis**](https://www.linguistics.rub.de/forschung/arbeitsberichte/22.pdf):

> the application of existing tools  
> describe a mapping to a modern form  
> applying similar replacement rules  
> the base ensembles slightly outperform  
>
> hungarian, icelandic, portuguese  
> perform a similar evaluation  
> contemporary lexemes or morphemes  
> a single dataset in isolation  
>
> historical and modern language stages  
> the weighted combination of encoder  
> the german dative ending -e in phrases  
> predictions fed into the next decoder  
>
> in this example from the innsbruck letter  
> machine translation still remains the better

These stanzas are compiled from a couple of automatically-generated suggestions
based on the **_abstracts_ of all papers published in 2021 in the [ACL
Anthology](https://aclanthology.org/)**:

> effective algorithm that enables  
> improvements on a wide variety  
> and training with adjudicated labels  
> anxiety and test anxiety  
>
> obtain remarkable improvements on  
> decoder architecture, which equips  
> associated with the lexicon  
> surprising personal relationships  
>
> achieves the same embedding quality  
> the current efforts of explaining such  
> detect and filter out low-quality  
> and smaller datasets in german, dutch  
>
> examples, while in practice, most unseen  
> evaluate translation tasks between

Here's the same using [Moby Dick](https://www.gutenberg.org/ebooks/2701):

> among the marble senate of the dead  
> offensive matters consequent upon  
> a crawling reptile of the land, instead  
> fifteen, eighteen, and twenty hours on  
>
> the lakeman now patrolled the barricade  
> egyptian tablets, whose antiquity  
> the waters seemed a golden finger laid  
> maintains a permanent obliquity  
>
> the pequod with the little negro pippin  
> and with a frightful roll and vomit, he  
> increased, besides perhaps improving it in  
> transparent air into the summer sea  
>
> the traces of a simple honest heart  
> the fishery, and not the thousandth part

*(The emjambment in the third stanza here is a lucky coincidence; the script
currently doesn't do any kind of syntactic analysis or attempt coherence between
lines.)*

## How it works

This script relies on the [grapheme-to-phoneme library `g2p_en` by Park &
Kim](https://github.com/Kyubyong/g2p) to convert the English input text to
phoneme sequences (i.e., how the text would be pronounced).  I chose this
because it's a pip-installable Python library that fulfills two important
criteria:

1. it's not restricted to looking up pronunciations in a dictionary, but can
   handle arbitrary words through the use of a neural model (although,
   obviously, this will not always be accurate);

2. it provides stress information for each vowel (i.e., whether any given vowel
   should be stressed or unstressed, which is important for determining the
   poetic meter).

The script then scans the g2p output for occurrences of [iambic
pentameter](https://en.wikipedia.org/wiki/Iambic_pentameter), i.e. a
`0101010101(0)` pattern, additionally checking if they coincide with word
boundaries.

For finding snippets that _rhyme_, I rely mostly on [Ghazvininejad et
al. (2016)](https://aclanthology.org/D16-1126), particularly §3 (relaxing the
iambic pentameter a bit by allowing words that end in `100`) and §5.2 (giving an
operational definition of "slant rhyme" that I mostly try to follow).

### Limitations

This script can only be as good as the grapheme-to-phoneme algorithm that's
used.  It frequently fails on words it doesn't know (for example, it tries to
rhyme _datasets_ with _Portuguese_, or _noun_ with _cross-lingual_?!) and also
usually fails on abbreviations.


## Can I use this for ...?

- **Generating different types of poems?**  You could start by changing the regex
  `iambic_pentameter` to something else; maybe a sequence of
  [dactyls](https://en.wikipedia.org/wiki/Dactyl_(poetry))?  There are some
  further hardcoded assumptions in the code about iambic pentameter in the
  function `get_stress_and_boundaries()`.

- **Generating poems in languages other than English?**  This mostly requires a
  suitable replacement for `g2p_en` that predicts pronunciations and stress
  patterns for the desired language, as well as re-writing the code that
  determines whether two phrases can rhyme; see the comments in the script for
  details.  In particular, the code for English uses [ARPABET
  notation](https://en.wikipedia.org/wiki/ARPABET) for the pronunciation, which
  won't be suitable for other languages.

- **Generate completely novel phrases _in the style of_ an input text?**  This
  script does not "hallucinate" any text or generate anything that wasn't
  already there in the input; if you want to do that, take a look at
  [Deep-speare](https://github.com/jhlau/deepspeare) maybe.


## etc.

Written by [Marcel Bollmann](https://marcel.bollmann.me/), inspired by [a
tweet](https://twitter.com/samuelmehr/status/1427463112563773441), licensed
under the [MIT License](LICENSE).

[I'm not the first one to write a script like
this](https://github.com/rossgoodwin/sonnetizer), but it was a fun exercise!
