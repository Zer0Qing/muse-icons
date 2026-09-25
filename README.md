# Muse Icons

为 [Muse](https://github.com/Zer0Qing/Muse) 设计的自有图标系统（rounded-geometric outline set）。

**24dp 栅格 · 1.7dp 圆头笔触 · 几何优先 · `currentColor` 自适应深浅主题**

> 状态：**全量完成 · 171 个图标**。覆盖 Muse 全部在用的图标语义（原 430 处引用去重后得出），后续仅随新功能增量补充。

## 预览

在线预览：<https://zer0qing.github.io/muse-icons/>（GitHub Pages）

或本地直接打开 [`docs/index.html`](docs/index.html)（深浅双色预览全部图标）。

## 使用

直接取 [`icons/`](icons) 下的 SVG 源文件，任意框架可用：

```html
<img src="icons/search.svg" width="24" height="24" alt="search">
```

颜色随 `currentColor`，在深浅主题中自动适配（可通过 CSS `color` 或 SVG `stroke` 覆盖）。

## 设计规范

| 项目 | 规格 |
| --- | --- |
| 网格 | 24 × 24，内容安全区 ≥ 2dp |
| 笔触 | 1.7dp，圆头端点与圆角连接（round cap / join） |
| 造型 | 几何优先：正圆、圆角矩形、45° 线；曲线克制 |
| 颜色 | `currentColor`，随主题自动着色 |
| 风格 | 线性（outline），无填充 |

## 目录结构

```
icons/        SVG 源文件（一图一文件）
icons.json    图标数据（唯一数据源）
docs/         预览页（深浅双色，GitHub Pages 指向此处）
scripts/      构建脚本
```

## 构建

```bash
python scripts/build.py
```

从 `icons.json` 重新生成 `icons/*.svg` 与 `docs/index.html`。

## 路线图

- [x] 第一批：核心图标（18）
- [x] 第二批：高频图标（49）
- [x] 第三批：工具 / 渠道 / 状态 / 品牌 / 长尾（104）——全量 171
- [ ] Compose ImageVector 生成器（Android）
- [ ] 图标字体（可选）
- [ ] 接入 Muse：替换现有 Material / Tabler 引用

## License

[MIT](LICENSE) © 2026 Zer0Qing
