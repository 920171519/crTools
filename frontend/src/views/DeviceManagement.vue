<template>
  <div class="device-management">
    <div class="page-header">
      <h1>设备管理</h1>
      <p>管理和监控Linux设备的使用情况</p>
    </div>

    <!-- 调试信息 -->
    <!-- <el-card v-if="true" style="margin-bottom: 20px;">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>调试信息</span>
          <el-button size="small" @click="refreshUserInfo">刷新用户信息</el-button>
        </div>
      </template>
      <div>
        <p><strong>当前用户角色:</strong> {{ currentUserRole }}</p>
        <p><strong>用户信息:</strong> {{ userStore.userInfo }}</p>
        <p><strong>isNormalUser:</strong> {{ isNormalUser }}</p>
        <p><strong>isAdvancedUserOnly:</strong> {{ isAdvancedUserOnly }}</p>
        <p><strong>isAdminOrSuper:</strong> {{ isAdminOrSuper }}</p>
        <p><strong>Store isAdvancedUser:</strong> {{ userStore.isAdvancedUser }}</p>
        <p><strong>Store isAdminUser:</strong> {{ userStore.isAdminUser }}</p>
      </div>
    </el-card> -->

    <!-- 搜索栏 -->
    <el-card shadow="never" style="margin-bottom: 20px;">
      <div class="search-bar">
        <el-form :model="searchForm" inline>
          <el-form-item label="环境名称">
            <el-input v-model="searchForm.name" placeholder="请输入环境名称" clearable />
          </el-form-item>
          <el-form-item label="环境IP">
            <el-input v-model="searchForm.ip" placeholder="请输入环境IP" clearable />
          </el-form-item>
          <el-form-item label="环境状态">
            <el-select
              v-model="searchForm.status"
              placeholder="请选择状态"
              clearable
              style="width: 130px"
            >
              <el-option label="可用" value="available" />
              <el-option label="占用中" value="occupied" />
              <el-option label="长时间占用" value="long_term_occupied" />
              <el-option label="维护中" value="maintenance" />
              <el-option label="不可占用" value="offline" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="handleReset">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 操作栏 -->
    <div class="action-bar">
      <!-- 批量操作按钮 -->
      <el-button type="warning" @click="releaseAllMyDevices" :loading="batchLoading.release">
        <el-icon><VideoPlay /></el-icon>
        一键释放所有占用设备
      </el-button>
      <el-button type="info" @click="cancelAllMyQueues" :loading="batchLoading.cancel">
        <el-icon><VideoPause /></el-icon>
        一键取消所有排队
      </el-button>

      <!-- 管理员操作按钮 -->
      <el-button type="primary" icon="Plus" @click="openAddDialog">
        添加设备
      </el-button>
      <el-button icon="Refresh" @click="loadDevices">
        刷新
      </el-button>
    </div>

    <!-- 设备列表 -->
    <el-card shadow="never">
      <el-table :data="devices" stripe style="width: 100%" v-loading="loading">
        <!-- <el-table-column prop="name" label="环境名称" width="150"> -->
        <el-table-column prop="name" label="环境名称" >
          <template #default="{ row }">
            <div class="device-name">
              <el-icon class="device-icon">
                <Monitor />
              </el-icon>
              {{ row.name }}
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="ip" label="环境IP">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.ip }}</el-tag>
          </template>
        </el-table-column>
        

        
        <el-table-column prop="current_user" label="当前使用人">
          <template #default="{ row }">
            <span v-if="row.current_user" class="current-user">
              <el-icon><User /></el-icon>
              {{ row.current_user }}
            </span>
            <span v-else class="no-user">-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="occupied_duration" label="已使用时长" width="120">
          <template #default="{ row }">
            <span v-if="(row.status === 'occupied' || row.status === 'long_term_occupied') && row.occupied_duration >= 1" class="duration">
              {{ formatDuration(row.occupied_duration) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="queue_count" label="排队人数" width="100">
          <template #default="{ row }">
            <el-tag 
              v-if="row.queue_count > 0" 
              type="warning" 
              size="small"
            >
              {{ row.queue_count }}人
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="环境状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="getStatusTag(row.status)"
              size="small"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="连通性" width="80">
          <template #default="{ row }">
            <div class="connectivity-status">
              <el-icon
                :class="getConnectivityClass(row.id)"
                :title="getConnectivityTitle(row.id)"
                size="16"
              >
                <SuccessFilled v-if="getConnectivityStatus(row.id)" />
                <WarningFilled v-else />
              </el-icon>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <!-- 设备可用时：所有用户都可以使用 -->
              <template v-if="row.status === 'available'">
                <el-button
                  type="primary"
                  size="small"
                  @click="useDevice(row)"
                  :loading="useLoading[row.id]"
                >
                  使用
                </el-button>
                <el-button
                  type="warning"
                  size="small"
                  @click="openLongTermUseDialog(row)"
                  :loading="useLoading[row.id]"
                >
                  申请长时间占用
                </el-button>
              </template>

              <!-- 设备被占用时的操作 -->
              <template v-if="row.status === 'occupied'">
                <!-- 当前用户占用的设备：显示释放按钮 -->
                <el-button
                  v-if="row.current_user === currentUserEmployeeId"
                  type="danger"
                  size="small"
                  @click="releaseDevice(row)"
                  :loading="releaseLoading[row.id]"
                >
                  释放
                </el-button>

                <!-- 设备被他人占用时的操作 -->
                <template v-else>
                  <!-- 等待用户信息加载 -->
                  <template v-if="!userInfoLoaded">
                    <el-button size="small" loading>加载中...</el-button>
                  </template>

                  <template v-else>
                    <!-- 调试信息 -->
                    <!-- <div style="font-size: 12px; color: #666; margin-bottom: 5px;">
                      角色: {{ currentUserRole }} |
                      普通: {{ isNormalUser }} |
                      高级: {{ isAdvancedUserOnly }} |
                      管理: {{ isAdminOrSuper }}
                    </div> -->

                    <!-- 基于角色和排队状态的动态按钮逻辑 -->
                    <template v-if="currentUserRole === '管理员' || userStore.userInfo?.is_superuser">
                      <!-- 管理员/超级管理员按钮 -->
                      <el-button type="danger" size="small" @click="preemptDevice(row)" :loading="useLoading[row.id]">抢占</el-button>

                      <!-- 根据排队状态显示不同按钮 -->
                      <template v-if="!row.is_current_user_in_queue">
                        <el-button type="success" size="small" @click="priorityQueue(row)" :loading="useLoading[row.id]">优先排队</el-button>
                        <el-button type="warning" size="small" @click="joinQueue(row)" :loading="useLoading[row.id]">普通排队</el-button>
                      </template>
                      <template v-else>
                        <el-button type="info" size="small" @click="cancelQueue(row)" :loading="useLoading[row.id]">取消排队</el-button>
                      </template>

                      <el-button type="danger" size="small" @click="adminReleaseDevice(row)" :loading="releaseLoading[row.id]">强制释放</el-button>
                    </template>

                    <template v-else-if="currentUserRole === '高级用户'">
                      <!-- 高级用户按钮：可以选择抢占、优先排队或普通排队 -->
                      <el-button type="danger" size="small" @click="preemptDevice(row)" :loading="useLoading[row.id]">抢占</el-button>

                      <!-- 根据排队状态显示不同按钮 -->
                      <template v-if="!row.is_current_user_in_queue">
                        <el-button type="success" size="small" @click="priorityQueue(row)" :loading="useLoading[row.id]">优先排队</el-button>
                        <el-button type="warning" size="small" @click="joinQueue(row)" :loading="useLoading[row.id]">普通排队</el-button>
                      </template>
                      <template v-else>
                        <el-button type="info" size="small" @click="cancelQueue(row)" :loading="useLoading[row.id]">取消排队</el-button>
                      </template>
                    </template>

                    <template v-else>
                      <!-- 普通用户按钮：根据排队状态显示排队或取消排队 -->
                      <template v-if="!row.is_current_user_in_queue">
                        <el-button type="warning" size="small" @click="joinQueue(row)" :loading="useLoading[row.id]">排队</el-button>
                      </template>
                      <template v-else>
                        <el-button type="info" size="small" @click="cancelQueue(row)" :loading="useLoading[row.id]">取消排队</el-button>
                      </template>
                    </template>
                  </template>
                </template>
              </template>

              <!-- 设备长时间占用时的操作 -->
              <template v-if="row.status === 'long_term_occupied'">
                <!-- 当前用户占用的设备：显示释放按钮 -->
                <el-button
                  v-if="row.current_user === currentUserEmployeeId"
                  type="danger"
                  size="small"
                  @click="releaseDevice(row)"
                  :loading="releaseLoading[row.id]"
                >
                  释放
                </el-button>

                <!-- 管理员/超级管理员按钮 -->
                <template v-if="currentUserRole === '管理员' || userStore.userInfo?.is_superuser">
                  <el-button
                    type="danger"
                    size="small"
                    @click="adminReleaseDevice(row)"
                    :loading="releaseLoading[row.id]"
                  >
                    强制释放
                  </el-button>
                </template>
              </template>

              <!-- 详情按钮 - 所有用户都显示 -->
              <el-button 
                type="info" 
                size="small" 
                @click="viewDetails(row)"
              >
                详情
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :small="false"
          :disabled="false"
          :background="false"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 添加设备对话框 -->
    <el-dialog 
      v-model="showAddDialog" 
      title="添加设备" 
      width="600px"
      :before-close="handleAddDialogClose"
    >
      <el-form 
        ref="addFormRef" 
        :model="addForm" 
        :rules="addFormRules" 
        label-width="120px"
      >
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="addForm.name" placeholder="请输入设备名称" />
        </el-form-item>
        
        <el-form-item label="设备IP" prop="ip">
          <el-input v-model="addForm.ip" placeholder="请输入设备IP地址" />
        </el-form-item>
        
        <el-form-item label="所需VPN" prop="required_vpn">
          <el-input v-model="addForm.required_vpn" placeholder="请输入所需VPN" />
        </el-form-item>
        
        <el-form-item label="归属人" prop="owner">
          <el-input v-model="addForm.owner" placeholder="请输入归属人" />
        </el-form-item>
        
        <el-form-item label="设备类型" prop="device_type">
          <el-select v-model="addForm.device_type" placeholder="请选择设备类型">
            <el-option label="测试设备" value="test" />
            <el-option label="开发设备" value="develop" />
            <el-option label="CI设备" value="ci" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="FTP连接需VPN">
          <el-switch v-model="addForm.need_vpn_login" />
        </el-form-item>
        
        <el-form-item label="支持排队">
          <el-switch v-model="addForm.support_queue" />
        </el-form-item>
        
        <el-form-item label="备注信息">
          <el-input 
            v-model="addForm.remarks" 
            type="textarea" 
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="handleAddDevice" :loading="addLoading">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑设备对话框 -->
    <el-dialog 
      v-model="showEditDialog" 
      title="编辑设备信息" 
      width="600px"
      :before-close="handleEditDialogClose"
    >
      <el-form 
        ref="editFormRef" 
        :model="editForm" 
        :rules="addFormRules" 
        label-width="120px"
      >
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入设备名称" />
        </el-form-item>
        
        <el-form-item label="设备IP" prop="ip">
          <el-input :value="deviceDetail?.ip" disabled placeholder="IP地址不可修改" />
        </el-form-item>
        
        <el-form-item label="所需VPN" prop="required_vpn">
          <el-input v-model="editForm.required_vpn" placeholder="请输入所需VPN" />
        </el-form-item>
        
        <el-form-item label="归属人" prop="owner">
          <el-input v-model="editForm.owner" placeholder="请输入归属人" />
        </el-form-item>
        
        <el-form-item label="设备类型" prop="device_type">
          <el-select v-model="editForm.device_type" placeholder="请选择设备类型">
            <el-option label="测试设备" value="test" />
            <el-option label="开发设备" value="develop" />
            <el-option label="CI设备" value="ci" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="FTP连接需VPN">
          <el-switch v-model="editForm.need_vpn_login" />
        </el-form-item>
        
        <el-form-item label="支持排队">
          <el-switch v-model="editForm.support_queue" />
        </el-form-item>
        
        <el-form-item label="备注信息">
          <el-input 
            v-model="editForm.remarks" 
            type="textarea" 
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="handleEditDevice" :loading="editLoading">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 长时间占用设备对话框 -->
    <el-dialog
      v-model="showLongTermUseDialog"
      title="申请长时间占用设备"
      width="500px"
    >
      <el-form
        ref="longTermUseFormRef"
        :model="longTermUseForm"
        :rules="longTermUseFormRules"
        label-width="120px"
      >
        <el-form-item label="设备名称">
          <el-input :value="selectedDevice?.name" disabled />
        </el-form-item>

        <el-form-item label="使用人" prop="user">
          <el-input v-model="longTermUseForm.user" disabled />
        </el-form-item>

        <el-form-item label="截至时间" prop="end_date">
          <el-date-picker
            v-model="longTermUseForm.end_date"
            type="datetime"
            placeholder="选择截至时间"
            :disabled-date="disabledDate"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="使用目的" prop="purpose">
          <el-input
            v-model="longTermUseForm.purpose"
            type="textarea"
            :rows="3"
            placeholder="请输入使用目的"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showLongTermUseDialog = false">取消</el-button>
          <el-button type="primary" @click="handleLongTermUseDevice" :loading="submitLoading">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 设备详情抽屉 -->
    <el-drawer
      v-model="showDetailDrawer"
      title="设备详情"
      direction="rtl"
      size="600px"
      :before-close="handleDetailDrawerClose"
    >
      <div v-loading="detailLoading" class="device-detail">
        <template v-if="deviceDetail">
          <!-- 基本信息 -->
          <div class="detail-section">
            <h3 class="section-title">
              <el-icon><InfoFilled /></el-icon>
              基本信息
              <!-- 编辑按钮 - 环境归属人或管理员可见 -->
              <el-button
                v-if="canEditDevice"
                type="primary"
                size="small"
                plain
                @click="openEditDialog"
                class="edit-button"
              >
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
            </h3>
            <div class="info-grid">
              <div class="info-item">
                <label>设备名称：</label>
                <span>{{ deviceDetail.name }}</span>
              </div>
              <div class="info-item">
                <label>设备IP：</label>
                <el-tag type="info" size="small">{{ deviceDetail.ip }}</el-tag>
              </div>
              <div class="info-item">
                <label>设备类型：</label>
                <el-tag 
                  :type="getDeviceTypeTag(deviceDetail.device_type)"
                  size="small"
                >
                  {{ getDeviceTypeText(deviceDetail.device_type) }}
                </el-tag>
              </div>
              <div class="info-item">
                <label>所需VPN：</label>
                <span>{{ deviceDetail.required_vpn }}</span>
              </div>
              <div class="info-item">
                <label>添加人：</label>
                <span>{{ deviceDetail.creator }}</span>
              </div>
              <div class="info-item">
                <label>归属人：</label>
                <span>{{ deviceDetail.owner }}</span>
              </div>
              <div class="info-item">
                <label>登录需VPN：</label>
                <el-tag :type="deviceDetail.need_vpn_login ? 'warning' : 'success'" size="small">
                  {{ deviceDetail.need_vpn_login ? '是' : '否' }}
                </el-tag>
              </div>
              <div class="info-item">
                <label>支持排队：</label>
                <el-tag :type="deviceDetail.support_queue ? 'success' : 'info'" size="small">
                  {{ deviceDetail.support_queue ? '是' : '否' }}
                </el-tag>
              </div>
              <div class="info-item full-width" v-if="deviceDetail.remarks">
                <label>备注信息：</label>
                <div class="remarks">{{ deviceDetail.remarks }}</div>
              </div>
            </div>
          </div>

          <!-- 使用状态 -->
          <div class="detail-section">
            <h3 class="section-title">
              <el-icon><Clock /></el-icon>
              使用状态
            </h3>
            <div class="usage-info">
              <div class="usage-item">
                <label>当前状态：</label>
                <el-tag 
                  :type="getStatusTag(usageDetail?.status || 'available')"
                  size="small"
                >
                  {{ getStatusText(usageDetail?.status || 'available') }}
                </el-tag>
              </div>
              <div class="usage-item" v-if="usageDetail?.current_user">
                <label>当前使用人：</label>
                <span class="current-user">
                  <el-icon><User /></el-icon>
                  {{ usageDetail.current_user }}
                </span>
              </div>
              <div class="usage-item">
                <label>开始时间：</label>
                <span>{{ usageDetail?.start_time ? formatDateTime(usageDetail.start_time) : '-' }}</span>
              </div>
              <div class="usage-item">
                <label>截至时间：</label>
                <span>{{ usageDetail?.end_date ? formatDateTime(usageDetail.end_date) : '-' }}</span>
              </div>
              <div class="usage-item">
                <label>已使用时长：</label>
                <span class="duration" v-if="usageDetail?.occupied_duration >= 1">
                  {{ formatDuration(usageDetail.occupied_duration) }}
                </span>
                <span v-else>-</span>
              </div>
              <div class="usage-item">
                <label>长时间占用：</label>
                <span>{{ usageDetail?.is_long_term ? '是' : '否' }}</span>
              </div>
              <div class="usage-item full-width">
                <label>占用目的：</label>
                <div class="purpose">{{ usageDetail?.long_term_purpose || '-' }}</div>
              </div>
            </div>
          </div>

          <!-- 排队信息 -->
          <div class="detail-section">
            <h3 class="section-title">
              <el-icon><UserFilled /></el-icon>
              排队信息
              <el-tag 
                v-if="usageDetail?.queue_count > 0" 
                type="warning" 
                size="small"
                style="margin-left: 8px;"
              >
                {{ usageDetail.queue_count }}人排队
              </el-tag>
            </h3>
            <div class="queue-info">
              <template v-if="usageDetail?.queue_users && usageDetail.queue_users.length > 0">
                <div 
                  v-for="(user, index) in usageDetail.queue_users" 
                  :key="index"
                  class="queue-item"
                >
                  <div class="queue-position">{{ index + 1 }}</div>
                  <div class="queue-user">
                    <el-icon><User /></el-icon>
                    {{ user }}
                  </div>
                  <div class="queue-time">等待中</div>
                </div>
              </template>
              <div v-else class="no-queue">
                <el-empty description="暂无排队用户" :image-size="80" />
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="detail-actions">
            <!-- 普通用户按钮逻辑 -->
            <template v-if="!(isAdvancedUser || isAdminUser || isAdmin)">
              <!-- 设备可用：显示使用按钮 -->
              <el-button 
                v-if="usageDetail?.status === 'available'"
                type="primary" 
                @click="useDeviceFromDetail"
                :loading="useLoading[deviceDetail.id]"
              >
                <el-icon><VideoPlay /></el-icon>
                使用设备
              </el-button>
              
              <!-- 设备被自己占用：显示释放按钮 -->
              <el-button
                v-else-if="(usageDetail?.status === 'occupied' || usageDetail?.status === 'long_term_occupied') && usageDetail?.current_user === currentUserEmployeeId"
                type="danger"
                @click="releaseDeviceFromDetail"
                :loading="releaseLoading[deviceDetail.id]"
              >
                <el-icon><VideoPause /></el-icon>
                释放设备
              </el-button>
              
              <!-- 设备被他人占用且未排队：显示排队按钮 -->
              <el-button 
                v-else-if="usageDetail?.status === 'occupied' && usageDetail?.current_user !== currentUserEmployeeId && !isCurrentUserInQueue"
                type="warning" 
                @click="joinQueueFromDetail"
                :loading="useLoading[deviceDetail.id]"
              >
                <el-icon><Clock /></el-icon>
                排队
              </el-button>
              
              <!-- 设备被他人占用且已排队：显示取消排队按钮 -->
              <el-button 
                v-else-if="usageDetail?.status === 'occupied' && usageDetail?.current_user !== currentUserEmployeeId && isCurrentUserInQueue"
                type="info" 
                @click="cancelQueueFromDetail"
                :loading="useLoading[deviceDetail.id]"
              >
                <el-icon><Clock /></el-icon>
                取消排队
              </el-button>
            </template>
            
            <!-- 高级用户/管理员按钮逻辑 -->
            <template v-else>
              <el-button 
                v-if="usageDetail?.status === 'available'"
                type="primary" 
                @click="useDeviceFromDetail"
                :loading="useLoading[deviceDetail.id]"
              >
                <el-icon><VideoPlay /></el-icon>
                使用设备
              </el-button>
              
              <!-- 高级用户专用按钮 -->
              <template v-if="usageDetail?.status === 'occupied' || usageDetail?.status === 'long_term_occupied'">
                <el-button
                  v-if="usageDetail?.status === 'occupied'"
                  type="danger"
                  @click="preemptDeviceFromDetail"
                  :loading="useLoading[deviceDetail.id]"
                >
                  <el-icon><VideoPlay /></el-icon>
                  抢占设备
                </el-button>
                
                <el-button 
                  v-if="!isCurrentUserInQueue"
                  type="success" 
                  @click="priorityQueueFromDetail"
                  :loading="useLoading[deviceDetail.id]"
                >
                  <el-icon><Clock /></el-icon>
                  优先排队
                </el-button>
                
                <el-button 
                  v-if="isCurrentUserInQueue"
                  type="info" 
                  @click="cancelQueueFromDetail"
                  :loading="useLoading[deviceDetail.id]"
                >
                  <el-icon><Clock /></el-icon>
                  取消排队
                </el-button>
                
                <!-- 释放设备按钮 -->
                <el-button
                  v-if="usageDetail?.current_user === currentUserEmployeeId || isAdmin"
                  type="danger"
                  @click="releaseDeviceFromDetail"
                  :loading="releaseLoading[deviceDetail.id]"
                >
                  <el-icon><VideoPause /></el-icon>
                  {{ isAdmin && usageDetail?.current_user !== currentUserEmployeeId ? '强制释放' : '释放设备' }}
                </el-button>
              </template>
            </template>
            
            <!-- 删除设备按钮 - 只有设备归属人或管理员才能看到 -->
            <el-button 
              v-if="deviceDetail.owner === currentUserEmployeeId || deviceDetail.owner === currentUser || isAdmin"
              type="danger" 
              plain
              @click="deleteDeviceFromDetail"
              :loading="deleteLoading"
            >
              <el-icon><Delete /></el-icon>
              删除设备
            </el-button>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch, onActivated, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor, User, Plus, Refresh, InfoFilled, Clock, UserFilled,
  VideoPlay, VideoPause, Delete, Edit, Search, SuccessFilled, WarningFilled
} from '@element-plus/icons-vue'
import { deviceApi } from '../api/device'
import { useUserStore } from '@/stores/user'

// 获取用户store
const userStore = useUserStore()

// 数据定义
const loading = ref(false)
const devices = ref([])
const useLoading = reactive({})
const releaseLoading = reactive({})
const userInfoLoaded = ref(false)
const deleteLoading = ref(false)

// 连通性相关数据
const connectivityStatus = ref({}) // 存储设备连通性状态
const connectivityTimer = ref(null) // 连通性检测定时器

// 搜索表单
const searchForm = reactive({
  name: '',
  ip: '',
  status: ''
})

// 分页信息
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

// 批量操作加载状态
const batchLoading = reactive({
  release: false,
  cancel: false
})

// 计算属性
const currentUser = computed(() => userStore.userInfo?.username || '')
const currentUserEmployeeId = computed(() => userStore.userInfo?.employee_id?.toLowerCase() || '')
const isAdmin = computed(() => userStore.userInfo?.is_superuser || false)
const isAdvancedUser = computed(() => userStore.isAdvancedUser)
const isAdminUser = computed(() => userStore.isAdminUser)

// 确保用户信息正确加载
onMounted(async () => {
  // 等待用户store恢复状态
  await userStore.restoreFromStorage()

  // 强制从服务器获取最新的用户信息（避免角色修改后的缓存问题）
  try {
    console.log('从服务器获取最新用户信息...')
    await userStore.fetchUserInfo()
    console.log('最新用户信息:', userStore.userInfo)
  } catch (error) {
    console.error('获取用户信息失败:', error)
    // 如果获取失败，使用缓存的信息
    console.log('使用缓存的用户信息:', userStore.userInfo)
  }

  userInfoLoaded.value = true
  await loadDevices()

  // 启动连通性检测定时器
  startConnectivityTimer()
})

// 监听设备清理完成事件
const handleCleanupCompleted = () => {
  loadDevices()
}
window.addEventListener('device-cleanup-completed', handleCleanupCompleted)

// 组件卸载时移除事件监听
onUnmounted(() => {
  // 停止连通性检测定时器
  stopConnectivityTimer()

  // 移除事件监听
  window.removeEventListener('device-cleanup-completed', handleCleanupCompleted)
})

// 调试时使用的按钮: 手动刷新用户信息
const refreshUserInfo = async () => {
  try {
    console.log('手动刷新用户信息...')
    await userStore.fetchUserInfo()
    console.log('用户信息刷新完成:', userStore.userInfo)
    ElMessage.success('用户信息已刷新')
  } catch (error) {
    console.error('刷新用户信息失败:', error)
    ElMessage.error('刷新用户信息失败')
  }
}

// 监听用户信息变化
watch(() => userStore.userInfo, (newUserInfo, oldUserInfo) => {
  if (newUserInfo && oldUserInfo && newUserInfo.role !== oldUserInfo.role) {
    console.log('检测到用户角色变化:', oldUserInfo.role, '->', newUserInfo.role)
    ElMessage.info(`用户角色已更新为: ${newUserInfo.role}`)
  }
}, { deep: true })

// 页面激活时检查用户信息
onActivated(async () => {
  console.log('设备管理页面激活，检查用户信息...')
  try {
    await userStore.fetchUserInfo()
    console.log('用户信息已更新:', userStore.userInfo)
  } catch (error) {
    console.error('激活时获取用户信息失败:', error)
  }
})

// 新的权限计算属性 - 简化逻辑
const currentUserRole = computed(() => {
  const role = userStore.userInfo?.role || '未知'
  console.log('currentUserRole:', role, 'userInfo:', userStore.userInfo)
  return role
})

const isNormalUser = computed(() => {
  const role = userStore.userInfo?.role
  console.log('isNormalUser check:', { role, is_superuser: userStore.userInfo?.is_superuser })
  return role === '普通用户' && !userStore.userInfo?.is_superuser
})

const isAdvancedUserOnly = computed(() => {
  const role = userStore.userInfo?.role
  console.log('isAdvancedUserOnly check:', { role, is_superuser: userStore.userInfo?.is_superuser })
  return role === '高级用户' && !userStore.userInfo?.is_superuser
})

const isAdminOrSuper = computed(() => {
  const role = userStore.userInfo?.role
  const is_superuser = userStore.userInfo?.is_superuser
  console.log('isAdminOrSuper check:', { role, is_superuser })
  return is_superuser || role === '管理员'
})

// 判断是否可以编辑设备（环境归属人或管理员）
const canEditDevice = computed(() => {
  if (!deviceDetail.value || !userStore.userInfo) return false

  // 管理员或超级管理员可以编辑任何设备
  const isAdminOrSuperUser = userStore.userInfo.is_superuser || userStore.userInfo.role === '管理员'
  if (isAdminOrSuperUser) {
    return true
  }

  // 环境归属人可以编辑自己的设备
  const isOwner = deviceDetail.value.owner === userStore.userInfo.employee_id

  console.log('canEditDevice check:', {
    device: deviceDetail.value.name,
    owner: deviceDetail.value.owner,
    currentUser: userStore.userInfo.employee_id,
    isOwner,
    isAdminOrSuperUser,
    canEdit: isOwner || isAdminOrSuperUser
  })

  return isOwner || isAdminOrSuperUser
})

// 调试用的计算属性
const debugInfo = computed(() => {
  const info = {
    userInfo: userStore.userInfo,
    role: userStore.userInfo?.role,
    is_superuser: userStore.userInfo?.is_superuser,
    isNormalUser: isNormalUser.value,
    isAdvancedUserOnly: isAdvancedUserOnly.value,
    isAdminOrSuper: isAdminOrSuper.value,
    storeIsAdvancedUser: userStore.isAdvancedUser,
    storeIsAdminUser: userStore.isAdminUser
  }
  console.log('Debug Info:', info)
  return info
})

// 检查用户是否在指定设备的排队中（用于列表）
const isUserInDeviceQueue = (device) => {
  // 这里需要通过API获取设备使用详情才能知道排队情况
  // 为了性能考虑，我们可以在设备列表中添加当前用户的排队状态字段
  return false // 暂时返回false，后续优化
}

// 添加设备相关
const showAddDialog = ref(false)
const addLoading = ref(false)
const addFormRef = ref()
const addForm = reactive({
  name: '',
  ip: '',
  required_vpn: '',
  owner: '',
  device_type: 'test',
  need_vpn_login: false,
  support_queue: true,
  remarks: ''
})

const addFormRules = {
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  ip: [
    { required: true, message: '请输入设备IP', trigger: 'blur' },
    { pattern: /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/, message: '请输入正确的IP地址格式', trigger: 'blur' }
  ],
  required_vpn: [{ required: true, message: '请输入所需VPN', trigger: 'blur' }],
  creator: [{ required: true, message: '请输入添加人', trigger: 'blur' }],
  owner: [{ required: true, message: '请输入归属人', trigger: 'blur' }]
}

// 长时间占用设备相关
const showLongTermUseDialog = ref(false)
const submitLoading = ref(false)
const selectedDevice = ref(null)
const longTermUseFormRef = ref()
const longTermUseForm = reactive({
  user: '',
  end_date: '',
  purpose: ''
})

const longTermUseFormRules = {
  user: [{ required: true, message: '请输入使用人', trigger: 'blur' }],
  end_date: [{ required: true, message: '请选择截至时间', trigger: 'change' }],
  purpose: [{ required: true, message: '请输入使用目的', trigger: 'blur' }]
}

// 抽屉相关
const showDetailDrawer = ref(false)
const detailLoading = ref(false)
const deviceDetail = ref(null)
const usageDetail = ref(null)

// 编辑设备相关
const showEditDialog = ref(false)
const editLoading = ref(false)
const editFormRef = ref()
const editForm = reactive({
  name: '',
  ip: '',
  required_vpn: '',
  owner: '',
  device_type: '',
  need_vpn_login: false,
  support_queue: true,
  remarks: ''
})

// 方法定义
const loadDevices = async () => {
  loading.value = true
  try {
    const response = await deviceApi.getDevices({
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm
    })
    devices.value = response.data.items
    pagination.total = response.data.total
    console.log('成功加载设备列表，数量:', devices.value?.length)
  } catch (error) {
    console.error('加载设备失败:', error)
    ElMessage.error('加载设备列表失败')
  } finally {
    loading.value = false
  }

  // 加载设备后检查连通性
  await checkDevicesConnectivity()
}

// 连通性检测相关方法
const checkDevicesConnectivity = async () => {
  if (!devices.value || devices.value.length === 0) return

  try {
    const deviceIds = devices.value.map(device => device.id)
    const response = await deviceApi.getDevicesConnectivityStatus(deviceIds)
    connectivityStatus.value = response.data
  } catch (error) {
    console.error('获取连通性状态失败:', error)
  }
}

const getConnectivityStatus = (deviceId) => {
  const status = connectivityStatus.value[deviceId]
  return status ? status.status : false
}

const getConnectivityClass = (deviceId) => {
  const status = connectivityStatus.value[deviceId]
  if (!status) return 'connectivity-unknown'
  return status.status ? 'connectivity-online' : 'connectivity-offline'
}

const getConnectivityTitle = (deviceId) => {
  const status = connectivityStatus.value[deviceId]
  if (!status) return '连通性未知'

  const statusText = status.status ? '连通正常' : '连通失败'
  const lastCheck = status.last_check ? new Date(status.last_check).toLocaleString() : '未检测'
  return `${statusText}\n最后检测: ${lastCheck}`
}

const startConnectivityTimer = () => {
  // 清除现有定时器
  if (connectivityTimer.value) {
    clearInterval(connectivityTimer.value)
  }

  // 每10秒检测一次连通性
  connectivityTimer.value = setInterval(async () => {
    await checkDevicesConnectivity()
  }, 10000)
}

const stopConnectivityTimer = () => {
  if (connectivityTimer.value) {
    clearInterval(connectivityTimer.value)
    connectivityTimer.value = null
  }
}

const useDevice = async (device) => {
  // 直接使用设备，不弹出对话框
  try {
    useLoading[device.id] = true
    const response = await deviceApi.useDevice({
      device_id: device.id,
      user: currentUserEmployeeId.value
    })

    ElMessage.success(response.data?.message || '设备使用成功')
    await loadDevices()
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('使用设备失败')
    }
  } finally {
    useLoading[device.id] = false
  }
}

