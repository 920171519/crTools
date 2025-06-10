<script setup lang="ts">
// 应用主组件
</script>

<template>
  <div id="app">
    <router-view />
  </div>
</template>

<style>
#app {
  width: 100vw;
  /* width: 100%; */
  height: 100vh;
  max-width: 100%;
}

/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  background-color: #f5f5f5;
  color: #303133;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-thumb {
  background-color: #ddd;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background-color: #ccc;
}

::-webkit-scrollbar-track {
  background-color: transparent;
}

/* Element Plus 样式调整 */
.el-menu {
  border-right: none !important;
}

.el-main {
  padding: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .el-main {
    padding: 10px;
  }
}
</style>
