<!-- markdownlint-disable -->

<a href="../src/ssh_debug.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `ssh_debug.py`
Observer module for ssh-debug integration. 

**Global Variables**
---------------
- **DEBUG_SSH_INTEGRATION_NAME**


---

## <kbd>class</kbd> `Observer`
The ssh-debug integration observer. 

<a href="../src/ssh_debug.py#L19"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(charm: CharmBase, state: State)
```

Initialize the observer and register event handlers. 



**Args:**
 
 - <b>`charm`</b>:  The parent charm to attach the observer to. 
 - <b>`state`</b>:  The charm state. 


---

#### <kbd>property</kbd> model

Shortcut for more simple access the model. 



---

<a href="../src/ssh_debug.py#L35"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `update_relation_data`

```python
update_relation_data(host: str, fingerprints: Fingerprints) → None
```

Update ssh_debug relation data if relation is available. 



**Args:**
 
 - <b>`host`</b>:  The unit's bound IP address. 
 - <b>`fingerprints`</b>:  The tmate-ssh-server generated fingerprint for RSA and ED25519 keys. 


