<!-- markdownlint-disable -->

<a href="../src/environment.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `environment.py`
Generate container app environment based on charm configuration. 

**Global Variables**
---------------
- **CONTAINER_PORT**
- **METRICS_PORT**
- **REQUIRED_S3_SETTINGS**
- **REQUIRED_SETTINGS**
- **REQUIRED_SSO_SETTINGS**
- **SAML_IDP_CRT**
- **CANONICAL_DEFAULTS**

---

<a href="../src/environment.py#L180"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `missing_config_settings`

```python
missing_config_settings(config: dict) → Iterable[str]
```

Return a list of settings required to satisfy configuration dependencies. 



**Args:**
 
 - <b>`config`</b>:  dict of the charm's configuration 



**Returns:**
 a list of settings required to satisfy configuration dependencies. 


---

<a href="../src/environment.py#L208"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `generate`

```python
generate(config: dict, app_name: str, site_url: str, db_uri: str) → dict
```

Generate container app environment based on charm configuration. 



**Args:**
 
 - <b>`config`</b>:  dict of the charm's configuration 
 - <b>`app_name`</b>:  name of the app 
 - <b>`site_url`</b>:  public facing URL of mattermost 
 - <b>`db_uri`</b>:  URI of the psql database 



**Returns:**
 dict of container app environment. 


