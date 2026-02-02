<template>
  <div class="container">
    <h2>帮助与使用说明</h2>

    <section class="card">
      <h3>总体说明</h3>
      <ul>
        <li>协议提取工具是一个基于 Vue 3 与 Python 的 Web 应用，用于从协议文档中提取指定字段。</li>
      </ul>
    </section>

    <section class="card">
      <h3>使用流程</h3>
      <ol>
        <li>进入“字段配置”页面，维护协议字段与目标字段。</li>
        <li>进入“提取”页面：
          <ul>
            <li>选择需要提取的协议字段，或选择一个已保存的模板。</li>
            <li>如需复用选择，可输入模板名称并“保存为模板”。</li>
            <li>上传协议 Word 文档，点击“开始提取”，等待处理完成后下载结果。</li>
          </ul>
        </li>
        <li>处理中弹出“匹配”页面：用于处理模糊匹配，进行字段拖拽/映射。</li>
        <li>进入“知识库”页面：查看/维护知识库条目与统计。</li>
      </ol>
    </section>

    <section class="card">
      <h3>常见问题</h3>
      <ul>
        <li>字段列表为空：请先在“字段配置”页面新增字段。</li>
        <li>长时间无进度：可在首页仪表盘查看处理进度与输出日志</li>
      </ul>
    </section>
  </div>
</template>

<script setup lang="ts">
// 纯静态说明页，无需脚本逻辑
</script>

<style scoped>
ul, ol { padding-left: 20px; color: var(--text-main); }
li { margin-bottom: 8px; }
</style>
