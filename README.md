# proxy-config

[中文说明](README.zh-CN.md)

This repository stores configuration files for various proxy clients.

The `surge` directory is currently initialized, and an automated workflow is provided to:

- fetch OpenClash's `openclash_custom_fake_filter.list` every day
- convert it into a Surge Module `always-real-ip` configuration
- output it to `surge/fake-ip-filter.sgmodule`
