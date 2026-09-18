# F-009 历史证据归档索引

此文件是历史过程证据的轻量入口。原始Git blob未被摘要化或丢弃，其完整字节流按换行边界保存在 `evidence.parts/`。

- 原始Git blob字节数：36,115,596
- 原始Git blob SHA256：`7faa58c14a36029de2864fc410fcfcdd6bfd2e15ee648ac4079141e708fba979`
- 机器索引：[evidence.index.json](evidence.index.json)
- 分片目录：[evidence.parts/](evidence.parts/)
- 重组方法：严格按照机器索引中的顺序，对所有分片执行原始字节连接。

离线完整性核验只能证明可无损重组；在独立敏感信息预检完成前，不得声明这些内容已经通过当前门禁。
