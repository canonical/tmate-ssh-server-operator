<!-- markdownlint-disable -->

<a href="../src/actions.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `actions.py`
tmate-ssh-server charm actions. 



---

## <kbd>class</kbd> `Observer`
Tmate-ssh-server charm actions observer. 

<a href="../src/actions.py#L18"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(charm: CharmBase, state: State)
```

Initialize the observer and register actions handlers. 



**Args:**
 
 - <b>`charm`</b>:  The parent charm to attach the observer to. 
 - <b>`state`</b>:  The charm state. 


---

#### <kbd>property</kbd> model

Shortcut for more simple access the model. 



---

<a href="../src/actions.py#L31"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `on_get_server_config`

```python
on_get_server_config(event: ActionEvent) → None
```

Get server configuration values for .tmate.conf. 



**Args:**
 
 - <b>`event`</b>:  The get-server-config action event. 


