<!-- markdownlint-disable -->

<a href="../src/state.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `state.py`
tmate-ssh-server states. 

**Global Variables**
---------------
- **DEBUG_SSH_INTEGRATION_NAME**


---

## <kbd>class</kbd> `CharmStateBaseError`
Represents an error with charm state. 





---

## <kbd>class</kbd> `InvalidCharmStateError`
Represents an invalid charm state. 

<a href="../src/state.py#L21"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(reason: str)
```

Initialize the error. 



**Args:**
 
 - <b>`reason`</b>:  The reason why the state is invalid. 





---

## <kbd>class</kbd> `State`
The tmate-ssh-server operator charm state. 



**Attributes:**
 
 - <b>`ip_addr`</b>:  The host IP address of the given tmate-ssh-server unit. 




---

<a href="../src/state.py#L40"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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


