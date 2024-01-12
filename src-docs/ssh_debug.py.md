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

<a href="../src/ssh_debug.py#L18"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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




