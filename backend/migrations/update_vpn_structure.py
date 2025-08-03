"""
更新VPN表结构的数据库迁移脚本
将name和description字段改为region和network字段
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from config import settings

async def migrate():
    """执行数据库迁移"""
    # 初始化数据库连接
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["models.admin", "models.deviceModel", "models.systemModel", "models.vpnModel"]}
    )
    
    # 获取数据库连接
    conn = Tortoise.get_connection("default")
    
    try:
        print("开始更新VPN表结构...")
        
        # 检查vpn_configs表是否存在
        result = await conn.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='vpn_configs';")
        
        if result[1]:  # 表存在
            print("vpn_configs表已存在，开始更新结构...")
            
            # 创建新表结构
            await conn.execute_query("""
                CREATE TABLE vpn_configs_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    region VARCHAR(50) NOT NULL,
                    network VARCHAR(50) NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(region, network)
                );
            """)
            print("创建新表结构完成")
            
            # 迁移现有数据（如果有的话）
            try:
                await conn.execute_query("""
                    INSERT INTO vpn_configs_new (id, region, network, is_active, created_at, updated_at)
                    SELECT id, 
                           COALESCE(name, 'Default') as region,
                           'Default' as network,
                           is_active, 
                           created_at, 
                           updated_at
                    FROM vpn_configs;
                """)
                print("数据迁移完成")
            except Exception as e:
                print(f"数据迁移失败（可能是空表）: {e}")
            
            # 删除旧表
            await conn.execute_query("DROP TABLE vpn_configs;")
            print("删除旧表完成")
            
            # 重命名新表
            await conn.execute_query("ALTER TABLE vpn_configs_new RENAME TO vpn_configs;")
            print("重命名新表完成")
            
        else:
            print("vpn_configs表不存在，将由模型自动创建")
        
        # 检查user_vpn_configs表是否存在，如果存在则清空（因为结构变化）
        result = await conn.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='user_vpn_configs';")
        if result[1]:
            await conn.execute_query("DELETE FROM user_vpn_configs;")
            print("清空user_vpn_configs表数据")
        
        print("VPN表结构更新完成！")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        raise
    finally:
        # 关闭数据库连接
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(migrate())