// 打开长时间占用对话框
const openLongTermUseDialog = (device) => {
  selectedDevice.value = device
  longTermUseForm.user = currentUserEmployeeId.value
  longTermUseForm.end_date = ''
  longTermUseForm.purpose = ''
  showLongTermUseDialog.value = true
}

// 处理长时间占用设备
const handleLongTermUseDevice = async () => {
  if (!longTermUseFormRef.value) return

  try {
    await longTermUseFormRef.value.validate()
    submitLoading.value = true
    const response = await deviceApi.longTermUseDevice({
      device_id: selectedDevice.value.id,
      user: longTermUseForm.user.toLowerCase(),
      end_date: longTermUseForm.end_date,
      purpose: longTermUseForm.purpose
    })
    ElMessage.success(response.data?.message || '长时间占用申请成功')
    showLongTermUseDialog.value = false
    await loadDevices()
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('申请失败')
    }
  } finally {
    submitLoading.value = false
  }
}

// 禁用过去的日期
const disabledDate = (time) => {
  return time.getTime() < Date.now() - 8.64e7 // 禁用今天之前的日期
}

const joinQueue = async (device) => {
  try {
    useLoading[device.id] = true
    const response = await deviceApi.unifiedQueue({
      device_id: device.id,
      user: currentUserEmployeeId.value,
      expected_duration: 60,
      purpose: '普通排队'
    })

    if (response.data?.queue_position) {
      ElMessage.success(`已加入排队，排队位置：${response.data.queue_position}`)
    } else {
      ElMessage.success('已加入排队')
    }

    await loadDevices()

    // 如果详情抽屉打开，刷新详情数据
    if (showDetailDrawer.value && deviceDetail.value?.id === device.id) {
      await viewDetails(device)
    }
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('加入排队失败')
    }
  } finally {
    useLoading[device.id] = false
  }
}

