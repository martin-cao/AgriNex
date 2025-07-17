<template>
  <div class="media-gallery">
    <el-card class="header-card">
      <div class="header-content">
        <h2>📸 媒体库</h2>
        <p>管理和查看农业监控中的图片和视频资料</p>
      </div>
    </el-card>

    <!-- 上传区域 -->
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <span>上传媒体文件</span>
        </div>
      </template>
      
      <el-upload
        class="upload-demo"
        :action="uploadUrl"
        :headers="uploadHeaders"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
        :file-list="fileList"
        list-type="picture-card"
        accept="image/*,video/*"
        multiple
      >
        <el-icon class="el-icon--upload">
          <upload-filled />
        </el-icon>
        <div class="el-upload__text">
          点击上传或拖拽文件到此处
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持jpg/png/gif/mp4/mov格式，单个文件大小不超过10MB
          </div>
        </template>
      </el-upload>
    </el-card>

    <!-- 筛选和搜索 -->
    <el-card class="filter-card">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-select v-model="filterType" placeholder="文件类型" @change="fetchMedia">
            <el-option label="全部" value="" />
            <el-option label="图片" value="image" />
            <el-option label="视频" value="video" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            @change="fetchMedia"
          />
        </el-col>
        <el-col :span="8">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索文件名..."
            @keyup.enter="fetchMedia"
          >
            <template #prefix>
              <el-icon><search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="fetchMedia">
            搜索
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 媒体网格 -->
    <el-card class="media-grid-card">
      <template #header>
        <div class="card-header">
          <span>媒体文件 ({{ mediaFiles.length }})</span>
          <div class="view-controls">
            <el-radio-group v-model="viewMode" @change="handleViewModeChange">
              <el-radio-button label="grid">
                <el-icon><grid /></el-icon>
              </el-radio-button>
              <el-radio-button label="list">
                <el-icon><list /></el-icon>
              </el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>
      
      <!-- 网格视图 -->
      <div v-if="viewMode === 'grid'" class="media-grid">
        <div
          v-for="file in mediaFiles"
          :key="file.id"
          class="media-item"
          @click="openPreview(file)"
        >
          <div class="media-preview">
            <img
              v-if="file.file_type === 'image'"
              :src="file.thumbnail_url || file.url"
              :alt="file.original_filename"
              class="media-thumbnail"
            />
            <div v-else class="video-preview">
              <video :src="file.url" class="media-thumbnail" preload="metadata" />
              <div class="video-overlay">
                <el-icon class="play-icon"><video-play /></el-icon>
              </div>
            </div>
          </div>
          <div class="media-info">
            <div class="media-name" :title="file.original_filename">{{ file.original_filename }}</div>
            <div class="media-meta">
              <span class="file-size">{{ formatFileSize(file.file_size) }}</span>
              <span class="upload-date">{{ formatDate(file.created_at) }}</span>
            </div>
          </div>
          <div class="media-actions">
            <el-button type="primary" size="small" @click.stop="downloadFile(file)">
              <el-icon><download /></el-icon>
            </el-button>
            <el-button type="danger" size="small" @click.stop="deleteFile(file)">
              <el-icon><delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
      
      <!-- 列表视图 -->
      <el-table v-else :data="mediaFiles" style="width: 100%">
        <el-table-column label="预览" width="80">
          <template #default="scope">
            <div class="table-preview" @click="openPreview(scope.row)">
              <img
                v-if="scope.row.file_type === 'image'"
                :src="scope.row.thumbnail_url || scope.row.url"
                :alt="scope.row.original_filename"
                class="table-thumbnail"
              />
              <div v-else class="video-icon">
                <el-icon><video-play /></el-icon>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="original_filename" label="文件名" />
        <el-table-column prop="mime_type" label="类型" width="120" />
        <el-table-column prop="file_size" label="大小" width="100">
          <template #default="scope">
            {{ formatFileSize(scope.row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button type="text" size="small" @click="openPreview(scope.row)">
              预览
            </el-button>
            <el-button type="text" size="small" @click="downloadFile(scope.row)">
              下载
            </el-button>
            <el-button type="text" size="small" @click="deleteFile(scope.row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 预览对话框 -->
    <el-dialog
      v-model="previewVisible"
      :title="currentFile?.original_filename"
      width="80%"
      @close="closePreview"
    >
      <div class="preview-content">
        <img
          v-if="currentFile && currentFile.file_type === 'image'"
          :src="currentFile.url"
          :alt="currentFile.original_filename"
          class="preview-image"
        />
        <video
          v-else-if="currentFile && currentFile.file_type === 'video'"
          :src="currentFile.url"
          class="preview-video"
          controls
        />
      </div>
      <div class="preview-info">
        <p><strong>文件名:</strong> {{ currentFile?.original_filename }}</p>
        <p><strong>类型:</strong> {{ currentFile?.mime_type }}</p>
        <p><strong>大小:</strong> {{ formatFileSize(currentFile?.file_size || 0) }}</p>
        <p><strong>上传时间:</strong> {{ formatDate(currentFile?.created_at || '') }}</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  UploadFilled,
  Search,
  Grid,
  List,
  VideoPlay,
  Download,
  Delete
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { mediaApi } from '@/api'
import { formatDate, formatFileSize } from '@/utils'
import type { MediaFile } from '@/api/media'

const authStore = useAuthStore()

// 响应式数据
const mediaFiles = ref<MediaFile[]>([])
const fileList = ref([])
const loading = ref(false)
const viewMode = ref('grid')
const filterType = ref('')
const searchKeyword = ref('')
const dateRange = ref<[Date, Date] | null>(null)
const previewVisible = ref(false)
const currentFile = ref<MediaFile | null>(null)

// 上传配置
const uploadUrl = computed(() => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api'
  return `${baseUrl}/media/upload/`
})
const uploadHeaders = computed(() => ({
  'Authorization': `Bearer ${authStore.token}`
}))

// 获取媒体文件列表
const fetchMedia = async () => {
  loading.value = true
  try {
    const params: any = {}
    
    if (filterType.value) {
      params.file_type = filterType.value
    }
    
    if (dateRange.value) {
      params.start_date = dateRange.value[0].toISOString().split('T')[0]
      params.end_date = dateRange.value[1].toISOString().split('T')[0]
    }
    
    const response = await mediaApi.getMediaFiles(params)
    
    if (response.success) {
      let filteredData = response.data || []
      
      // 应用搜索关键词筛选
      if (searchKeyword.value) {
        filteredData = filteredData.filter(file => 
          file.original_filename.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
          file.filename.toLowerCase().includes(searchKeyword.value.toLowerCase())
        )
      }
      
      mediaFiles.value = filteredData
    } else {
      ElMessage.error('获取媒体文件失败')
    }
  } catch (error: any) {
    console.error('获取媒体文件失败:', error)
    // 如果API不存在，显示模拟数据
    if (error.response?.status === 404) {
      ElMessage.warning('媒体API暂不可用，显示模拟数据')
      mediaFiles.value = getMockData()
    } else {
      ElMessage.error('获取媒体文件失败')
    }
  } finally {
    loading.value = false
  }
}

// 模拟数据
const getMockData = (): MediaFile[] => {
  return [
    {
      id: 1,
      filename: 'farm_monitoring_20240101.jpg',
      original_filename: '农田监控-2024-01-01.jpg',
      file_type: 'image',
      file_size: 1024000,
      mime_type: 'image/jpeg',
      url: 'https://picsum.photos/800/600?random=1',
      thumbnail_url: 'https://picsum.photos/200/200?random=1',
      device_id: 1,
      sensor_id: 1,
      created_at: '2024-01-01T10:00:00Z',
      updated_at: '2024-01-01T10:00:00Z'
    },
    {
      id: 2,
      filename: 'irrigation_system_20240102.mp4',
      original_filename: '灌溉系统视频.mp4',
      file_type: 'video',
      file_size: 5048000,
      mime_type: 'video/mp4',
      url: 'https://www.w3schools.com/html/mov_bbb.mp4',
      device_id: 2,
      created_at: '2024-01-02T14:30:00Z',
      updated_at: '2024-01-02T14:30:00Z'
    },
    {
      id: 3,
      filename: 'crop_growth_20240103.jpg',
      original_filename: '作物生长记录.jpg',
      file_type: 'image',
      file_size: 856000,
      mime_type: 'image/jpeg',
      url: 'https://picsum.photos/800/600?random=2',
      thumbnail_url: 'https://picsum.photos/200/200?random=2',
      device_id: 3,
      sensor_id: 3,
      created_at: '2024-01-03T09:15:00Z',
      updated_at: '2024-01-03T09:15:00Z'
    }
  ]
}

// 文件上传前验证
const beforeUpload = (file: File) => {
  const isValidType = file.type.startsWith('image/') || file.type.startsWith('video/')
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isValidType) {
    ElMessage.error('只能上传图片或视频文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB!')
    return false
  }
  return true
}

// 上传成功处理
const handleUploadSuccess = (response: any, file: any) => {
  if (response.success) {
    ElMessage.success('文件上传成功')
    fetchMedia()
  } else {
    ElMessage.error('文件上传失败: ' + (response.message || '未知错误'))
  }
}

// 上传失败处理
const handleUploadError = (error: any) => {
  console.error('上传失败:', error)
  ElMessage.error('文件上传失败')
}

// 切换视图模式
const handleViewModeChange = (mode: string) => {
  viewMode.value = mode
}

// 打开预览
const openPreview = (file: MediaFile) => {
  currentFile.value = file
  previewVisible.value = true
}

// 关闭预览
const closePreview = () => {
  previewVisible.value = false
  currentFile.value = null
}

// 下载文件
const downloadFile = (file: MediaFile) => {
  const link = document.createElement('a')
  link.href = file.url
  link.download = file.original_filename
  link.click()
  ElMessage.success('文件下载已开始')
}

// 删除文件
const deleteFile = async (file: MediaFile) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件 "${file.original_filename}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    try {
      await mediaApi.deleteMediaFile(file.id)
      ElMessage.success('文件删除成功')
      fetchMedia()
    } catch (error) {
      console.error('删除文件失败:', error)
      ElMessage.error('删除文件失败')
    }
  } catch (error) {
    // 取消删除
  }
}

