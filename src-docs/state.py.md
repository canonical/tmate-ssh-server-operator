<!-- markdownlint-disable -->

<a href="../src/state.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `state.py`
tmate-ssh-server states. 

**Global Variables**
---------------
- **DEBUG_SSH_INTEGRATION_NAME**


---

## <kbd>class</kbd> `State`
The tmate-ssh-server operator charm state. 



**Attributes:**
 
 - <b>`ip_addr`</b>:  The host IP address of the given tmate-ssh-server unit. 




---

<a href="../src/state.py#L24"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>classmethod</kbd> `from_charm`

```python
from_charm(charm: CharmBase) → State
```

Initialize the state from charm. 



**Args:**
 
 - <b>`charm`</b>:  The charm root TmateSSHServer charm. 



**Returns:**
 The current state of tmate-ssh-server charm. 