const cancelQueue = async (device) => {
  try {
    await ElMessageBox.confirm(
      '确定要取消排队吗？',
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    useLoading[device.id] = true
    await deviceApi.cancelQueue({
      device_id: device.id
    })
    
    ElMessage.success('已取消排队')
    await loadDevices()
    
    // 如果详情抽屉打开，刷新详情数据
    if (showDetailDrawer.value && deviceDetail.value?.id === device.id) {
      await viewDetails(device)
    }
  } catch (error) {
    if (error !== 'cancel') {
      if (error.response?.data?.detail) {
        ElMessage.error(error.response.data.detail)
      } else {
        ElMessage.error('取消排队失败')
      }
    }
  } finally {
    useLoading[device.id] = false
  }
}

// 统一排队操作
const unifiedQueueAction = async (device) => {
  try {
    useLoading[device.id] = true
    const response = await deviceApi.unifiedQueue({
      device_id: device.id,
      user: currentUserEmployeeId.value,
      expected_duration: 60,
      purpose: '使用设备'
    })
    
    if (response.data.action === 'use') {
      ElMessage.success('设备使用成功')
    } else {
      ElMessage.success(`已加入排队，排队位置：${response.data.queue_position}`)
    }
    
    await loadDevices()
    
    // 如果详情抽屉打开，刷新详情数据
    if (showDetailDrawer.value && deviceDetail.value?.id === device.id) {
      await viewDetails(device)
    }
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('操作失败')
    }
  } finally {
    useLoading[device.id] = false
  }
}

