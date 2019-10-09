import json
from collections import defaultdict
from pathlib import Path
from pprint import pprint
from typing import List, Optional, Dict, Tuple, Set

from pysle.isletool import LexicalTool, WordNotInISLE
from pysle.pronunciationtools import findBestSyllabification
from tqdm import tqdm

isleDict = LexicalTool('ISLEdict.txt')


def get_ipa_syllables(word) -> Optional[List[List[str]]]:
    try:
        return isleDict.lookup(word)[0][0][0]
    except WordNotInISLE:
        return None


sy_file = Path('25K-syllabified-sorted-alphabetically.txt')
lines = sy_file.read_text().splitlines()

failed = 0
total = len(lines)

correspondence: Dict[str, List[Tuple[str, str]]] = defaultdict(list)

stress_markers = {'ˌ', 'ˈ'}
aa = '̩'
all_chars: Set[str] = set()
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
            correspondence[word].append((word_morphemes[i], new_syllable))
with open('word_to_ipa_with_syllables.json', 'w') as file:
    json.dump(correspondence, file)
print(correspondence['zoo'])
print(failed / total)

pprint(dict(list(correspondence.items())[:20]))