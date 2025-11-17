"""
命令行集路由
提供命令行的增删改查等API接口
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import datetime

from models.commandModel import Command, CommandOperationLog
from models.admin import User
from schemas import (
    CommandCreate, CommandUpdate, CommandResponse, CommandListItem, BaseResponse
)
from auth import AuthManager

router = APIRouter(prefix="/api/commands", tags=["命令行集"])


@router.get("/", response_model=BaseResponse, summary="获取命令行列表")
async def get_commands(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    command_keyword: Optional[str] = Query(None, description="命令内容搜索关键词"),
    remarks_keyword: Optional[str] = Query(None, description="备注内容搜索关键词"),
    current_user: User = Depends(AuthManager.get_current_user)
):
    """
    获取命令行列表
    - 支持分页
    - 支持按命令内容和备注内容搜索
    - 如果命令内容为空，则搜索备注
    - 如果备注内容为空，则搜索命令内容
    - 如果都为空，则不搜索
    - 如果都不为空，则同时考虑两个条件（AND关系）
    """
    # 构建查询条件
    query = Command.all()

    # 根据搜索关键词进行过滤
    has_command_keyword = command_keyword and command_keyword.strip()
    has_remarks_keyword = remarks_keyword and remarks_keyword.strip()
    
    if has_command_keyword and has_remarks_keyword:
        # 两个都不为空，同时考虑两个条件
        query = query.filter(
            command_text__icontains=command_keyword.strip(),
            remarks__icontains=remarks_keyword.strip()
        )
    elif has_command_keyword:
        # 只有命令内容关键词
        query = query.filter(command_text__icontains=command_keyword.strip())
    elif has_remarks_keyword:
        # 只有备注内容关键词
        query = query.filter(remarks__icontains=remarks_keyword.strip())
    # 如果都为空，则不添加过滤条件

    # 获取总数
    total = await query.count()
    
    # 分页查询
    offset = (page - 1) * page_size
    commands = await query.offset(offset).limit(page_size).order_by('-updated_at')

    # 构建返回数据
    result = []
    for command in commands:
        result.append(CommandListItem(
            id=command.id,
            command_text=command.command_text,
            link=command.link,
            remarks=command.remarks,
            last_editor=command.last_editor,
            updated_at=command.updated_at
        ))

    return BaseResponse(
        code=200,
        message="命令行列表获取成功",
        data={
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    )


@router.post("/", response_model=BaseResponse, summary="创建命令行")
async def create_command(
    command_data: CommandCreate,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """创建新命令行"""
    try:
        # 创建命令行
        command = await Command.create(
            command_text=command_data.command_text,
            link=command_data.link,
            remarks=command_data.remarks,
            creator=current_user.employee_id
        )

        # 构建响应数据
        command_response = {
            "id": command.id,
            "command_text": command.command_text,
            "link": command.link,
            "remarks": command.remarks,
            "creator": command.creator,
            "last_editor": command.last_editor,
            "created_at": command.created_at,
            "updated_at": command.updated_at
        }

        return BaseResponse(
            code=200,
            message="命令行创建成功",
            data=command_response
        )

    except Exception as e:
        print(f"创建命令行失败: {e}")
        raise HTTPException(status_code=500, detail="创建命令行失败")


@router.get("/operation-logs", response_model=BaseResponse, summary="获取命令行操作日志")
async def get_command_operation_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    employee_id: Optional[str] = Query(None, description="工号"),
    current_user: User = Depends(AuthManager.get_current_user)
):
    """获取命令行操作日志列表"""
    try:
        query = CommandOperationLog.all()

        if employee_id:
            query = query.filter(employee_id__icontains=employee_id)

        total = await query.count()
        offset = (page - 1) * page_size
        logs = await query.offset(offset).limit(page_size).order_by('-created_at')

        items = []
        for log in logs:
            items.append({
                "id": log.id,
                "command_id": log.command_id,
                "employee_id": log.employee_id,
                "username": log.username,
                "operation_type": log.operation_type,
                "operation_result": log.operation_result,
                "description": log.description,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None
            })

        return BaseResponse(
            code=200,
            message="命令行操作日志获取成功",
            data={
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        )

    except Exception as e:
        print(f"获取命令行操作日志失败: {e}")
        return BaseResponse(
            code=200,
            message="暂无命令行操作日志",
            data={
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size
            }
        )


@router.get("/{command_id:int}", response_model=BaseResponse, summary="获取命令行详情")
async def get_command(
    command_id: int,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """根据ID获取命令行详情"""
    command = await Command.filter(id=command_id).first()
    if not command:
        raise HTTPException(status_code=404, detail="命令行不存在")

    command_data = {
        "id": command.id,
        "command_text": command.command_text,
        "link": command.link,
        "remarks": command.remarks,
        "creator": command.creator,
        "last_editor": command.last_editor,
        "created_at": command.created_at,
        "updated_at": command.updated_at
    }

    return BaseResponse(
        code=200,
        message="命令行详情获取成功",
        data=command_data
    )


@router.put("/{command_id:int}", response_model=BaseResponse, summary="更新命令行")
async def update_command(
    command_id: int,
    command_data: CommandUpdate,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """更新命令行信息"""
    command = await Command.filter(id=command_id).first()
    if not command:
        raise HTTPException(status_code=404, detail="命令行不存在")

    # 记录旧值用于日志
    old_values = {
        "command_text": command.command_text,
        "link": command.link,
        "remarks": command.remarks
    }

    # 更新字段
    update_data = command_data.dict(exclude_unset=True)
    if update_data:
        for key, value in update_data.items():
            setattr(command, key, value)
        
        # 更新最后编辑人
        command.last_editor = current_user.employee_id
        await command.save()

        # 记录命令行操作日志
        changes = []
        if command_data.command_text and command_data.command_text != old_values["command_text"]:
            changes.append("命令内容")
        if command_data.link is not None and command_data.link != old_values["link"]:
            changes.append("链接")
        if command_data.remarks is not None and command_data.remarks != old_values["remarks"]:
            changes.append("备注")

        if changes:
            await CommandOperationLog.create_log(
                command_id=command.id,
                user=current_user,
                operation_type="command_update",
                operation_result="success",
                description=f"更新命令行 ID:{command.id}，修改了：{', '.join(changes)}"
            )

    # 重新获取命令行信息
    command = await Command.filter(id=command_id).first()
    
    command_response = {
        "id": command.id,
        "command_text": command.command_text,
        "link": command.link,
        "remarks": command.remarks,
        "creator": command.creator,
        "last_editor": command.last_editor,
        "created_at": command.created_at,
        "updated_at": command.updated_at
    }

    return BaseResponse(
        code=200,
        message="命令行更新成功",
        data=command_response
    )


@router.delete("/{command_id:int}", response_model=BaseResponse, summary="删除命令行")
async def delete_command(
    command_id: int,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """删除命令行，只有创建人或管理员可以删除"""
    command = await Command.filter(id=command_id).first()
    if not command:
        raise HTTPException(status_code=404, detail="命令行不存在")
    
    # 权限检查：只有创建人或管理员可以删除
    is_creator = command.creator == current_user.employee_id
    is_admin = current_user.is_superuser or (await current_user.has_role("管理员"))
    
    if not (is_creator or is_admin):
        raise HTTPException(
            status_code=403,
            detail="权限不足，只有创建人或管理员可以删除命令行"
        )
    
    # 删除命令行
    await command.delete()
    
    return BaseResponse(
        code=200,
        message="命令行删除成功",
        data=None
    )