// 抢占设备
const preemptDevice = async (device) => {
  try {
    await ElMessageBox.confirm(
      '确定要抢占此设备吗？原使用者将被加入排队列表首位。',
      '确认抢占',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    useLoading[device.id] = true
    const response = await deviceApi.preemptDevice({
      device_id: device.id,
      user: currentUserEmployeeId.value,
      expected_duration: 60,
      purpose: '抢占使用'
    })
    
    ElMessage.success(response.message)
    await loadDevices()
    
    // 如果详情抽屉打开，刷新详情数据
    if (showDetailDrawer.value && deviceDetail.value?.id === device.id) {
      await viewDetails(device)
    }
  } catch (error) {
    if (error !== 'cancel') {
      if (error.response?.data?.detail) {
        ElMessage.error(error.response.data.detail)
      } else {
        ElMessage.error('抢占设备失败')
      }
    }
  } finally {
    useLoading[device.id] = false
  }
}

// 优先排队
const priorityQueue = async (device) => {
  try {
    useLoading[device.id] = true
    const response = await deviceApi.priorityQueue({
      device_id: device.id,
      user: currentUserEmployeeId.value,
      expected_duration: 60,
      purpose: '优先排队'
    })
    
    ElMessage.success(response.message)
    await loadDevices()
    
    // 如果详情抽屉打开，刷新详情数据
    if (showDetailDrawer.value && deviceDetail.value?.id === device.id) {
      await viewDetails(device)
    }
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('优先排队失败')
    }
  } finally {
    useLoading[device.id] = false
  }
}

