<!-- markdownlint-disable -->

<a href="../src/utils.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `utils.py`





---

<a href="../src/utils.py#L7"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `extend_list_merging_dicts_matched_by_key`

```python
extend_list_merging_dicts_matched_by_key(dst, src, key)
```

Merge src, a list of zero or more dictionaries, into dst, also such a list.  Dictionaries with the same key will be copied from dst and then merged using .update(src).  This is not done recursively. 


