# proxy-config

[中文说明](README.zh-CN.md)

This repository stores configuration files for various proxy clients.

The `surge` directory stores Surge-related configuration artifacts.

- `surge/fake-ip-filter.sgmodule`: a generated Surge Module that appends entries to `always-real-ip`

The `config` directory contains the INI configuration for the Subconverter:

- `base/`: Basic configuration
  - `normal.ini`: keeps inline rules in their regular form and does not add `no-resolve`
  - `noresolve.ini`: adds `no-resolve` to inline rules that may trigger local DNS resolution, to reduce unnecessary local lookups
- `surge/`, `shadowrocket/`, `clash/`: generated client-specific outputs

## jsDelivr Links

The following files can be accessed through `https://testingcf.jsdelivr.net/gh/smallmain/proxy-config@main`:

### `surge/*.sgmodule`

```text
surge/fake-ip-filter.sgmodule
https://testingcf.jsdelivr.net/gh/smallmain/proxy-config@main/surge/fake-ip-filter.sgmodule
```

### `config/surge/*.ini`

```text
config/surge/normal.ini
https://testingcf.jsdelivr.net/gh/smallmain/proxy-config@main/config/surge/normal.ini

config/surge/noresolve.ini
https://testingcf.jsdelivr.net/gh/smallmain/proxy-config@main/config/surge/noresolve.ini
```

### `config/shadowrocket/*.ini`

```text
config/shadowrocket/normal.ini
https://testingcf.jsdelivr.net/gh/smallmain/proxy-config@main/config/shadowrocket/normal.ini

config/shadowrocket/noresolve.ini
https://testingcf.jsdelivr.net/gh/smallmain/proxy-config@main/config/shadowrocket/noresolve.ini
```

### `shadowrocket/*.conf`

```text
shadowrocket/base.conf
https://testingcf.jsdelivr.net/gh/smallmain/proxy-config@main/shadowrocket/base.conf

shadowrocket/normal.conf
https://testingcf.jsdelivr.net/gh/smallmain/proxy-config@main/shadowrocket/normal.conf

shadowrocket/noresolve.conf
https://testingcf.jsdelivr.net/gh/smallmain/proxy-config@main/shadowrocket/noresolve.conf
```

### `config/clash/*.ini`

```text
config/clash/normal.ini
https://testingcf.jsdelivr.net/gh/smallmain/proxy-config@main/config/clash/normal.ini

config/clash/noresolve.ini
https://testingcf.jsdelivr.net/gh/smallmain/proxy-config@main/config/clash/noresolve.ini
```
