from unittest import TestCase, main
from string_permutations import string_permutations

class TestFindVariations(TestCase):
    string_permutations = string_permutations(10)
    def test_should_find_string_permutations_of_at(self):
        variations = list(self.string_permutations('at'))
        self.assertListEqual(variations, ['at', 'ta'])

    def test_should_find_string_permutations_of_the(self):
        variations = list(self.string_permutations('the'))
        
        self.assertListEqual(
            variations, ['the', 'teh', 'hte', 'het', 'eth', 'eht'])

if __name__ == '__main__':
    main()
