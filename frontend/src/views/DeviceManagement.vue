<template>
  <div class="device-management">
    <div class="page-header">
      <h1>设备管理</h1>
      <p>管理和监控Linux设备的使用情况</p>
    </div>

    <!-- 当前使用中的环境 -->
    <el-card shadow="never" class="usage-summary-card" v-loading="usageSummaryLoading">
      <template #header>
        <div class="summary-header">
          <div class="summary-title">
            <el-icon><Monitor /></el-icon>
            <span>当前使用的环境</span>
          </div>
          <el-button text size="small" @click="loadUsageSummary">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      <div class="usage-section">
        <div class="usage-title">我占用的环境</div>
        <el-table :data="usageSummary.occupied" size="small" style="width:100%">
          <el-table-column label="环境名称" min-width="180">
            <template #default="{ row }">
              <div class="device-name">
                <el-icon class="device-icon"><Monitor /></el-icon>
                <span class="name-text">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="环境IP" width="160">
            <template #default="{ row }">
              <el-tag type="info" size="small">{{ row.ip }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="已使用时长" width="140">
            <template #default="{ row }">
              <span v-if="row.occupied_duration && row.occupied_duration >= 1">{{ formatDuration(row.occupied_duration) }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="所属分组" min-width="200">
            <template #default="{ row }">
              <template v-if="row.groups?.length">
                <el-tag v-for="g in row.groups" :key="g.id" size="small" type="info" style="margin-right:4px">{{ g.name }}</el-tag>
              </template>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button type="danger" size="small" @click="releaseFromUsage(row)" :loading="row.__releasing">释放</el-button>
            </template>
          </el-table-column>
          <el-table-column label="详情" width="120">
            <template #default="{ row }">
              <el-button size="small" @click="viewDetails(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="usage-section">
        <div class="usage-title">我共用的环境</div>
        <el-table :data="usageSummary.shared" size="small" style="width:100%">
          <el-table-column label="环境名称" min-width="180">
            <template #default="{ row }">
              <div class="device-name">
                <el-icon class="device-icon"><Monitor /></el-icon>
                <span class="name-text">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="环境IP" width="160">
            <template #default="{ row }">
              <el-tag type="info" size="small">{{ row.ip }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="已使用时长" width="140">
            <template #default="{ row }">
              <span v-if="row.occupied_duration && row.occupied_duration >= 1">{{ formatDuration(row.occupied_duration) }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="所属分组" min-width="200">
            <template #default="{ row }">
              <template v-if="row.groups?.length">
                <el-tag v-for="g in row.groups" :key="g.id" size="small" type="info" style="margin-right:4px">{{ g.name }}</el-tag>
              </template>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200">
            <template #default="{ row }">
              <el-button type="danger" size="small" plain @click="cancelShareFromUsage(row)" :disabled="!row.share_request_id" :loading="row.__canceling">取消共用</el-button>
            </template>
          </el-table-column>
          <el-table-column label="详情" width="120">
            <template #default="{ row }">
              <el-button size="small" @click="viewDetails(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

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
          <el-form-item label="配置值">
            <el-input v-model="searchForm.config_value" placeholder="请输入配置关键词" clearable />
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

        <el-table-column label="所属分组" min-width="160">
          <template #default="{ row }">
            <div v-if="row.groups?.length" class="group-tags">
              <el-tag
                v-for="group in row.groups"
                :key="group.id"
                size="small"
                type="info"
                class="group-tag"
              >
                {{ group.name }}
              </el-tag>
            </div>
            <span v-else class="no-data">-</span>
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
                  :disabled="!row.support_queue || !!useLoading[row.id]"
                  :title="!row.support_queue ? '该设备未开放使用' : ''"
                >
                  使用
                </el-button>
                <el-button
                  v-if="showLongTermUseButton"
                  type="warning"
                  size="small"
                  @click="openLongTermUseDialog(row)"
                  :loading="useLoading[row.id]"
                  :disabled="!row.support_queue || !!useLoading[row.id]"
                  :title="!row.support_queue ? '该设备未开放使用' : ''"
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
                        <el-button
                          type="success"
                          size="small"
                          @click="priorityQueue(row)"
                          :loading="useLoading[row.id]"
                          :disabled="!row.support_queue || !!useLoading[row.id]"
                          :title="!row.support_queue ? '该设备未开放排队' : ''"
                        >
                          优先排队
                        </el-button>
                        <el-button
                          type="warning"
                          size="small"
                          @click="joinQueue(row)"
                          :loading="useLoading[row.id]"
                          :disabled="!row.support_queue || !!useLoading[row.id]"
                          :title="!row.support_queue ? '该设备未开放排队' : ''"
                        >
                          普通排队
                        </el-button>
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
                        <el-button
                          type="success"
                          size="small"
                          @click="priorityQueue(row)"
                          :loading="useLoading[row.id]"
                          :disabled="!row.support_queue || !!useLoading[row.id]"
                          :title="!row.support_queue ? '该设备未开放排队' : ''"
                        >
                          优先排队
                        </el-button>
                        <el-button
                          type="warning"
                          size="small"
                          @click="joinQueue(row)"
                          :loading="useLoading[row.id]"
                          :disabled="!row.support_queue || !!useLoading[row.id]"
                          :title="!row.support_queue ? '该设备未开放排队' : ''"
                        >
                          普通排队
                        </el-button>
                      </template>
                      <template v-else>
                        <el-button type="info" size="small" @click="cancelQueue(row)" :loading="useLoading[row.id]">取消排队</el-button>
                      </template>
                    </template>

                    <template v-else>
                      <!-- 普通用户按钮：根据排队状态显示排队或取消排队 -->
                      <template v-if="!row.is_current_user_in_queue">
                        <el-button
                          type="warning"
                          size="small"
                          @click="joinQueue(row)"
                          :loading="useLoading[row.id]"
                          :disabled="!row.support_queue || !!useLoading[row.id]"
                          :title="!row.support_queue ? '该设备未开放排队' : ''"
                        >
                          排队
                        </el-button>
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

              <span v-if="showShareControls(row)" class="share-controls">
                <el-button
                  v-if="canForceShare(row)"
                  type="danger"
                  size="small"
                  plain
                  @click="forceShare(row)"
                  :loading="forceShareLoading[row.id]"
                >
                  强制使用
                </el-button>
                <template v-if="canApplyShare(row)">
                  <el-button
                    type="primary"
                    size="small"
                    plain
                    @click="requestShare(row)"
                    :loading="shareRequestLoading[row.id]"
                  >
                    申请共用
                  </el-button>
                </template>
                <template v-else-if="row.share_request_id">
                  <el-button
                    type="danger"
                    size="small"
                    plain
                    @click="cancelShare(row)"
                    :loading="shareRequestLoading[row.id]"
                  >
                    {{ row.is_shared_user ? '取消共用' : '取消申请' }}
                  </el-button>
                </template>
                <el-tag v-if="row.has_pending_share_request" size="small" type="warning">
                  申请处理中
                </el-tag>
                <el-tag v-else-if="row.is_shared_user" size="small" type="success">
                  已获批共用
                </el-tag>
              </span>
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
        
        <el-form-item label="VPN域段" prop="vpn_region">
          <el-select
            v-model="addForm.vpn_region"
            placeholder="请选择域段"
            @change="onAddFormRegionChange"
            clearable
          >
            <el-option
              v-for="region in availableRegions"
              :key="region"
              :label="region"
              :value="region"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="* VPN网段" prop="vpn_config_id">
          <el-select
            v-model="addForm.vpn_config_id"
            placeholder="请选择网段"
            :disabled="!addForm.vpn_region"
            clearable
          >
            <el-option
              v-for="config in filteredNetworksForAdd"
              :key="config.id"
              :label="config.network"
              :value="config.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="归属人" prop="owner">
          <el-input v-model="addForm.owner" placeholder="请输入归属人" />
        </el-form-item>

        <el-form-item label="管理员账号" prop="admin_username">
          <el-input v-model="addForm.admin_username" placeholder="请输入管理员账号" />
        </el-form-item>

        <el-form-item label="管理员密码" prop="admin_password">
          <el-input v-model="addForm.admin_password" placeholder="请输入管理员密码" />
        </el-form-item>

        <el-form-item label="设备类型" prop="device_type">
          <el-select v-model="addForm.device_type" placeholder="请选择设备类型">
            <el-option label="测试设备" value="test" />
            <el-option label="开发设备" value="develop" />
            <el-option label="CI设备" value="ci" />
          </el-select>
        </el-form-item>

        <el-form-item label="设备形态" prop="form_type">
          <el-select v-model="addForm.form_type" placeholder="请选择设备形态">
            <el-option label="单" value="单" />
            <el-option label="双" value="双" />
            <el-option label="未知" value="未知" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="FTP需要前缀">
          <el-switch v-model="addForm.ftp_prefix" />
        </el-form-item>
        <el-form-item label="最长占用(分钟)">
          <el-input-number
            v-model="addForm.max_occupy_minutes"
            :min="1"
            :max="1440"
            placeholder="留空表示不限制"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="支持排队">
          <el-switch v-model="addForm.support_queue" />
        </el-form-item>

        <el-form-item label="所属分组">
          <el-select
            v-model="addForm.group_ids"
            multiple
            filterable
            placeholder="请选择分组"
            style="width: 100%"
          >
            <el-option
              v-for="group in groupOptions"
              :key="group.id"
              :label="group.name"
              :value="group.id"
            />
          </el-select>
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
        
        <el-form-item label="VPN域段" prop="vpn_region">
          <el-select
            v-model="editForm.vpn_region"
            placeholder="请选择域段"
            @change="onEditFormRegionChange"
            clearable
            :disabled="!canEditDevice"
          >
            <el-option
              v-for="region in availableRegions"
              :key="region"
              :label="region"
              :value="region"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="* VPN网段" prop="vpn_config_id">
          <el-select
            v-model="editForm.vpn_config_id"
            placeholder="请选择网段"
            :disabled="!editForm.vpn_region || !canEditDevice"
            clearable
          >
            <el-option
              v-for="config in filteredNetworksForEdit"
              :key="config.id"
              :label="config.network"
              :value="config.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="归属人" prop="owner">
          <el-input v-model="editForm.owner" placeholder="请输入归属人" />
        </el-form-item>

        <el-form-item label="管理员账号" prop="admin_username">
          <el-input v-model="editForm.admin_username" placeholder="请输入管理员账号" />
        </el-form-item>

        <el-form-item label="管理员密码" prop="admin_password">
          <el-input v-model="editForm.admin_password" placeholder="请输入管理员密码" />
        </el-form-item>

        <el-form-item label="设备类型" prop="device_type">
          <el-select v-model="editForm.device_type" placeholder="请选择设备类型">
            <el-option label="测试设备" value="test" />
            <el-option label="开发设备" value="develop" />
            <el-option label="CI设备" value="ci" />
          </el-select>
        </el-form-item>

        <el-form-item label="设备形态" prop="form_type">
          <el-select v-model="editForm.form_type" placeholder="请选择设备形态">
            <el-option label="单" value="单" />
            <el-option label="双" value="双" />
            <el-option label="未知" value="未知" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="FTP需要前缀">
          <el-switch v-model="editForm.ftp_prefix" />
        </el-form-item>
        <el-form-item label="最长占用(分钟)">
          <el-input-number
            v-model="editForm.max_occupy_minutes"
            :min="1"
            :max="1440"
            placeholder="留空表示不限制"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="支持排队">
          <el-switch v-model="editForm.support_queue" />
        </el-form-item>

        <el-form-item label="所属分组">
          <el-select
            v-model="editForm.group_ids"
            multiple
            filterable
            placeholder="请选择分组"
            style="width: 100%"
          >
            <el-option
              v-for="group in groupOptions"
              :key="group.id"
              :label="group.name"
              :value="group.id"
            />
          </el-select>
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
          <!-- Tab页面结构 -->
          <el-tabs v-model="activeDetailTab" class="device-detail-tabs">
            <!-- 基本信息Tab -->
            <el-tab-pane label="基本信息" name="basic">
              <div class="detail-section">
            <h3 class="section-title">
              <div class="section-title__info">
                <el-icon><InfoFilled /></el-icon>
                基本信息
              </div>
              <div class="section-actions">
                <el-button
                  type="primary"
                  size="small"
                  plain
                  class="copy-button"
                  @click="copyDeviceInfo"
                >
                  <el-icon><DocumentCopy /></el-icon>
                  一键复制
                </el-button>
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
              </div>
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
                <label>设备形态：</label>
                <el-tag size="small">{{ deviceDetail.form_type }}</el-tag>
              </div>
              <div class="info-item">
                <label>所需VPN：</label>
                <span v-if="deviceDetail.vpn_display_name">{{ deviceDetail.vpn_display_name }}</span>
                <span v-else class="no-vpn">未配置VPN</span>
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
                <label>所属分组：</label>
                <div v-if="deviceDetail.groups?.length" class="group-tags">
                  <el-tag
                    v-for="group in deviceDetail.groups"
                    :key="group.id"
                    size="small"
                    type="info"
                    class="group-tag"
                  >
                    {{ group.name }}
                  </el-tag>
                </div>
                <span v-else>-</span>
              </div>
              <!-- 管理员账号密码 - 只有归属人和管理员可见 -->
              <div v-if="canEditDevice" class="info-item">
                <label>管理员账号：</label>
                <span>{{ deviceDetail.admin_username }}</span>
              </div>
              <div v-if="canEditDevice" class="info-item">
                <label>管理员密码：</label>
                <span>{{ deviceDetail.admin_password }}</span>
              </div>
              <div v-if="shouldShowCurrentCredentials" class="info-item">
                <label>当前账号：</label>
                <span>{{ deviceDetail.admin_username }}</span>
              </div>
              <div v-if="shouldShowCurrentCredentials" class="info-item copyable">
                <label>当前密码：</label>
                <span>{{ deviceDetail.admin_password }}</span>
                <el-button
                  text
                  size="small"
                  type="primary"
                  @click="copyCredential(deviceDetail.admin_password)"
                >
                  复制
                </el-button>
              </div>
              <div class="info-item">
                <label>FTP需要前缀：</label>
                <el-tag :type="deviceDetail.ftp_prefix ? 'warning' : 'success'" size="small">
                  {{ deviceDetail.ftp_prefix ? '是' : '否' }}
                </el-tag>
              </div>
              <div class="info-item">
                <label>最长占用(分钟)：</label>
                <span>{{ deviceDetail.max_occupy_minutes ?? '未限制' }}</span>
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

          <div
            class="detail-section"
            v-if="usageDetail && (usageDetail.shared_users?.length || usageDetail.has_pending_share_request || isCurrentUserOccupant)"
          >
            <h3 class="section-title">
              <el-icon><UserFilled /></el-icon>
              共用信息
            </h3>
            <div class="shared-users-info">
              <div v-if="usageDetail?.shared_users?.length" class="shared-users-list">
                <div
                  v-for="user in usageDetail.shared_users"
                  :key="user.employee_id"
                  class="shared-user-item"
                >
                  <el-tag type="success" size="small">
                    {{ user.username }} ({{ user.employee_id }})
                  </el-tag>
                  <span class="shared-reason" v-if="user.request_message">
                    申请原因：{{ user.request_message }}
                  </span>
                  <span class="shared-time" v-if="user.approved_at">
                    于 {{ formatDateTime(user.approved_at) }} 获批
                  </span>
                  <el-button
                    v-if="isCurrentUserOccupant || isAdmin"
                    type="danger"
                    size="small"
                    plain
                    @click="revokeSharedUser(user)"
                    :loading="detailShareLoading"
                    style="margin-left: 8px;"
                  >
                    剔除
                  </el-button>
                </div>
              </div>
              <div v-else class="no-data">暂无共用用户</div>
              <div v-if="usageDetail?.share_status" class="share-status">
                当前状态：{{ getShareStatusText(usageDetail.share_status) }}
              </div>
              <div
                class="pending-tip"
                v-if="usageDetail?.has_pending_share_request && !isCurrentUserOccupant && !isSharedUser"
              >
                您的共用申请正在等待占用人处理
              </div>
              <div
                class="shared-actions"
                v-if="usageDetail?.share_request_id && (usageDetail?.has_pending_share_request || usageDetail?.is_shared_user)"
              >
                <el-button
                  type="danger"
                  size="small"
                  plain
                  @click="cancelShareFromDetail"
                  :loading="detailShareLoading"
                >
                  {{ usageDetail?.is_shared_user ? '取消共用' : '取消申请' }}
                </el-button>
              </div>
            </div>
          </div>

          <!-- 访问IP信息 -->
          <div class="detail-section" v-if="usageDetail?.can_view_access_ips">
            <h3 class="section-title">
              <el-icon><InfoFilled /></el-icon>
              访问IP
            </h3>
            <el-table :data="usageDetail?.access_ips || []" size="small" style="width: 100%">
              <el-table-column label="人员" min-width="200">
                <template #default="{ row }">
                  {{ row.username }} ({{ row.employee_id }})
                </template>
              </el-table-column>
              <el-table-column prop="role" label="身份" width="120" />
              <el-table-column label="访问IP" min-width="180">
                <template #default="{ row }">
                  <span>{{ row.vpn_ip || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="更新时间" width="180">
                <template #default="{ row }">
                  <span>{{ row.updated_at ? formatDateTime(row.updated_at) : '-' }}</span>
                </template>
              </el-table-column>
            </el-table>
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
            </el-tab-pane>

            <!-- 配置管理Tab -->
            <el-tab-pane label="配置管理" name="config">
              <div class="config-section">
                <div class="config-header">
                  <h3>设备配置</h3>
                  <div class="config-actions">
                    <el-button
                      v-if="canEditDevice"
                      type="primary"
                      size="small"
                      plain
                      :loading="configImportLoading"
                      @click="triggerImportConfigs"
                    >
                      <el-icon><UploadFilled /></el-icon>
                      一键导入
                    </el-button>
                    <el-button
                      v-if="canEditDevice"
                      type="primary"
                      size="small"
                      @click="openConfigDialog"
                      icon="Plus"
                    >
                      添加配置
                    </el-button>
                  </div>
                </div>
                
                <el-table 
                  :data="deviceConfigs" 
                  stripe 
                  style="width: 100%" 
                  v-loading="configLoading"
                  empty-text="暂无配置数据"
                >
                  <el-table-column prop="config_param1" label="配置参数1" width="100">
                    <template #default="{ row }">
                      <el-tag size="small">{{ row.config_param1 }}</el-tag>
                    </template>
                  </el-table-column>
                  
                  <el-table-column prop="config_param2" label="配置参数2" width="100">
                    <template #default="{ row }">
                      <el-tag size="small">{{ row.config_param2 }}</el-tag>
                    </template>
                  </el-table-column>
                  
                  <el-table-column prop="config_value" label="配置值">
                    <template #default="{ row }">
                      <span>{{ row.config_value }}</span>
                    </template>
                  </el-table-column>
                  
                  <el-table-column prop="created_at" label="创建时间" width="160">
                    <template #default="{ row }">
                      {{ formatDateTime(row.created_at) }}
                    </template>
                  </el-table-column>
                  
                  <el-table-column 
                    v-if="canEditDevice" 
                    label="操作" 
                    width="120"
                    fixed="right"
                  >
                    <template #default="{ row }">
                      <el-button
                        type="primary"
                        size="small"
                        text
                        @click="editConfig(row)"
                        icon="Edit"
                      >
                        编辑
                      </el-button>
                      <el-button
                        type="danger"
                        size="small"
                        text
                        @click="deleteConfig(row)"
                        icon="Delete"
                      >
                        删除
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </el-tab-pane>
          </el-tabs>
        </template>
      </div>
    </el-drawer>

    <!-- 配置管理对话框 -->
    <el-dialog
      v-model="configDialogVisible"
      :title="isEditingConfig ? '编辑配置' : '添加配置'"
      width="450px"
      :before-close="handleConfigDialogClose"
    >
      <el-form
        ref="configFormRef"
        :model="configForm"
        :rules="configRules"
        label-width="100px"
      >
        <el-form-item label="配置参数1" prop="config_param1">
          <el-input-number
            v-model="configForm.config_param1"
            :min="1"
            :max="deviceDetail?.form_type === '单' ? 1 : 8"
            :disabled="deviceDetail?.form_type === '单'"
            style="width: 100%"
          />
          <div v-if="deviceDetail?.form_type === '单'" style="color: #909399; font-size: 12px; margin-top: 4px;">
            形态为"单"时，参数1固定为1
          </div>
        </el-form-item>
        
        <el-form-item label="配置参数2" prop="config_param2">
          <el-input-number
            v-model="configForm.config_param2"
            :min="1"
            :max="40"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="配置值" prop="config_value">
          <el-input
            v-model="configForm.config_value"
            type="textarea"
            :rows="3"
            placeholder="请输入配置值"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleConfigDialogClose">取消</el-button>
          <el-button
            type="primary"
            @click="saveConfig"
            :loading="configSaveLoading"
          >
            {{ isEditingConfig ? '更新' : '添加' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch, onActivated, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
// 修复某些版本下自动样式导入路径不一致问题，手动引入所需样式
import 'element-plus/es/components/message-box/style/css'
import 'element-plus/es/components/message/style/css'
import {
  Monitor, User, Plus, Refresh, InfoFilled, Clock, UserFilled,
  VideoPlay, VideoPause, Delete, Edit, Search, SuccessFilled, WarningFilled,
  DocumentCopy, UploadFilled
} from '@element-plus/icons-vue'
import { deviceApi, type DeviceConfig } from '../api/device'
import { vpnApi } from '../api/vpn'
import { useUserStore } from '@/stores/user'
import { getGroupList } from '@/api/user'

// 获取用户store
const userStore = useUserStore()

// 数据定义
const loading = ref(false)
const devices = ref([])
const useLoading = reactive({})
const releaseLoading = reactive({})
const userInfoLoaded = ref(false)
const deleteLoading = ref(false)
const groupOptions = ref<{ id: number; name: string }[]>([])
const shareRequestLoading = reactive<Record<number, boolean>>({})
const forceShareLoading = reactive<Record<number, boolean>>({})
const detailShareLoading = ref(false)
const usageSummaryLoading = ref(false)
const usageSummary = reactive<{ occupied: any[]; shared: any[] }>({
  occupied: [],
  shared: []
})
const ensureDeviceOperational = (device, action: '使用' | '排队' = '使用') => {
  if (!device?.support_queue) {
    ElMessage.warning(`该设备未开放${action}`)
    return false
  }
  return true
}

// 从使用摘要表格释放设备
const releaseFromUsage = async (row) => {
  if (!row?.id) return
  try {
    row.__releasing = true
    await deviceApi.releaseDevice({ device_id: row.id, user: currentUserEmployeeId.value })
    ElMessage.success('设备已释放')
    await loadDevices()
    await loadUsageSummary()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '释放失败')
  } finally {
    row.__releasing = false
  }
}

// 从使用摘要表格取消共用
const cancelShareFromUsage = async (row) => {
  if (!row?.share_request_id) return
  try {
    row.__canceling = true
    await deviceApi.cancelShareRequest(row.share_request_id)
    ElMessage.success('已取消共用')
    await loadDevices()
    await loadUsageSummary()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '取消失败')
  } finally {
    row.__canceling = false
  }
}

// 详情页Tab状态
const activeDetailTab = ref('basic')

// 配置管理相关数据
const deviceConfigs = ref<DeviceConfig[]>([])
const configLoading = ref(false)
const configDialogVisible = ref(false)
const isEditingConfig = ref(false)
const currentConfigId = ref<number | null>(null)
const configSaveLoading = ref(false)
const configFormRef = ref()
const triggerImportConfigs = async () => {
  if (!deviceDetail.value) {
    ElMessage.warning('设备信息不存在')
    return
  }
  try {
    configImportLoading.value = true
    const response = await deviceApi.importAllDeviceConfigs(deviceDetail.value.id) as any
    ElMessage.success(response.data?.message || '导入任务已触发')
    await loadDeviceConfigs(deviceDetail.value.id)
  } catch (error) {
    console.error('触发配置导入失败:', error)
    ElMessage.error(error?.response?.data?.detail || '导入失败')
  } finally {
    configImportLoading.value = false
  }
}
const configImportLoading = ref(false)

// 配置表单
const configForm = reactive({
  config_param1: 1,
  config_param2: 1,
  config_value: ''
})

// 配置表单验证规则
const configRules = {
  config_param1: [
    { required: true, message: '请选择配置参数1', trigger: 'change' }
  ],
  config_param2: [
    { required: true, message: '请选择配置参数2', trigger: 'change' }
  ],
  config_value: [
    { required: true, message: '请输入配置值', trigger: 'blur' }
  ]
}

// 连通性相关数据
const connectivityStatus = ref({}) // 存储设备连通性状态
const connectivityTimer = ref(null) // 连通性检测定时器

// VPN相关数据
const vpnConfigs = ref([]) // 所有VPN配置
const availableRegions = ref([]) // 可用的域段列表
const filteredNetworksForAdd = ref([]) // 添加表单中过滤后的网段
const filteredNetworksForEdit = ref([]) // 编辑表单中过滤后的网段
const loadGroupOptions = async () => {
  try {
    const response = await getGroupList()
    groupOptions.value = (response.data || []).map((group: any) => ({
      id: group.id,
      name: group.name
    }))
  } catch (error) {
    console.error('获取分组列表失败:', error)
  }
}

// 搜索表单
const searchForm = reactive({
  name: '',
  ip: '',
  status: '',
  config_value: ''
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

const showShareControls = (device) => {
  if (!device) return false
  const occupiedStatuses = ['occupied', 'long_term_occupied']
  return (
    occupiedStatuses.includes(device.status) &&
    device.current_user &&
    device.current_user !== currentUserEmployeeId.value
  )
}

const canApplyShare = (device) => {
  if (!device) return false
  return showShareControls(device) && !device.has_pending_share_request && !device.is_shared_user && !device.share_request_id
}

const canForceShare = (device) => {
  if (!device) return false
  return showShareControls(device) && !device.is_shared_user
}

const getShareStatusText = (status?: string) => {
  if (!status) return '-'
  const map: Record<string, string> = {
    pending: '待审批',
    approved: '已获批',
    rejected: '已拒绝',
    revoked: '已取消',
    cancelled: '已取消'
  }
  return map[status] || status
}

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
  await loadVPNConfigs()
  await loadGroupOptions()

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
  if (!deviceDetail.value || !userStore.userInfo) {
    console.log('canEditDevice: 缺少必要信息', { deviceDetail: !!deviceDetail.value, userInfo: !!userStore.userInfo })
    return false
  }

  // 管理员或超级管理员可以编辑任何设备
  const isAdminOrSuperUser = userStore.userInfo.is_superuser || userStore.userInfo.role === '管理员'
  if (isAdminOrSuperUser) {
    console.log('canEditDevice: 管理员权限', { is_superuser: userStore.userInfo.is_superuser, role: userStore.userInfo.role })
    return true
  }

  // 环境归属人可以编辑自己的设备
  // 使用 employee_id 或 username 进行比较
  const currentUserId = userStore.userInfo.employee_id // || userStore.userInfo.username 这里不应该用name比较, 只考虑id即可
  const isOwner = deviceDetail.value.owner === currentUserId

  console.log('canEditDevice check:', {
    device: deviceDetail.value.name,
    owner: deviceDetail.value.owner,
    currentUserId: currentUserId,
    employee_id: userStore.userInfo.employee_id,
    username: userStore.userInfo.username,
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
  vpn_region: '',
  vpn_config_id: null,
  owner: '',
  admin_username: 'root123',
  admin_password: 'Root@123',
  device_type: 'test',
  form_type: '',
  ftp_prefix: false,
  max_occupy_minutes: null as number | null,
  support_queue: true,
  remarks: '',
  group_ids: [] as number[]
})

const addFormRules = {
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  ip: [
    { required: true, message: '请输入设备IP', trigger: 'blur' },
    { pattern: /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/, message: '请输入正确的IP地址格式', trigger: 'blur' }
  ],
  vpn_region: [{ required: true, message: '请选择VPN域段', trigger: 'change' }],
  vpn_config_id: [{ required: true, message: '请选择VPN网段', trigger: 'change' }],
  creator: [{ required: true, message: '请输入添加人', trigger: 'blur' }],
  owner: [{ required: true, message: '请输入归属人', trigger: 'blur' }],
  admin_username: [{ required: true, message: '请输入管理员账号', trigger: 'blur' }],
  admin_password: [{ required: true, message: '请输入管理员密码', trigger: 'blur' }],
  form_type: [{ required: true, message: '请选择设备形态', trigger: 'change' }]
}

// 控制“申请长时间占用”按钮（未来可通过配置/权限启用）
const showLongTermUseButton = false

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
const isCurrentUserOccupant = computed(() => usageDetail.value?.current_user === currentUserEmployeeId.value)
const isSharedUser = computed(() => {
  if (usageDetail.value?.is_shared_user) return true
  if (!usageDetail.value?.shared_users) return false
  return usageDetail.value.shared_users.some(user => user.employee_id === currentUserEmployeeId.value)
})
const shouldShowCurrentCredentials = computed(() => {
  if (canEditDevice.value) return false
  return isCurrentUserOccupant.value || isSharedUser.value
})
const canViewCredentials = computed(() => canEditDevice.value || shouldShowCurrentCredentials.value)

// 编辑设备相关
const showEditDialog = ref(false)
const editLoading = ref(false)
const editFormRef = ref()
const editForm = reactive({
  name: '',
  ip: '',
  vpn_region: '',
  vpn_config_id: null,
  owner: '',
  admin_username: '',
  admin_password: '',
  device_type: '',
  form_type: '',
  ftp_prefix: false,
  max_occupy_minutes: null as number | null,
  support_queue: true,
  remarks: '',
  group_ids: [] as number[]
})

// 方法定义
const loadUsageSummary = async () => {
  try {
    usageSummaryLoading.value = true
    const response = await deviceApi.getMyUsageSummary()
    usageSummary.occupied = response.data?.occupied_devices || []
    usageSummary.shared = response.data?.shared_devices || []
  } catch (error) {
    console.error('加载环境使用信息失败:', error)
    usageSummary.occupied = []
    usageSummary.shared = []
  } finally {
    usageSummaryLoading.value = false
  }
}

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
  try {
    await checkDevicesConnectivity()
  } catch (error) {
    console.error('获取连通性状态失败:', error)
  }

  try {
    await loadUsageSummary()
  } catch (error) {
    console.error('加载使用摘要失败:', error)
  }
}

// VPN相关方法
const loadVPNConfigs = async () => {
  try {
    const response = await vpnApi.getAllVPNConfigs()
    vpnConfigs.value = response.data || []

    // 提取所有唯一的域段
    const regions = Array.from(new Set(vpnConfigs.value.map(config => config.region)))
    availableRegions.value = regions

    console.log('成功加载VPN配置，数量:', vpnConfigs.value.length)
    console.log('VPN配置数据:', vpnConfigs.value)
  } catch (error) {
    console.error('加载VPN配置失败:', error)
    ElMessage.error('加载VPN配置失败')
  }
}

// 添加表单域段变化处理
const onAddFormRegionChange = (selectedRegion) => {
  addForm.vpn_config_id = null // 清空网段选择
  if (selectedRegion) {
    filteredNetworksForAdd.value = vpnConfigs.value.filter(
      config => config.region === selectedRegion
    )
  } else {
    filteredNetworksForAdd.value = []
  }
}

// 编辑表单域段变化处理
const onEditFormRegionChange = (selectedRegion) => {
  editForm.vpn_config_id = null // 清空网段选择
  if (selectedRegion) {
    filteredNetworksForEdit.value = vpnConfigs.value.filter(
      config => config.region === selectedRegion
    )
  } else {
    filteredNetworksForEdit.value = []
  }
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

const forceShare = async (device) => {
  if (!device) return
  if (!showShareControls(device)) {
    ElMessage.warning('当前无需强制使用')
    return
  }
  if (forceShareLoading[device.id]) return

  try {
    const { value, action } = await ElMessageBox.prompt('请输入强制共用的备注信息（可为空）', '强制使用', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputType: 'textarea',
      inputPlaceholder: '请输入备注信息'
    })
    if (action !== 'confirm') return

    forceShareLoading[device.id] = true
    await deviceApi.forceShare(device.id, { message: value })
    ElMessage.success('已强制加入共用')
    await loadDevices()
    await loadUsageSummary()
    if (showDetailDrawer.value && deviceDetail.value?.id === device.id) {
      await viewDetails(device)
    }
  } catch (error: any) {
    if (error === 'cancel') return
    if (error?.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('强制使用失败')
    }
  } finally {
    forceShareLoading[device.id] = false
  }
}

const requestShare = async (device) => {
  if (!device) return
  if (!showShareControls(device)) {
    ElMessage.warning('当前不可申请共用')
    return
  }
  if (device.share_request_id) {
    ElMessage.warning('已存在共用申请')
    return
  }
  if (shareRequestLoading[device.id]) {
    return
  }
  try {
    // 申请共用时需填写说明
    const { value, action } = await ElMessageBox.prompt('请输入申请共用的说明', '申请共用', {
      confirmButtonText: '提交',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '说明不能为空'
    })
    if (action !== 'confirm') return

    shareRequestLoading[device.id] = true
    await deviceApi.requestShare({
      device_id: device.id,
      message: value
    })
    ElMessage.success('共用申请已提交')
    await loadDevices()
    await loadUsageSummary()
    if (showDetailDrawer.value && deviceDetail.value?.id === device.id) {
      await viewDetails(device)
    }
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('申请共用失败')
    }
  } finally {
    shareRequestLoading[device.id] = false
  }
}

const cancelShare = async (device) => {
  if (!device?.share_request_id) {
    ElMessage.warning('暂无可取消的共用信息')
    return
  }
  if (shareRequestLoading[device.id]) {
    return
  }
  try {
    shareRequestLoading[device.id] = true
    await deviceApi.cancelShareRequest(device.share_request_id)
    ElMessage.success(device.is_shared_user ? '已取消共用' : '已取消申请')
    await loadDevices()
    await loadUsageSummary()
    if (showDetailDrawer.value && deviceDetail.value?.id === device.id) {
      await viewDetails(device)
    }
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('取消共用失败')
    }
  } finally {
    shareRequestLoading[device.id] = false
  }
}

const cancelShareFromDetail = async () => {
  if (!usageDetail.value?.share_request_id || !deviceDetail.value) {
    ElMessage.warning('暂无可取消的共用信息')
    return
  }
  try {
    detailShareLoading.value = true
    await deviceApi.cancelShareRequest(usageDetail.value.share_request_id)
    ElMessage.success(usageDetail.value.is_shared_user ? '已取消共用' : '已取消申请')
    await loadDevices()
    await loadUsageSummary()
    await viewDetails(deviceDetail.value)
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('取消共用失败')
    }
  } finally {
    detailShareLoading.value = false
  }
}

const revokeSharedUser = async (user) => {
  if (!usageDetail.value || !user?.share_request_id) return
  try {
    detailShareLoading.value = true
    await deviceApi.revokeSharedUser(user.share_request_id)
    ElMessage.success('已剔除共用用户')
    await loadDevices()
    await viewDetails(deviceDetail.value)
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('剔除失败')
    }
  } finally {
    detailShareLoading.value = false
  }
}

const copyDeviceInfo = async () => {
  if (!deviceDetail.value) {
    ElMessage.warning('暂无可复制的设备信息')
    return
  }
  const parts = [
    `设备名称: ${deviceDetail.value.name}`,
    `设备IP: ${deviceDetail.value.ip}`,
    `所需VPN: ${deviceDetail.value.vpn_display_name || '未配置'}`
  ]
  if (canViewCredentials.value) {
    parts.push(`管理员账号: ${deviceDetail.value.admin_username}`)
    parts.push(`管理员密码: ${deviceDetail.value.admin_password}`)
  }
  const text = parts.join('\n')
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('设备信息已复制')
  } catch (error) {
    console.error('复制设备信息失败:', error)
    ElMessage.error('复制失败，请手动查看')
  }
}

const copyCredential = async (value?: string) => {
  if (!value) {
    ElMessage.warning('暂无可复制的密码')
    return
  }
  try {
    await navigator.clipboard.writeText(value)
    ElMessage.success('密码已复制')
  } catch (error) {
    console.error('复制密码失败:', error)
    ElMessage.error('复制失败，请手动查看')
  }
}

const useDevice = async (device) => {
  if (!ensureDeviceOperational(device, '使用')) return
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
  if (!ensureDeviceOperational(device, '使用')) return
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
  if (!ensureDeviceOperational(device, '排队')) return
  try {
    useLoading[device.id] = true
    const response = await deviceApi.unifiedQueue({
      device_id: device.id,
      user: currentUserEmployeeId.value,
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
  if (!ensureDeviceOperational(device, '排队')) return
  try {
    useLoading[device.id] = true
    const response = await deviceApi.unifiedQueue({
      device_id: device.id,
      user: currentUserEmployeeId.value,
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
  if (!ensureDeviceOperational(device, '使用')) return
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
      purpose: '抢占使用'
    })
    
    ElMessage.success(response.data?.message || '操作成功')
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
  if (!ensureDeviceOperational(device, '排队')) return
  try {
    useLoading[device.id] = true
    const response = await deviceApi.priorityQueue({
      device_id: device.id,
      user: currentUserEmployeeId.value,
      purpose: '优先排队'
    })
    
    ElMessage.success(response.data?.message || '操作成功')
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
    ElMessage.success(response.data?.message || '操作成功')
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

    ElMessage.success(response.data?.message || '操作成功')
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
      name: addForm.name,
      ip: addForm.ip,
      vpn_config_id: addForm.vpn_config_id,
      owner: addForm.owner.toLowerCase(),
      admin_username: addForm.admin_username,
      admin_password: addForm.admin_password,
      device_type: addForm.device_type,
      form_type: addForm.form_type,
      ftp_prefix: addForm.ftp_prefix,
      max_occupy_minutes: addForm.max_occupy_minutes || null,
      support_queue: addForm.support_queue,
      remarks: addForm.remarks,
      group_ids: addForm.group_ids,
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

  // 重置VPN相关字段
  addForm.vpn_region = ''
  addForm.vpn_config_id = null
  addForm.group_ids = []
  addForm.max_occupy_minutes = null
  filteredNetworksForAdd.value = []

  // 设置默认值
  addForm.owner = userStore.userInfo?.employee_id?.toLowerCase() || userStore.userInfo?.username || ''
  addForm.admin_username = 'root123'
  addForm.admin_password = 'Root@123'

  // 设置默认VPN配置（第一条）
  if (vpnConfigs.value.length > 0) {
    const firstVpnConfig = vpnConfigs.value[0]
    addForm.vpn_region = firstVpnConfig.region
    addForm.vpn_config_id = firstVpnConfig.id
    // 更新网段选项
    filteredNetworksForAdd.value = vpnConfigs.value.filter(
      config => config.region === firstVpnConfig.region
    )
  }

  showAddDialog.value = true
}

const handleAddDialogClose = () => {
  addFormRef.value?.resetFields()
  addForm.group_ids = []
  showAddDialog.value = false
}

// 编辑设备相关方法
const openEditDialog = () => {
  if (!deviceDetail.value) return

  // 填充编辑表单
  editForm.name = deviceDetail.value.name
  editForm.ip = deviceDetail.value.ip
  editForm.vpn_region = deviceDetail.value.vpn_region || ''
  editForm.vpn_config_id = deviceDetail.value.vpn_config_id || null
  editForm.owner = deviceDetail.value.owner
  editForm.admin_username = deviceDetail.value.admin_username
  editForm.admin_password = deviceDetail.value.admin_password
  editForm.device_type = deviceDetail.value.device_type
  editForm.form_type = deviceDetail.value.form_type
  editForm.ftp_prefix = deviceDetail.value.ftp_prefix
  editForm.max_occupy_minutes = deviceDetail.value.max_occupy_minutes ?? null
  editForm.support_queue = deviceDetail.value.support_queue
  editForm.remarks = deviceDetail.value.remarks || ''
  editForm.group_ids = (deviceDetail.value.groups || []).map((group: any) => group.id)

  // 根据当前选择的域段过滤网段
  if (editForm.vpn_region) {
    filteredNetworksForEdit.value = vpnConfigs.value.filter(
      config => config.region === editForm.vpn_region
    )
  } else {
    filteredNetworksForEdit.value = []
  }

  showEditDialog.value = true
}

const handleEditDevice = async () => {
  if (!editFormRef.value || !deviceDetail.value) return
  
  try {
    await editFormRef.value.validate()
    editLoading.value = true
    
    // 确保owner字段为小写，移除vpn_region字段
    const updateData = {
      name: editForm.name,
      vpn_config_id: editForm.vpn_config_id,
      owner: editForm.owner.toLowerCase(),
      admin_username: editForm.admin_username,
      admin_password: editForm.admin_password,
      device_type: editForm.device_type,
      form_type: editForm.form_type,
      ftp_prefix: editForm.ftp_prefix,
      max_occupy_minutes: editForm.max_occupy_minutes || null,
      support_queue: editForm.support_queue,
      remarks: editForm.remarks,
      group_ids: editForm.group_ids
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
  editForm.group_ids = []
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
      ElMessage.success(response.data?.message || '操作成功')
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
      ElMessage.success(response.data?.message || '操作成功')
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
    status: '',
    config_value: ''
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

// ===== 配置管理相关函数 =====

// 加载设备配置列表
const loadDeviceConfigs = async (deviceId: number) => {
  if (!deviceId) return
  
  try {
    configLoading.value = true
    const response = await deviceApi.getDeviceConfigs(deviceId)
    if (response.data) {
      deviceConfigs.value = response.data || []
    } else {
      deviceConfigs.value = []
    }
  } catch (error) {
    console.error('加载设备配置失败:', error)
    deviceConfigs.value = []
    ElMessage.error('加载设备配置失败')
  } finally {
    configLoading.value = false
  }
}

// 打开配置对话框
const openConfigDialog = () => {
  isEditingConfig.value = false
  currentConfigId.value = null
  configForm.config_param1 = deviceDetail.value?.form_type === '单' ? 1 : 1
  configForm.config_param2 = 1
  configForm.config_value = ''
  configDialogVisible.value = true
}

// 编辑配置
const editConfig = (config: DeviceConfig) => {
  isEditingConfig.value = true
  currentConfigId.value = config.id
  configForm.config_param1 = config.config_param1
  configForm.config_param2 = config.config_param2
  configForm.config_value = config.config_value
  configDialogVisible.value = true
}

// 删除配置
const deleteConfig = async (config: DeviceConfig) => {
  try {
    await ElMessageBox.confirm(
      `确定删除配置 "参数1=${config.config_param1}, 参数2=${config.config_param2}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    const response = await deviceApi.deleteDeviceConfig(config.device_id, config.id) as any
    if (response.code === 200) {
      ElMessage.success('配置删除成功')
      await loadDeviceConfigs(config.device_id)
    } else {
      ElMessage.error(response.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除配置失败:', error)
      ElMessage.error('删除配置失败')
    }
  }
}

// 保存配置
const saveConfig = async () => {
  if (!configFormRef.value) return
  
  try {
    await configFormRef.value.validate()
    
    if (!deviceDetail.value) {
      ElMessage.error('设备信息不存在')
      return
    }
    
    configSaveLoading.value = true
    
    if (isEditingConfig.value && currentConfigId.value) {
      // 编辑现有配置
      const response = await deviceApi.updateDeviceConfig(
        deviceDetail.value.id,
        currentConfigId.value,
        {
          config_param1: configForm.config_param1,
          config_param2: configForm.config_param2,
          config_value: configForm.config_value
        }
      ) as any
      
      if (response.code === 200) {
        ElMessage.success('配置更新成功')
        handleConfigDialogClose()
        await loadDeviceConfigs(deviceDetail.value.id)
      } else {
        ElMessage.error(response.message || '更新失败')
      }
    } else {
      // 添加新配置
      const response = await deviceApi.createDeviceConfig(
        deviceDetail.value.id,
        {
          config_param1: configForm.config_param1,
          config_param2: configForm.config_param2,
          config_value: configForm.config_value
        }
      ) as any
      
      if (response.code === 200) {
        ElMessage.success('配置添加成功')
        handleConfigDialogClose()
        await loadDeviceConfigs(deviceDetail.value.id)
      } else {
        ElMessage.error(response.message || '添加失败')
      }
    }
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error('保存配置失败')
  } finally {
    configSaveLoading.value = false
  }
}

// 关闭配置对话框
const handleConfigDialogClose = () => {
  configDialogVisible.value = false
  isEditingConfig.value = false
  currentConfigId.value = null
  configForm.config_param1 = 1
  configForm.config_param2 = 1
  configForm.config_value = ''
  if (configFormRef.value) {
    configFormRef.value.clearValidate()
  }
}


// 监听设备详情变化，当切换到配置管理Tab时加载配置数据
watch(activeDetailTab, (newTab) => {
  if (newTab === 'config' && deviceDetail.value) {
    loadDeviceConfigs(deviceDetail.value.id)
  }
})

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
  justify-content: flex-start;
  gap: 8px;
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  border-bottom: 2px solid #409eff;
  padding-bottom: 8px;
}

.section-title__info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.section-title .edit-button {
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

.info-item.copyable span {
  font-family: 'Menlo', 'Courier New', monospace;
}

.usage-summary-card {
  margin-bottom: 20px;
}

.summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.summary-header .summary-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}

.usage-summary-content {
  display: flex;
  gap: 40px;
  flex-wrap: wrap;
}

.summary-column {
  flex: 1;
  min-width: 220px;
}

.column-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: #303133;
}

.summary-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.summary-tag {
  margin-bottom: 4px;
}

.empty-summary {
  color: #909399;
  font-size: 13px;
}

.share-controls {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-left: 8px;
}

.shared-users-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.shared-users-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.shared-user-item {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.shared-reason {
  color: #606266;
  font-size: 12px;
}

.shared-time {
  color: #909399;
  font-size: 12px;
}

.pending-tip {
  color: #e6a23c;
  font-size: 13px;
}

.shared-actions {
  margin-top: 10px;
}

.share-status {
  margin-top: 6px;
  color: #606266;
  font-size: 13px;
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

/* 设备详情Tab样式 */
.device-detail-tabs {
  margin-top: -10px;
}

.device-detail-tabs .el-tabs__content {
  padding: 0;
}

/* 配置管理样式 */
.config-section {
  padding: 20px 0;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.config-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.config-actions {
  display: flex;
  gap: 8px;
  align-items: center;
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

.group-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.group-tag {
  margin-bottom: 4px;
}

.no-data {
  color: #909399;
  font-size: 12px;
}
</style>
