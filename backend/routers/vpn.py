"""
VPN配置管理路由
提供VPN配置的增删改查和用户VPN IP配置管理API接口
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from models.admin import User
from models.vpnModel import VPNConfig, UserVPNConfig
from schemas import (
    BaseResponse, VPNConfigCreate, VPNConfigUpdate, VPNConfigResponse,
    UserVPNConfigUpdate, UserVPNConfigResponse
)
from auth import AuthManager, require_permission

router = APIRouter(prefix="/vpn", tags=["VPN配置管理"])


# ===== 管理员VPN配置管理 =====

@router.get("/configs", response_model=BaseResponse, summary="获取VPN配置列表")
async def get_vpn_configs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    region: Optional[str] = Query(None, description="地域搜索"),
    network: Optional[str] = Query(None, description="网段搜索"),
    current_user: User = Depends(AuthManager.get_current_user)
):
    """获取VPN配置列表（管理员）"""
    try:
        # 构建查询条件
        query = VPNConfig.all()

        if region:
            query = query.filter(region__icontains=region)
        if network:
            query = query.filter(network__icontains=network)

        # 分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        configs = await query.offset(offset).limit(page_size).order_by('id')

        # 转换为响应格式
        items = []
        for config in configs:
            items.append(VPNConfigResponse(
                id=config.id,
                region=config.region,
                network=config.network
            ))

        return BaseResponse(
            code=200,
            message="获取VPN配置列表成功",
            data={
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        )
    except Exception as e:
        print(f"获取VPN配置列表失败: {e}")
        return BaseResponse(
            code=500,
            message="获取VPN配置列表失败",
            data=None
        )


@router.post("/configs", response_model=BaseResponse, summary="创建VPN配置")
async def create_vpn_config(
    config_data: VPNConfigCreate,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """创建VPN配置（管理员）"""
    try:
        # 检查地域和网段组合是否已存在
        existing_config = await VPNConfig.filter(
            region=config_data.region,
            network=config_data.network
        ).first()
        if existing_config:
            return BaseResponse(
                code=400,
                message="该地域和网段组合已存在",
                data=None
            )

        # 创建VPN配置
        config = await VPNConfig.create(
            region=config_data.region,
            network=config_data.network
        )

        return BaseResponse(
            code=200,
            message="创建VPN配置成功",
            data={
                "id": config.id,
                "region": config.region,
                "network": config.network
            }
        )
    except Exception as e:
        print(f"创建VPN配置失败: {e}")
        return BaseResponse(
            code=500,
            message="创建VPN配置失败",
            data=None
        )


@router.put("/configs/{config_id}", response_model=BaseResponse, summary="更新VPN配置")
async def update_vpn_config(
    config_id: int,
    config_data: VPNConfigUpdate,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """更新VPN配置（管理员）"""
    try:
        # 查找VPN配置
        config = await VPNConfig.filter(id=config_id).first()
        if not config:
            return BaseResponse(
                code=404,
                message="VPN配置不存在",
                data=None
            )

        # 检查地域和网段组合是否重复
        if (config_data.region is not None or config_data.network is not None):
            new_region = config_data.region if config_data.region is not None else config.region
            new_network = config_data.network if config_data.network is not None else config.network

            if new_region != config.region or new_network != config.network:
                existing_config = await VPNConfig.filter(
                    region=new_region,
                    network=new_network
                ).first()
                if existing_config:
                    return BaseResponse(
                        code=400,
                        message="该地域和网段组合已存在",
                        data=None
                    )

        # 更新配置
        update_data = {}
        if config_data.region is not None:
            update_data["region"] = config_data.region
        if config_data.network is not None:
            update_data["network"] = config_data.network

        if update_data:
            await VPNConfig.filter(id=config_id).update(**update_data)

        return BaseResponse(
            code=200,
            message="更新VPN配置成功",
            data={"id": config_id}
        )
    except Exception as e:
        print(f"更新VPN配置失败: {e}")
        return BaseResponse(
            code=500,
            message="更新VPN配置失败",
            data=None
        )


@router.delete("/configs/{config_id}", response_model=BaseResponse, summary="删除VPN配置")
async def delete_vpn_config(
    config_id: int,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """删除VPN配置（管理员）"""
    try:
        # 查找VPN配置
        config = await VPNConfig.filter(id=config_id).first()
        if not config:
            return BaseResponse(
                code=404,
                message="VPN配置不存在",
                data=None
            )
        
        # 检查是否有用户配置使用此VPN
        user_configs_count = await UserVPNConfig.filter(vpn_config=config).count()
        if user_configs_count > 0:
            return BaseResponse(
                code=400,
                message=f"无法删除，还有 {user_configs_count} 个用户配置使用此VPN",
                data=None
            )
        
        # 删除VPN配置
        await config.delete()
        
        return BaseResponse(
            code=200,
            message="删除VPN配置成功",
            data={"id": config_id}
        )
    except Exception as e:
        print(f"删除VPN配置失败: {e}")
        return BaseResponse(
            code=500,
            message="删除VPN配置失败",
            data=None
        )


# ===== 用户VPN IP配置管理 =====

@router.get("/user-configs", response_model=BaseResponse, summary="获取当前用户的VPN配置")
async def get_user_vpn_configs(
    current_user: User = Depends(AuthManager.get_current_user)
):
    """获取当前用户的VPN配置"""
    try:
        # 获取所有VPN配置
        vpn_configs = await VPNConfig.all().order_by('region', 'network')

        # 获取用户的VPN IP配置
        user_configs = await UserVPNConfig.filter(user=current_user).prefetch_related('vpn_config')
        user_config_dict = {uc.vpn_config.id: uc for uc in user_configs}

        # 构建响应数据
        items = []
        for vpn_config in vpn_configs:
            user_config = user_config_dict.get(vpn_config.id)
            items.append(UserVPNConfigResponse(
                id=user_config.id if user_config else 0,
                vpn_config_id=vpn_config.id,
                vpn_region=vpn_config.region,
                vpn_network=vpn_config.network,
                ip_address=user_config.ip_address if user_config else None
            ))
        
        return BaseResponse(
            code=200,
            message="获取用户VPN配置成功",
            data=items
        )
    except Exception as e:
        print(f"获取用户VPN配置失败: {e}")
        return BaseResponse(
            code=500,
            message="获取用户VPN配置失败",
            data=None
        )


@router.put("/user-configs/{vpn_config_id}", response_model=BaseResponse, summary="更新用户VPN IP配置")
async def update_user_vpn_config(
    vpn_config_id: int,
    config_data: UserVPNConfigUpdate,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """更新用户VPN IP配置"""
    try:
        # 检查VPN配置是否存在
        vpn_config = await VPNConfig.filter(id=vpn_config_id).first()
        if not vpn_config:
            return BaseResponse(
                code=404,
                message="VPN配置不存在",
                data=None
            )

        # 查找或创建用户VPN配置
        user_config = await UserVPNConfig.filter(user=current_user, vpn_config=vpn_config).first()

        if user_config:
            # 更新现有配置
            user_config.ip_address = config_data.ip_address
            await user_config.save()
        else:
            # 创建新配置
            user_config = await UserVPNConfig.create(
                user=current_user,
                vpn_config=vpn_config,
                ip_address=config_data.ip_address
            )

        return BaseResponse(
            code=200,
            message="更新VPN IP配置成功",
            data={
                "vpn_config_id": vpn_config_id,
                "ip_address": config_data.ip_address
            }
        )
    except Exception as e:
        print(f"更新用户VPN配置失败: {e}")
        return BaseResponse(
            code=500,
            message="更新用户VPN配置失败",
            data=None
        )


# ===== IP搜索功能 =====

@router.get("/search-ip", response_model=BaseResponse, summary="根据IP地址搜索用户VPN配置")
async def search_user_by_ip(
    ip_address: str = Query(..., description="要搜索的IP地址"),
    current_user: User = Depends(AuthManager.get_current_user)
):
    """根据IP地址搜索用户VPN配置（管理员）"""
    try:
        # 搜索包含该IP地址的用户VPN配置
        user_configs = await UserVPNConfig.filter(
            ip_address__icontains=ip_address
        ).prefetch_related('user', 'vpn_config')

        # 构建响应数据
        results = []
        for config in user_configs:
            results.append({
                "employee_id": config.user.employee_id,
                "username": config.user.username,
                "region": config.vpn_config.region,
                "network": config.vpn_config.network,
                "ip_address": config.ip_address
            })

        return BaseResponse(
            code=200,
            message=f"搜索到 {len(results)} 条匹配记录",
            data=results
        )
    except Exception as e:
        print(f"IP搜索失败: {e}")
        return BaseResponse(
            code=500,
            message="IP搜索失败",
            data=None
        )