const releaseDevice = async (device) => {
  try {
    await ElMessageBox.confirm(
      '确定要释放此设备吗？',
      '确认释放',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    releaseLoading[device.id] = true
    const response = await deviceApi.releaseDevice({
      device_id: device.id,
      user: currentUserEmployeeId.value
    })
    
    // 显示后端返回的消息
    ElMessage.success(response.message)
    await loadDevices()
  } catch (error) {
    if (error !== 'cancel') {
      if (error.response?.data?.detail) {
        ElMessage.error(error.response.data.detail)
      } else {
        ElMessage.error('释放设备失败')
      }
    }
  } finally {
    releaseLoading[device.id] = false
  }
}

// 管理员强制释放设备
const adminReleaseDevice = async (device) => {
  try {
    await ElMessageBox.confirm(
      `确定要强制释放设备 ${device.name} 吗？当前使用者：${device.current_user}`,
      '强制释放确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    releaseLoading[device.id] = true
    const response = await deviceApi.releaseDevice({
      device_id: device.id,
      user: device.current_user // 使用当前占用者的用户名
    })

    ElMessage.success(response.message)
    await loadDevices()

    // 如果详情抽屉打开，刷新详情数据
    if (showDetailDrawer.value && deviceDetail.value?.id === device.id) {
      await viewDetails(device)
    }
  } catch (error) {
    if (error !== 'cancel') {
      if (error.response?.data?.detail) {
        ElMessage.error(error.response.data.detail)
      } else {
        ElMessage.error('强制释放设备失败')
      }
    }
  } finally {
    releaseLoading[device.id] = false
  }
}

const viewDetails = async (device) => {
  try {
    detailLoading.value = true
    showDetailDrawer.value = true
    
    // 获取设备详情
    const [deviceResponse, usageResponse] = await Promise.all([
      deviceApi.getDevice(device.id),
      deviceApi.getDeviceUsage(device.id)
    ])
    
    deviceDetail.value = deviceResponse.data
    usageDetail.value = usageResponse.data
  } catch (error) {
    ElMessage.error('获取设备详情失败')
    console.error(error)
  } finally {
    detailLoading.value = false
  }
}

const handleAddDevice = async () => {
  if (!addFormRef.value) return
  
  try {
    await addFormRef.value.validate()
    addLoading.value = true
    
    // 创建设备数据，添加creator字段，确保工号为小写
    const deviceData = {
      ...addForm,
      owner: addForm.owner.toLowerCase(),
      creator: userStore.userInfo?.employee_id?.toLowerCase() || userStore.userInfo?.username || ''
    }
    
    await deviceApi.createDevice(deviceData)
    ElMessage.success('设备添加成功')
    showAddDialog.value = false
    await loadDevices()
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('添加设备失败')
    }
  } finally {
    addLoading.value = false
  }
}



const openAddDialog = () => {
  // 重置表单
  if (addFormRef.value) {
    addFormRef.value.resetFields()
  }
  
  // 设置默认值
  addForm.owner = userStore.userInfo?.employee_id?.toLowerCase() || userStore.userInfo?.username || ''
  
  showAddDialog.value = true
}

const handleAddDialogClose = () => {
  addFormRef.value?.resetFields()
  showAddDialog.value = false
}

// 编辑设备相关方法
const openEditDialog = () => {
  if (!deviceDetail.value) return
  
  // 填充编辑表单
  editForm.name = deviceDetail.value.name
  editForm.ip = deviceDetail.value.ip
  editForm.required_vpn = deviceDetail.value.required_vpn
  editForm.owner = deviceDetail.value.owner
  editForm.device_type = deviceDetail.value.device_type
  editForm.need_vpn_login = deviceDetail.value.need_vpn_login
  editForm.support_queue = deviceDetail.value.support_queue
  editForm.remarks = deviceDetail.value.remarks || ''
  
  showEditDialog.value = true
}

const handleEditDevice = async () => {
  if (!editFormRef.value || !deviceDetail.value) return
  
  try {
    await editFormRef.value.validate()
    editLoading.value = true
    
    // 确保owner字段为小写
    const updateData = {
      ...editForm,
      owner: editForm.owner.toLowerCase()
    }
    
    await deviceApi.updateDevice(deviceDetail.value.id, updateData)
    ElMessage.success('设备信息更新成功')
    showEditDialog.value = false
    
    // 刷新设备详情和列表
    await viewDetails(deviceDetail.value)
    await loadDevices()
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('更新设备信息失败')
    }
  } finally {
    editLoading.value = false
  }
}

