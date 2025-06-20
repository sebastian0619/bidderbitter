<!-- 通用数据表格组件 -->
<template>
  <div class="data-table-container">
    <!-- 表格工具栏 -->
    <div v-if="showToolbar" class="table-toolbar">
      <div class="toolbar-left">
        <el-input
          v-if="searchable"
          v-model="searchText"
          placeholder="搜索..."
          style="width: 200px"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <slot name="toolbar-left" />
      </div>
      
      <div class="toolbar-right">
        <slot name="toolbar-right" />
        
        <el-button
          v-if="refreshable"
          circle
          @click="handleRefresh"
        >
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>
    
    <!-- 数据表格 -->
    <el-table
      ref="tableRef"
      v-loading="loading"
      :data="filteredData"
      :height="height"
      :max-height="maxHeight"
      :stripe="stripe"
      :border="border"
      :size="size"
      :default-sort="defaultSort"
      :empty-text="emptyText"
      style="width: 100%"
      @selection-change="handleSelectionChange"
      @sort-change="handleSortChange"
      @row-click="handleRowClick"
      @row-dblclick="handleRowDblClick"
    >
      <!-- 选择列 -->
      <el-table-column
        v-if="selectable"
        type="selection"
        width="55"
        :selectable="selectableFunction"
      />
      
      <!-- 动态列 -->
      <template v-for="column in columns" :key="column.prop">
        <el-table-column
          :prop="column.prop"
          :label="column.label"
          :width="column.width"
          :min-width="column.minWidth"
          :fixed="column.fixed"
          :sortable="column.sortable"
          :show-overflow-tooltip="column.showTooltip !== false"
          :align="column.align || 'left'"
        >
          <template v-if="column.slot" #default="scope">
            <slot :name="column.slot" v-bind="scope" />
          </template>
          
          <template v-else-if="column.formatter" #default="scope">
            <span v-html="column.formatter(scope.row, scope.column, scope.row[column.prop], scope.$index)" />
          </template>
        </el-table-column>
      </template>
      
      <!-- 操作列 -->
      <el-table-column
        v-if="showActions"
        label="操作"
        :width="actionWidth"
        :fixed="actionFixed"
        align="center"
      >
        <template #default="scope">
          <slot name="actions" v-bind="scope">
            <el-button
              type="primary"
              size="small"
              text
              @click="handleEdit(scope.row, scope.$index)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              text
              @click="handleDelete(scope.row, scope.$index)"
            >
              删除
            </el-button>
          </slot>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页器 -->
    <div v-if="pageable && totalCount > 0" class="table-pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="pageSizes"
        :total="totalCount"
        :layout="paginationLayout"
        :background="true"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'

const props = defineProps({
  // 表格数据
  data: {
    type: Array,
    default: () => []
  },
  // 表格列配置
  columns: {
    type: Array,
    default: () => []
  },
  // 是否显示工具栏
  showToolbar: {
    type: Boolean,
    default: true
  },
  // 是否支持搜索
  searchable: {
    type: Boolean,
    default: true
  },
  // 是否支持刷新
  refreshable: {
    type: Boolean,
    default: true
  },
  // 是否显示操作列
  showActions: {
    type: Boolean,
    default: true
  },
  // 操作列宽度
  actionWidth: {
    type: [String, Number],
    default: 150
  },
  // 操作列是否固定
  actionFixed: {
    type: String,
    default: 'right'
  },
  // 是否支持选择
  selectable: {
    type: Boolean,
    default: false
  },
  // 选择函数
  selectableFunction: {
    type: Function,
    default: null
  },
  // 是否支持分页
  pageable: {
    type: Boolean,
    default: true
  },
  // 总记录数
  totalCount: {
    type: Number,
    default: 0
  },
  // 分页布局
  paginationLayout: {
    type: String,
    default: 'total, sizes, prev, pager, next, jumper'
  },
  // 分页大小选项
  pageSizes: {
    type: Array,
    default: () => [10, 20, 50, 100]
  },
  // 表格高度
  height: {
    type: [String, Number],
    default: null
  },
  // 表格最大高度
  maxHeight: {
    type: [String, Number],
    default: null
  },
  // 是否显示斑马纹
  stripe: {
    type: Boolean,
    default: true
  },
  // 是否显示边框
  border: {
    type: Boolean,
    default: true
  },
  // 表格尺寸
  size: {
    type: String,
    default: 'default'
  },
  // 默认排序
  defaultSort: {
    type: Object,
    default: null
  },
  // 空数据文案
  emptyText: {
    type: String,
    default: '暂无数据'
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'search',
  'refresh',
  'selection-change',
  'sort-change',
  'row-click',
  'row-dblclick',
  'edit',
  'delete',
  'page-change',
  'size-change'
])

const tableRef = ref(null)
const searchText = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

// 过滤后的数据
const filteredData = computed(() => {
  if (!searchText.value || !props.searchable) {
    return props.data
  }
  
  const keyword = searchText.value.toLowerCase()
  return props.data.filter(row => {
    return props.columns.some(column => {
      const value = row[column.prop]
      return value && String(value).toLowerCase().includes(keyword)
    })
  })
})

// 监听页码变化
watch([currentPage, pageSize], () => {
  emit('page-change', {
    page: currentPage.value,
    size: pageSize.value
  })
})

// 方法
const handleSearch = (value) => {
  emit('search', value)
}

const handleRefresh = () => {
  emit('refresh')
}

const handleSelectionChange = (selection) => {
  emit('selection-change', selection)
}

const handleSortChange = (sortInfo) => {
  emit('sort-change', sortInfo)
}

const handleRowClick = (row, column, event) => {
  emit('row-click', row, column, event)
}

const handleRowDblClick = (row, column, event) => {
  emit('row-dblclick', row, column, event)
}

const handleEdit = (row, index) => {
  emit('edit', row, index)
}

const handleDelete = async (row, index) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条记录吗？',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    emit('delete', row, index)
  } catch {
    // 用户取消删除
  }
}

const handleSizeChange = (size) => {
  pageSize.value = size
  emit('size-change', size)
}

const handleCurrentChange = (page) => {
  currentPage.value = page
}

// 暴露方法给父组件
const clearSelection = () => {
  tableRef.value?.clearSelection()
}

const toggleRowSelection = (row, selected) => {
  tableRef.value?.toggleRowSelection(row, selected)
}

const toggleAllSelection = () => {
  tableRef.value?.toggleAllSelection()
}

const setCurrentRow = (row) => {
  tableRef.value?.setCurrentRow(row)
}

const clearSort = () => {
  tableRef.value?.clearSort()
}

const doLayout = () => {
  tableRef.value?.doLayout()
}

defineExpose({
  clearSelection,
  toggleRowSelection,
  toggleAllSelection,
  setCurrentRow,
  clearSort,
  doLayout,
  currentPage,
  pageSize
})
</script>

<style lang="scss" scoped>
.data-table-container {
  .table-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    .toolbar-left,
    .toolbar-right {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }
  
  .table-pagination {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
}

@media (max-width: 768px) {
  .data-table-container {
    .table-toolbar {
      flex-direction: column;
      align-items: stretch;
      gap: 12px;
      
      .toolbar-left,
      .toolbar-right {
        justify-content: center;
      }
    }
    
    .table-pagination {
      justify-content: center;
    }
  }
}
</style> 