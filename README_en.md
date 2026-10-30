# BotQraftReforged

[中文](README.md) | **English**

> A framework for developing official QQ bots, built on [MCDReforged](https://github.com/MCDReforged/MCDReforged).

BotQraftReforged builds on MCDR's plugin development, command management, permission management, and other capabilities. You can develop BotQraft plugins much like MCDR plugins, using message and event interfaces designed for QQ.

“Reforged” describes BotQraft as a reforging of MCDR and expresses our appreciation for MCDR's design. The distribution name, Python import namespace, and command-line entry point are all `botqraft`.

## Features

- Runs independently using the official QQ bot Gateway and HTTP API, supporting group chats and C2C.
- Reuses MCDR's plugin lifecycle, command trees, permissions, and translations.
- Provides QQ interfaces for passive replies, text, Markdown, keyboards, and command panels.
- Supports single-file, directory, and packed plugins for development and distribution.

Requires **Python 3.10 or later**. MCDR 2.16.2 is a code dependency, not the runtime host; no Minecraft server is required.

## Documentation

Check out the full documentation at [https://botqraft.tanh.moe/](https://botqraft.tanh.moe/).