onMounted(() => {
  fetchMedia()
})
</script>

<style scoped>
.media-gallery {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.header-content {
  text-align: center;
}

.header-content h2 {
  margin: 0 0 10px 0;
  color: var(--agrinex-text-primary);
}

.header-content p {
  margin: 0;
  color: var(--agrinex-text-secondary);
}

.upload-card,
.filter-card,
.media-grid-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.view-controls {
  display: flex;
  align-items: center;
}

.upload-demo {
  width: 100%;
}

.media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.media-item {
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.media-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.media-preview {
  position: relative;
  width: 100%;
  height: 180px;
  overflow: hidden;
}

.media-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-preview {
  position: relative;
  width: 100%;
  height: 100%;
}

.video-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.play-icon {
  color: white;
  font-size: 24px;
}

.media-info {
  padding: 12px;
}

.media-name {
  font-weight: bold;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.media-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
}

.media-actions {
  padding: 8px 12px;
  display: flex;
  gap: 8px;
  border-top: 1px solid #eee;
}

.table-preview {
  width: 50px;
  height: 50px;
  cursor: pointer;
}

.table-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 4px;
}

.video-icon {
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 4px;
}

.preview-content {
  text-align: center;
  margin-bottom: 20px;
}

.preview-image {
  max-width: 100%;
  max-height: 60vh;
  object-fit: contain;
}

.preview-video {
  max-width: 100%;
  max-height: 60vh;
}

.preview-info {
  background: #f9f9f9;
  padding: 15px;
  border-radius: 4px;
}

.preview-info p {
  margin: 5px 0;
}

.el-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}
</style>
