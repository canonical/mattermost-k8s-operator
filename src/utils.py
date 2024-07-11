# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

from copy import deepcopy


def extend_list_merging_dicts_matched_by_key(dst, src, key):
    """Merge src, a list of zero or more dictionaries, into dst, also
    such a list.  Dictionaries with the same key will be copied from dst
    and then merged using .update(src).  This is not done recursively."""
    result = []
    sbk = {s[key]: s for s in src}
    dbk = {d[key]: d for d in dst}
    to_merge = set(dbk.keys()).intersection(sbk.keys())
    result.extend([s for s in src if s[key] not in to_merge])
    result.extend([d for d in dst if d[key] not in to_merge])
    for k in sorted(to_merge):
        result.append(deepcopy(dbk[k]))
        result[-1].update(sbk[k])
    return result
