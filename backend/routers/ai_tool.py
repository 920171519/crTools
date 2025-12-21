"""
AI 工具路由
提供 AI 诊断功能的 API 接口
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncGenerator
from datetime import datetime
import asyncio
import json

from models.aiToolModel import AIDiagnosisLog
from models.deviceModel import Device
from models.admin import User
from schemas import (
    AIDiagnosisCreate, AIDiagnosisResponse, AIDiagnosisListItem, BaseResponse
)
from auth import AuthManager
from connectivity_manager import connectivity_manager

router = APIRouter(prefix="/api/ai-tool", tags=["AI工具"])


async def generate_diagnosis_stream(
    device: Device,
    problem_description: str,
    diagnosis_log: AIDiagnosisLog,
    connectivity_status: dict
) -> AsyncGenerator[str, None]:
    """生成诊断流式输出"""

    try:
        # 发送开始信号
        yield f"data: {json.dumps({'type': 'start', 'message': '开始诊断...'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.5)

        # 发送设备信息
        device_info = f"""# 诊断结果

## 设备信息
- **设备名称**: {device.name}
- **设备IP**: {device.ip}
- **设备类型**: {device.device_type}
- **所属项目**: {device.project_name or "未设置"}
"""
        yield f"data: {json.dumps({'type': 'content', 'content': device_info}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.5)

        # 发送连通性检测结果
        last_ping = connectivity_status.get("last_ping")
        last_ping_str = last_ping.strftime(
            '%Y-%m-%d %H:%M:%S') if last_ping else "未知"

        connectivity_info = f"""
## 连通性检测
✅ **设备连通正常**
- 最后检测时间: {last_ping_str}
"""
        yield f"data: {json.dumps({'type': 'content', 'content': connectivity_info}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.5)

        # 发送问题描述
        problem_info = f"""
## 问题描述
{problem_description}
"""
        yield f"data: {json.dumps({'type': 'content', 'content': problem_info}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.5)

        # 模拟 AI 分析过程
        yield f"data: {json.dumps({'type': 'content', 'content': '\n## AI 分析中...\n'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(1)

        # 发送分析结果（这里预留 AI 调用的位置）
        analysis_result = """
## 初步分析
设备网络连接正常，可以进行进一步诊断。

> **注意**: AI 诊断功能正在开发中，当前仅返回设备连通性信息。
> 后续将支持通过 AI (Qwen) 分析系统日志、性能指标等信息，提供详细的故障诊断建议。

### 建议操作
1. 检查系统日志: `journalctl -xe`
2. 查看系统资源使用情况: `top` 或 `htop`
3. 检查磁盘空间: `df -h`
4. 查看网络连接: `netstat -tuln`

### 常见问题排查

#### 系统性能问题
```bash
# 查看 CPU 和内存使用情况
top -bn1 | head -20

# 查看磁盘 I/O 情况
iostat -x 1 5
```

#### 网络连接问题
```bash
# 检查网络接口状态
ip addr show

# 查看路由表
ip route show

# 测试网络连通性
ping -c 4 8.8.8.8
```

