# proxy-config

[English README](README.md)

这个仓库用于存放各类代理软件的配置文件。

`surge` 目录用于存放 Surge 相关配置产物。

- `surge/fake-ip-filter.sgmodule`：一个生成得到的 Surge Module，用于向 `always-real-ip` 追加条目

`config` 目录提供 Subconverter 的 INI 配置：

- `base/`：基础配置
  - `normal.ini`：常规写法
  - `noresolve.ini`：为可能触发本地 DNS 解析的规则追加 `no-resolve`，以减少不必要的本地解析
- `surge/`、`shadowrocket/`、`clash/`：生成后的客户端配置

## jsDelivr 访问链接

以下文件可通过 `https://testingcf.jsdelivr.net/gh/smallmain/proxy-config@main` 访问：

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