const handleEditDialogClose = () => {
  editFormRef.value?.resetFields()
  showEditDialog.value = false
}

// 辅助方法
const getDeviceTypeText = (type) => {
  const typeMap = {
    test: '测试',
    develop: '开发',
    ci: 'CI'
  }
  return typeMap[type] || type
}

const getDeviceTypeTag = (type) => {
  const tagMap = {
    test: 'success',
    develop: 'primary',
    ci: 'warning'
  }
  return tagMap[type] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    available: '可用',
    occupied: '占用中',
    long_term_occupied: '长时间占用',
    maintenance: '维护中',
    offline: '不可占用',
    queue: '排队中'
  }
  return statusMap[status] || status
}

const getStatusTag = (status) => {
  const tagMap = {
    available: 'success',
    occupied: 'warning',
    long_term_occupied: 'danger',
    maintenance: 'info',
    offline: 'danger'
  }
  return tagMap[status] || 'info'
}

const formatDuration = (minutes) => {
  if (minutes < 60) {
    return `${minutes}分钟`
  } else {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}小时${mins > 0 ? mins + '分钟' : ''}`
  }
}

const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return '-'
  const date = new Date(dateTimeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

// 抽屉相关方法
const handleDetailDrawerClose = () => {
  showDetailDrawer.value = false
  deviceDetail.value = null
  usageDetail.value = null
}

const useDeviceFromDetail = () => {
  if (deviceDetail.value) {
    useDevice(deviceDetail.value)
    // 对于普通用户直接使用，不关闭抽屉以便看到结果
    // 对于高级用户弹出对话框，会关闭抽屉
    if (isAdvancedUser.value || isAdminUser.value || isAdmin.value) {
      showDetailDrawer.value = false
    }
  }
}

const releaseDeviceFromDetail = async () => {
  if (deviceDetail.value) {
    await releaseDevice(deviceDetail.value)
    showDetailDrawer.value = false
  }
}

const joinQueueFromDetail = async () => {
  if (deviceDetail.value) {
    await joinQueue(deviceDetail.value)
    // 刷新详情数据
    await viewDetails(deviceDetail.value)
  }
}

const preemptDeviceFromDetail = () => {
  if (deviceDetail.value) {
    preemptDevice(deviceDetail.value)
    // 不关闭抽屉，让用户能看到结果
  }
}

const priorityQueueFromDetail = () => {
  if (deviceDetail.value) {
    priorityQueue(deviceDetail.value)
    // 不关闭抽屉，让用户能看到结果
  }
}

const cancelQueueFromDetail = async () => {
  if (deviceDetail.value) {
    await cancelQueue(deviceDetail.value)
    // 不关闭抽屉，因为cancelQueue已经会刷新详情数据
  }
}

// 删除设备
const deleteDeviceFromDetail = async () => {
  if (!deviceDetail.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除设备 "${deviceDetail.value.name}" 吗？此操作不可恢复！`,
      '删除设备',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: false
      }
    )
    
    deleteLoading.value = true
    await deviceApi.deleteDevice(deviceDetail.value.id)
    ElMessage.success('设备删除成功')
    showDetailDrawer.value = false
    await loadDevices()
  } catch (error) {
    if (error === 'cancel') {
      return
    }
    
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('删除设备失败')
    }
  } finally {
    deleteLoading.value = false
  }
}

