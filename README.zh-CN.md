# mdoutline

**Markdown 章节文件 → 一份带精确大纲书签的可印刷 PDF。**

给它一个装着 `*.md` 章节文件的目录：它把章节拼成一份带样式的 HTML（封面、可点击目录、页眉页脚），用 Chromium 引擎打印成 PDF，并写入 PDF 大纲——每个标题都会出现在 PDF 阅读器的书签面板里，且**按构造保证落在正确的页上**。

## 为什么需要它

Chromium 的打印到 PDF 会丢掉文档大纲：产出的 PDF 没有书签。常见补救办法是按字号反猜标题页码，分页一漂移就失效。

mdoutline 走了另一条路：渲染出的目录由内部超链接组成，Chromium 打印时会把每个链接解析成具体页码。写书签的步骤只是把这些 GoTo 链接标注从 PDF 里读回来——每个标题的目标页本来就存在文件里，因此书签位置精确、不受字体与分页变化影响。只有未进目录的标题才回退到字号启发式。

默认主题开箱即用地支持中英混排（正文衬线、标题无衬线、面向打印的表格与代码块），纯西文文档同样适用。

## 安装

需要 Python 3.10+。

```bash
pip install mdoutline            # 从源码安装：pip install -e .
playwright install chromium      # 一次性浏览器下载（约 170 MB）
```

想用本机已有的 Chrome/Chromium/Edge 而不是内置浏览器：

```bash
export MDOUTLINE_BROWSER="/path/to/chrome"
```

## 快速上手

```bash
mdoutline make examples/demo -o demo.pdf
```

一本"书"就是一个按文件名排序的章节目录，外加可选的 `book.toml`：

```
mybook/
  book.toml
  chapters/
    01-绪论.md
    02-方法.md
    03-结果.md
```

运行 `mdoutline make mybook/chapters -o mybook.pdf`（或在 `mybook/` 下直接
`mdoutline make chapters`）。一条命令原子地跑完三个阶段：重新渲染不可能
留下一份丢书签的 PDF。

## 配置（book.toml）

所有键放在 `[book]` 下，全部可选。各键含义与默认值见 [README.md](README.md)
的 Configuration 一节（键名与英文版完全一致）：标题/副标题/作者/日期/摘要、
`lang`、`cover`、`toc_title`、页眉页脚模板（支持 `{title}` `{subtitle}`
`{page}` `{pages}` 占位符）、`page_format`、四边页距（mm）、`css` 追加样式、
`browser_path`、`settle_ms` 等待时间。

## 命令

```
mdoutline make SRC [-o OUT.pdf] [--config book.toml] [--keep-html]
    拼接 + 打印 + 书签，一次原子完成

mdoutline build SRC [-o OUT.html] [--config book.toml]
    章节 → 带样式 HTML（封面、目录、节锚点）

mdoutline render IN.html [-o OUT.pdf] [--config book.toml]
    HTML → PDF（不写书签）

mdoutline bookmarks IN.pdf --html IN.html
    给已有 PDF 写入大纲书签
```

## 标题锚点规则

数字编号标题保留可读锚点：`# 7 标题` → `sec-7`、`## 7.9 小节` →
`sec-7-9`，跨章链接写 `[见 7.9](#sec-7-9)` 即可。其他标题生成 slug 锚点。
若两个标题生成了相同锚点（例如小节号重复），第二个自动加 `-2` 后缀并在
stderr 打警告——重复编号从"悄悄劫持目录链接"降级为"提醒你改编号"。

## 依赖与协议

mdoutline 本体采用 MIT 协议，不含任何第三方代码拷贝。运行时依赖四个
PyPI 包（安装时各自拉取）：

| 包 | 协议 | 作用 |
|---|---|---|
| markdown | BSD-3-Clause | Markdown → HTML |
| pymdown-extensions | MIT | `~~删除线~~` 标记 |
| playwright | Apache-2.0 | 驱动 Chromium 打印引擎 |
| pymupdf | **AGPL-3.0** | 读目录链接标注、写大纲书签 |

需要留意的是 PyMuPDF：它本身是 AGPL-3.0（Artifex 提供商业授权）。本地
运行 mdoutline 生成自己的 PDF 不分发任何东西，不触发 AGPL 义务；但若把
mdoutline **连同依赖打包分发**（容器镜像、冻结应用），该分发在 PyMuPDF
环节受 AGPL 条款约束，基于此类打包的网络服务还会落入 AGPL 的源码披露
条款。若需要彻底消除该注意点，欢迎贡献一个宽松协议的 PDF 后端。

## 开发

```bash
pip install -e .
python tests/test_smoke.py    # 端到端：构建示例书并逐个检查书签落页
```

## 协议

[MIT](LICENSE)
