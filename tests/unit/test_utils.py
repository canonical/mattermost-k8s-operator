# Copyright 2020 Canonical Ltd.
# Licensed under the GPLv3, see LICENCE file for details.

import unittest
from copy import deepcopy

from utils import extend_list_merging_dicts_matched_by_key


class TestExtendListMergingDictsByKey(unittest.TestCase):
    def test_nothing(self):
        """Nothing in, nothing out."""
        self.assertEqual(extend_list_merging_dicts_matched_by_key([], [], key=None), [])

    def test_same(self):
        """Identity."""
        self.assertEqual(
            extend_list_merging_dicts_matched_by_key([{1: 1}], [{1: 1}], key=1), [{1: 1}]
        )

    def test_different(self):
        """Colleagues."""
        self.assertEqual(
            extend_list_merging_dicts_matched_by_key([{1: 2}], [{1: 1}], key=1), [{1: 1}, {1: 2}]
        )

    def test_merge_same_key(self):
        """Now this is what we came here for!"""
        self.assertEqual(
            extend_list_merging_dicts_matched_by_key([{1: 1, 3: 4}], [{1: 1, 2: 3}], key=1),
            [{1: 1, 2: 3, 3: 4}],
        )

    def test_merge_same_key_different_key(self):
        """A little of this, a little of that."""
        self.assertEqual(
            extend_list_merging_dicts_matched_by_key(
                [{1: 1, 3: 4}], [{1: 1, 2: 3}, {1: 2, 5: 6}, {1: 3, 7: 8}], key=1
            ),
            [{1: 2, 5: 6}, {1: 3, 7: 8}, {1: 1, 2: 3, 3: 4}],
        )

    def test_merge_same_key_different_key_deepcopy(self):
        """Merge targets are deep-copied beforehand."""
        d = [{1: 1, 3: 4}]
        dc = deepcopy(d)
        s = [{1: 1, 2: 3}, {1: 2, 5: 6}, {1: 3, 7: 8}]
        # Make sure it did something...
        self.assertNotEqual(extend_list_merging_dicts_matched_by_key(d, s, key=1), d)
        # ...but without altering d.
        self.assertEqual(d, dc)
