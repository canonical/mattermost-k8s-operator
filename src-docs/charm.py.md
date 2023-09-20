<!-- markdownlint-disable -->

<a href="../src/charm.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `charm.py`




**Global Variables**
---------------
- **CONTAINER_PORT**
- **METRICS_PORT**
- **DATABASE_NAME**
- **LICENSE_SECRET_KEY_NAME**
- **REQUIRED_S3_SETTINGS**
- **REQUIRED_SETTINGS**
- **REQUIRED_SSO_SETTINGS**
- **SAML_IDP_CRT**

---

<a href="../src/charm.py#L47"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `check_ranges`

```python
check_ranges(ranges, name)
```

If ranges has one or more invalid elements, return a string describing the problem. 

ranges is a string containing a comma-separated list of CIDRs, a CIDR being the only kind of valid element. 


---

<a href="../src/charm.py#L63"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_container`

```python
get_container(pod_spec, container_name)
```

Find and return the first container in pod_spec whose name is container_name, otherwise return None. 


---

<a href="../src/charm.py#L71"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_env_config`

```python
get_env_config(pod_spec, container_name)
```

Return the envConfig of the container in pod_spec whose name is container_name, otherwise return None. 

If the container exists but has no envConfig, raise KeyError. 


---

## <kbd>class</kbd> `MattermostCharmEvents`
Custom charm events. 


---

#### <kbd>property</kbd> model

Shortcut for more simple access the model. 




---

## <kbd>class</kbd> `MattermostDBMasterAvailableEvent`








---

## <kbd>class</kbd> `MattermostK8sCharm`




<a href="../src/charm.py#L89"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(*args)
```






---

#### <kbd>property</kbd> app

Application that this unit is part of. 

---

#### <kbd>property</kbd> charm_dir

Root directory of the charm as it is running. 

---

#### <kbd>property</kbd> config

A mapping containing the charm's config and current values. 

---

#### <kbd>property</kbd> meta

Metadata of this charm. 

---

#### <kbd>property</kbd> model

Shortcut for more simple access the model. 

---

#### <kbd>property</kbd> unit

Unit that this execution is responsible for. 


---

#### <kbd>handler</kbd> on


---

<a href="../src/charm.py#L338"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `configure_pod`

```python
configure_pod(event)
```

Assemble the pod spec and apply it, if possible. 


