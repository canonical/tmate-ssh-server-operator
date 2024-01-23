<!-- markdownlint-disable -->

<a href="../src/state.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `state.py`
tmate-ssh-server states. 

**Global Variables**
---------------
- **DEBUG_SSH_INTEGRATION_NAME**


---

## <kbd>class</kbd> `CharmConfigInvalidError`
Exception raised when a charm configuration is found to be invalid. 



**Attributes:**
 
 - <b>`msg`</b>:  Explanation of the error. 

<a href="../src/state.py#L42"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(msg: str)
```

Initialize a new instance of the CharmConfigInvalidError exception. 



**Args:**
 
 - <b>`msg`</b>:  Explanation of the error. 





---

## <kbd>class</kbd> `CharmStateBaseError`
Represents an error with charm state. 





---

## <kbd>class</kbd> `InvalidCharmStateError`
Represents an invalid charm state. 

<a href="../src/state.py#L26"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(reason: str)
```

Initialize the error. 



**Args:**
 
 - <b>`reason`</b>:  The reason why the state is invalid. 





---

## <kbd>class</kbd> `ProxyConfig`
Configuration for accessing Jenkins through proxy. 



**Attributes:**
 
 - <b>`http_proxy`</b>:  The http proxy URL. 
 - <b>`https_proxy`</b>:  The https proxy URL. 
 - <b>`no_proxy`</b>:  Comma separated list of hostnames to bypass proxy. 




---

<a href="../src/state.py#L64"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>classmethod</kbd> `from_env`

```python
from_env() → Optional[ForwardRef('ProxyConfig')]
```

Instantiate ProxyConfig from juju charm environment. 



**Returns:**
  ProxyConfig if proxy configuration is provided, None otherwise. 


---

## <kbd>class</kbd> `State`
The tmate-ssh-server operator charm state. 



**Attributes:**
 
 - <b>`ip_addr`</b>:  The host IP address of the given tmate-ssh-server unit. 
 - <b>`proxy_config`</b>:  The proxy configuration to apply to services used by tmate. 




---

<a href="../src/state.py#L94"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>classmethod</kbd> `from_charm`

```python
from_charm(charm: CharmBase) → State
```

Initialize the state from charm. 



**Args:**
 
 - <b>`charm`</b>:  The charm root TmateSSHServer charm. 



**Returns:**
 The current state of tmate-ssh-server charm. 



**Raises:**
 
 - <b>`InvalidCharmStateError`</b>:  if the network bind address was not of IPv4/IPv6. 
 - <b>`CharmConfigInvalidError`</b>:  if there was something wrong with charm configuration values. 