// 检查当前用户是否在抽屉设备的排队中
const isCurrentUserInQueue = computed(() => {
  if (!usageDetail.value?.queue_users || !currentUserEmployeeId.value) return false
  return usageDetail.value.queue_users.includes(currentUserEmployeeId.value)
})

// 批量操作方法
const releaseAllMyDevices = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要释放所有您占用的设备吗？',
      '批量释放确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    batchLoading.release = true

    try {
      const response = await deviceApi.batchReleaseMyDevices()
      ElMessage.success(response.message)
      await loadDevices()
    } catch (apiError) {
      console.error('批量释放API调用失败:', apiError)
      ElMessage.error('批量释放设备失败')
    }

  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量释放设备失败:', error)
      ElMessage.error('批量释放设备失败')
    }
  } finally {
    batchLoading.release = false
  }
}

const cancelAllMyQueues = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要取消所有您的排队吗？',
      '批量取消排队确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    batchLoading.cancel = true

    try {
      const response = await deviceApi.batchCancelMyQueues()
      ElMessage.success(response.message)
      await loadDevices()
    } catch (apiError) {
      console.error('批量取消排队API调用失败:', apiError)
      ElMessage.error('批量取消排队失败')
    }

  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量取消排队失败:', error)
      ElMessage.error('批量取消排队失败')
    }
  } finally {
    batchLoading.cancel = false
  }
}