#### 服务状态检查
```bash
# 查看系统服务状态
systemctl status

# 检查失败的服务
systemctl --failed
```
"""

        # 逐段发送分析结果
        lines = analysis_result.split('\n')
        for i, line in enumerate(lines):
            if line.strip():
                yield f"data: {json.dumps({'type': 'content', 'content': line + '\\n'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)

        # 发送完成信号
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        footer = f"""
---
*诊断时间: {current_time}*
"""
        yield f"data: {json.dumps({'type': 'content', 'content': footer}, ensure_ascii=False)}\n\n"

        # 更新数据库记录
        full_result = device_info + connectivity_info + \
            problem_info + analysis_result + footer
        await diagnosis_log.update_result(
            diagnosis_result=full_result,
            status="success",
            connectivity_status=True
        )

        yield f"data: {json.dumps({'type': 'done', 'message': '诊断完成', 'log_id': diagnosis_log.id}, ensure_ascii=False)}\n\n"

    except Exception as e:
        error_msg = f"诊断过程出错: {str(e)}"
        yield f"data: {json.dumps({'type': 'error', 'message': error_msg}, ensure_ascii=False)}\n\n"

        # 更新数据库记录为失败
        await diagnosis_log.update_result(
            diagnosis_result=error_msg,
            status="failed",
            connectivity_status=True,
            error_message=str(e)
        )


@router.get("/diagnose-stream", summary="创建AI诊断（流式输出）")
async def create_diagnosis_stream(
    device_id: int = Query(..., description="设备ID"),
    problem_description: str = Query(..., description="问题描述"),
    current_user: User = Depends(AuthManager.get_current_user_from_query)
):
    """
    创建AI诊断任务（SSE 流式输出）- GET方式支持EventSource
    1. 检查设备是否存在
    2. 检查设备连通性
    3. 如果连通，通过 SSE 流式返回诊断过程和结果
    4. 保存诊断日志
    """
    try:
        # 1. 检查设备是否存在
        device = await Device.filter(id=device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="设备不存在")

        # 2. 检查设备连通性
        connectivity_status = await connectivity_manager.get_connectivity_status(device.id)

        if not connectivity_status or not connectivity_status.get("status"):
            # 设备不可连通，返回错误
            raise HTTPException(status_code=400, detail="设备当前不可连通，无法进行诊断")

        # 3. 创建诊断日志
        diagnosis_log = await AIDiagnosisLog.create_log(
            device_id=device.id,
            device_ip=device.ip,
            user_id=current_user.id,
            employee_id=current_user.employee_id,
            username=current_user.username,
            problem_description=problem_description
        )

        # 4. 返回 SSE 流
        return StreamingResponse(
            generate_diagnosis_stream(
                device, problem_description, diagnosis_log, connectivity_status),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"AI诊断失败: {e}")
        raise HTTPException(status_code=500, detail=f"诊断失败: {str(e)}")


@router.post("/diagnose", response_model=BaseResponse, summary="创建AI诊断")
async def create_diagnosis(
    diagnosis_data: AIDiagnosisCreate,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """
    创建AI诊断任务
    1. 检查设备是否存在
    2. 检查设备连通性
    3. 如果连通，返回初步诊断结果（暂时只返回连通性信息）
    4. 保存诊断日志
    """
    try:
        # 1. 检查设备是否存在
        device = await Device.filter(id=diagnosis_data.device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="设备不存在")

        # 2. 创建诊断日志
        diagnosis_log = await AIDiagnosisLog.create_log(
            device_id=device.id,
            device_ip=device.ip,
            user_id=current_user.id,
            employee_id=current_user.employee_id,
            username=current_user.username,
            problem_description=diagnosis_data.problem_description
        )

        # 3. 检查设备连通性
        connectivity_status = await connectivity_manager.get_connectivity_status(device.id)

        if not connectivity_status or not connectivity_status.get("status"):
            # 设备不可连通
            result = f"""# 诊断结果

## 设备信息
- **设备名称**: {device.name}
- **设备IP**: {device.ip}
- **设备类型**: {device.device_type}

## 连通性检测
❌ **设备当前不可连通**

无法建立与设备的网络连接，请检查：
1. 设备是否在线
2. 网络连接是否正常
3. IP地址是否正确
4. 防火墙设置是否允许访问

