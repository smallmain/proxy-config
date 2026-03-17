# proxy-config

[English README](README.md)

这个仓库用于存放各类代理软件的配置文件。

当前已初始化 `surge` 目录，并提供一个自动化流程：

- 每天拉取 OpenClash 的 `openclash_custom_fake_filter.list`
- 转换为 Surge Module 的 `always-real-ip` 配置
- 输出到 `surge/fake-ip-filter.sgmodule`
