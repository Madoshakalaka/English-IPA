import json
from collections import defaultdict
from pathlib import Path
from pprint import pprint
from typing import List, Optional, Dict, Tuple, Set

from pysle.isletool import LexicalTool, WordNotInISLE
from pysle.pronunciationtools import findBestSyllabification
from tqdm import tqdm


# {'w', 'v', 'ŋ', 'p', 'ɝ', 'ɑ', 'ɾ', 'b', 'ɚ',
# 'ɔ', 'ʊ', 'n', 'u', 'j', 'm', 'k', 'i', 'ə', 'd', 'æ',
# 'ɛ', 'o', 's', 'ɵ', 'e', 'ʒ', 'l', 'z', '̩', 'ʌ',
# 'g', 'ɹ', 'f', 'ɪ', 'h', 'ð', 'ʃ', 'a', 't'}


def get_ipa_syllables(word) -> Optional[List[List[str]]]:
    try:
        return isleDict.lookup(word)[0][0][0]
    except WordNotInISLE:
        return None


sy_file = Path('25K-syllabified-sorted-alphabetically.txt')
lines = sy_file.read_text().splitlines()

failed = 0
total = len(lines)

correspondence: Dict[str, List[List[str]]] = defaultdict(list)

stress_markers = {'ˌ', 'ˈ'}
all_chars: Set[str] = set()

CONSONANT_PHONEMES = {'w', 'v', 'p', 'ɾ', 'b', 'n', 'j', 'm', 'k', 'd', 's', 'ʒ', 'l', 'z', 'g', 'ɹ', 'f', 'h', 'ð',
                      'ʃ', 't'}
CONSONANT_LETTERS = {'w', 'v', 'p', 't', 'b', 'n', 'j', 'm', 'k', 'd', 's', 'j', 'l', 'z', 'g', 'r', 'f', 'h', 'c', 'q',
                     'x', 'y'}
VOWEL_LETTERS = {'a', 'e', 'i', 'o', 'u'}


def fix_missing_trailing_consonants(correspondence: List[List[str]]):
    """
    25k file sometimes have missing trailing consonant letters
    ablaze: ['a', 'blaze']
    where b is classified to the first syllable in ISLE

    This function aims to fix that

    >>> fix_missing_trailing_consonants([['a', 'əb'], ['blaze', 'leiz']])
    [['ab', 'əb'], ['laze', 'leiz']]
    >>> fix_missing_trailing_consonants([['a', 'eib'], ['bly', 'li']])
    [['ab', 'eib'], ['ly', 'li']]
    """
    for i, (morpheme, ipa) in enumerate(correspondence[:-1]):
        if morpheme:
            if morpheme[-1] in VOWEL_LETTERS and ipa[-1] in CONSONANT_PHONEMES:

                if len(correspondence[i + 1][0]) > 0:
                    if (ipa[-1], correspondence[i + 1][0][0]) in {('t', 't'), ('b', 'b'), ('d', 'd'), ('p', 'p')}:
                        correspondence[i][0] += correspondence[i + 1][0][0]
                        correspondence[i + 1][0] = correspondence[i + 1][0][1:]
    return correspondence


def fix_extra_trailing_consonants(correspondence: List[List[str]]):
    """
    25k file sometimes have extra trailing consonant letters
    abated: ['a', 'bat', 'ed']
    where t is classified to the last syllable in ISLE

    This function aims to fix that

    >>> fix_extra_trailing_consonants([['a', 'ə'], ['bat', 'bei'], ['ed', 'tɪd']])
    [['a', 'ə'], ['ba', 'bei'], ['ted', 'tɪd']]
    >>> fix_extra_trailing_consonants([['rock', 'ɹɑ'], ['et', 'kət']])
    [['ro', 'ɹɑ'], ['cket', 'kət']]

    """
    # {'w', 'v', 'ŋ', 'p', 'ɝ', 'ɑ', 'ɾ', 'b', 'ɚ',
    # 'ɔ', 'ʊ', 'n', 'u', 'j', 'm', 'k', 'i', 'ə', 'd', 'æ',
    # 'ɛ', 'o', 's', 'ɵ', 'e', 'ʒ', 'l', 'z', '̩', 'ʌ',
    # 'g', 'ɹ', 'f', 'ɪ', 'h', 'ð', 'ʃ', 'a', 't'}
    for i, (morpheme, ipa) in enumerate(correspondence[:-1]):
        trailing_stuff = ''
        for letter_ind in range(len(morpheme) - 1, -1, -1):
            letter = morpheme[letter_ind]
            if letter in CONSONANT_LETTERS and ipa[-1] in {'ɑ', 'ɔ', 'ʊ', 'u', 'i', 'ə', 'æ', 'ɛ', 'o', 'ʌ', 'ɪ'}:
                trailing_stuff = letter + trailing_stuff
            else:
                correspondence[i][0] = morpheme[:letter_ind + 1]
                correspondence[i + 1][0] = trailing_stuff + correspondence[i + 1][0]
                break
    return correspondence


if __name__ == '__main__':

    isleDict = LexicalTool('ISLEdict.txt')
    for line in tqdm(lines):
        word = line.replace(';', '')
        word_morphemes = line.split(';')
        ipa_syllables = get_ipa_syllables(word)
        if ipa_syllables is None or len(ipa_syllables) != len(word_morphemes):
            failed += 1
        else:
            for i, syllable in enumerate(ipa_syllables):

                new_syllable = ''

                for part in syllable:
                    new_part = ''
                    for char in part:
                        if char not in stress_markers:
                            new_part += char
                    new_syllable += new_part

                correspondence[word].append([word_morphemes[i], new_syllable])
                fix_extra_trailing_consonants(correspondence[word])
                fix_missing_trailing_consonants(correspondence[word])
    with open('word_to_ipa_with_syllables.json', 'w') as file:
        json.dump(correspondence, file)
    print(correspondence['zoo'])
    print(failed / total)

    pprint(dict(list(correspondence.items())[:20]))