// 搜索处理
const handleSearch = () => {
  pagination.page = 1
  loadDevices()
}

// 重置搜索
const handleReset = () => {
  Object.assign(searchForm, {
    name: '',
    ip: '',
    status: ''
  })
  pagination.page = 1
  loadDevices()
}

// 分页大小改变
const handleSizeChange = (val: number) => {
  pagination.page_size = val
  pagination.page = 1
  loadDevices()
}

// 当前页改变
const handleCurrentChange = (val: number) => {
  pagination.page = val
  loadDevices()
}

// 生命周期已在上面的onMounted中处理
</script>

<style scoped>
.device-management {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.search-bar {
  margin-bottom: 0;
}

.action-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.device-list {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.device-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-icon {
  color: #409eff;
}

.current-user {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #409eff;
}

.no-user {
  color: #c0c4cc;
}

.duration {
  color: #e6a23c;
  font-weight: 500;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 抽屉样式 */
.device-detail {
  padding: 20px;
}

.detail-section {
  margin-bottom: 30px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px;
  background: #fafafa;
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  border-bottom: 2px solid #409eff;
  padding-bottom: 8px;
}

.section-title .edit-button {
  margin-left: auto;
  margin-bottom: 4px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item.full-width {
  grid-column: 1 / -1;
  flex-direction: column;
  align-items: flex-start;
}

.info-item label {
  font-weight: 500;
  color: #606266;
  min-width: 80px;
}

.remarks, .purpose {
  background: white;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  width: 100%;
  margin-top: 8px;
  line-height: 1.5;
}

.usage-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.usage-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.usage-item.full-width {
  flex-direction: column;
  align-items: flex-start;
}

.usage-item label {
  font-weight: 500;
  color: #606266;
  min-width: 100px;
}

.queue-info {
  max-height: 300px;
  overflow-y: auto;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: white;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 8px;
}

.queue-position {
  background: #409eff;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}

.queue-user {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 4px;
  color: #303133;
}

.queue-time {
  color: #909399;
  font-size: 12px;
}

.no-queue {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}

.detail-actions {
  position: sticky;
  bottom: 0;
  background: white;
  padding: 20px 0;
  border-top: 1px solid #ebeef5;
  margin-top: 20px;
  display: flex;
  gap: 12px;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .device-management {
    padding: 10px;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 4px;
  }
  
  .action-buttons .el-button {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .device-detail {
    padding: 15px;
  }
  
  .detail-section {
    padding: 15px;
  }
}

/* 连通性状态样式 */
.connectivity-status {
  display: flex;
  justify-content: center;
  align-items: center;
}

.connectivity-online {
  color: #67c23a; /* 绿色 */
}

.connectivity-offline {
  color: #f56c6c; /* 红色 */
}

.connectivity-unknown {
  color: #909399; /* 灰色 */
}
</style>