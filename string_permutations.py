import math
import functools
from curried import curried

class MaxPermutationsException(Exception):
    pass


@curried(2)
def string_permutations(max, word):
    def string_permutations_generator(max, word):
        if(math.factorial(len(word)) > max):
            raise MaxPermutationsException(
                f"permutations for {word} exceed max permutation count {max}")
        variations = [word]

        if len(word) == 2:
            variations = [*variations, word[::-1]]
        elif len(word) > 2:
            def combine_permutations(acc, letterIndex):
                letter, i = letterIndex
                sub = string_permutations_generator(
                    max, word[:i] + word[i + 1:])
                for v in acc:
                    yield v
                for v in map(lambda x: letter + x, sub):
                    yield v

            variations = functools.reduce(
                combine_permutations, to_letter_index_pairs(word), [])
        yield from variations
    return string_permutations_generator(max, word)

def to_letter_index_pairs(word):
    return [(word[i], i) for i in range(len(word))]