---
*诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
            await diagnosis_log.update_result(
                diagnosis_result=result,
                status="failed",
                connectivity_status=False,
                error_message="设备不可连通"
            )

            return BaseResponse(
                code=200,
                message="诊断完成，设备不可连通",
                data={
                    "id": diagnosis_log.id,
                    "status": "failed",
                    "connectivity_status": False,
                    "diagnosis_result": result
                }
            )

        # 4. 设备可连通，返回初步诊断结果
        last_ping = connectivity_status.get("last_ping")
        last_ping_str = last_ping.strftime(
            '%Y-%m-%d %H:%M:%S') if last_ping else "未知"

        result = f"""# 诊断结果

## 设备信息
- **设备名称**: {device.name}
- **设备IP**: {device.ip}
- **设备类型**: {device.device_type}
- **所属项目**: {device.project_name or "未设置"}

## 连通性检测
✅ **设备连通正常**
- 最后检测时间: {last_ping_str}

## 问题描述
{diagnosis_data.problem_description}

## 初步分析
设备网络连接正常，可以进行进一步诊断。

> **注意**: AI 诊断功能正在开发中，当前仅返回设备连通性信息。
> 后续将支持通过 AI 分析系统日志、性能指标等信息，提供详细的故障诊断建议。

### 建议操作
1. 检查系统日志: `journalctl -xe`
2. 查看系统资源使用情况: `top` 或 `htop`
3. 检查磁盘空间: `df -h`
4. 查看网络连接: `netstat -tuln`

---
*诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        await diagnosis_log.update_result(
            diagnosis_result=result,
            status="success",
            connectivity_status=True
        )

        return BaseResponse(
            code=200,
            message="诊断完成",
            data={
                "id": diagnosis_log.id,
                "status": "success",
                "connectivity_status": True,
                "diagnosis_result": result
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"AI诊断失败: {e}")
        raise HTTPException(status_code=500, detail=f"诊断失败: {str(e)}")


@router.get("/history", response_model=BaseResponse, summary="获取诊断历史")
async def get_diagnosis_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    device_ip: Optional[str] = Query(None, description="设备IP筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(AuthManager.get_current_user)
):
    """获取AI诊断历史列表"""
    try:
        # 构建查询条件
        query = AIDiagnosisLog.all()

        # 筛选条件
        if device_ip:
            query = query.filter(device_ip__icontains=device_ip)
        if status:
            query = query.filter(status=status)

        # 获取总数
        total = await query.count()

        # 分页查询
        offset = (page - 1) * page_size
        logs = await query.offset(offset).limit(page_size).order_by('-created_at')

        # 构建返回数据
        items = []
        for log in logs:
            items.append(AIDiagnosisListItem(
                id=log.id,
                device_ip=log.device_ip,
                username=log.username,
                problem_description=log.problem_description,
                status=log.status,
                connectivity_status=log.connectivity_status,
                created_at=log.created_at,
                completed_at=log.completed_at
            ))

        return BaseResponse(
            code=200,
            message="获取诊断历史成功",
            data={
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        )

    except Exception as e:
        print(f"获取诊断历史失败: {e}")
        raise HTTPException(status_code=500, detail="获取诊断历史失败")


@router.get("/history/{diagnosis_id}", response_model=BaseResponse, summary="获取诊断详情")
async def get_diagnosis_detail(
    diagnosis_id: int,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """获取单个诊断的详细信息"""
    try:
        diagnosis = await AIDiagnosisLog.filter(id=diagnosis_id).first()
        if not diagnosis:
            raise HTTPException(status_code=404, detail="诊断记录不存在")

        diagnosis_data = AIDiagnosisResponse(
            id=diagnosis.id,
            device_id=diagnosis.device_id,
            device_ip=diagnosis.device_ip,
            user_id=diagnosis.user_id,
            employee_id=diagnosis.employee_id,
            username=diagnosis.username,
            problem_description=diagnosis.problem_description,
            diagnosis_result=diagnosis.diagnosis_result,
            status=diagnosis.status,
            connectivity_status=diagnosis.connectivity_status,
            error_message=diagnosis.error_message,
            created_at=diagnosis.created_at,
            completed_at=diagnosis.completed_at
        )

        return BaseResponse(
            code=200,
            message="获取诊断详情成功",
            data=diagnosis_data
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"获取诊断详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取诊断详情失败")


@router.get("/export/{diagnosis_id}", summary="导出诊断结果")
async def export_diagnosis(
    diagnosis_id: int,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """导出诊断结果为Markdown文件"""
    try:
        diagnosis = await AIDiagnosisLog.filter(id=diagnosis_id).first()
        if not diagnosis:
            raise HTTPException(status_code=404, detail="诊断记录不存在")

        # 构建导出内容
        content = f"""# AI 诊断报告

**诊断ID**: {diagnosis.id}
**设备IP**: {diagnosis.device_ip}
**诊断人员**: {diagnosis.username} ({diagnosis.employee_id})
**诊断时间**: {diagnosis.created_at.strftime('%Y-%m-%d %H:%M:%S')}
**完成时间**: {diagnosis.completed_at.strftime('%Y-%m-%d %H:%M:%S') if diagnosis.completed_at else '未完成'}
**诊断状态**: {diagnosis.status}

---

{diagnosis.diagnosis_result or '暂无诊断结果'}
"""

        # 生成文件名
        filename = f"diagnosis_{diagnosis.id}_{diagnosis.device_ip}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        # 返回文件流
        return StreamingResponse(
            iter([content.encode('utf-8')]),
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"导出诊断结果失败: {e}")
        raise HTTPException(status_code=500, detail="导出诊断结果失败")


@router.delete("/history/{diagnosis_id}", response_model=BaseResponse, summary="删除诊断记录")
async def delete_diagnosis(
    diagnosis_id: int,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """删除诊断记录（仅创建人或管理员可删除）"""
    try:
        diagnosis = await AIDiagnosisLog.filter(id=diagnosis_id).first()
        if not diagnosis:
            raise HTTPException(status_code=404, detail="诊断记录不存在")

        # 权限检查：只有创建人或管理员可以删除
        is_creator = diagnosis.user_id == current_user.id
        is_admin = current_user.is_superuser or (await current_user.has_role("管理员"))

        if not (is_creator or is_admin):
            raise HTTPException(
                status_code=403,
                detail="权限不足，只有创建人或管理员可以删除诊断记录"
            )

        await diagnosis.delete()

        return BaseResponse(
            code=200,
            message="诊断记录删除成功",
            data=None
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"删除诊断记录失败: {e}")
        raise HTTPException(status_code=500, detail="删除诊断记录失败")
