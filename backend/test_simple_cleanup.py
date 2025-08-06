#!/usr/bin/env python3
"""
简单测试定期清理功能的时间比较逻辑
"""
from datetime import datetime, timedelta


def get_current_time():
    """获取当前时间，统一使用naive datetime"""
    return datetime.now()


def test_time_comparison():
    """测试时间比较逻辑"""
    print("测试时间比较逻辑...")
    
    current_time = get_current_time()
    print(f"当前时间: {current_time}")
    
    # 测试1：未到期的长时间占用
    future_end_date = current_time + timedelta(hours=2)
    print(f"\n测试1 - 未到期的长时间占用:")
    print(f"截至时间: {future_end_date}")
    print(f"是否到期: {future_end_date <= current_time}")
    print(f"应该跳过: {future_end_date > current_time}")
    
    # 测试2：已到期的长时间占用
    past_end_date = current_time - timedelta(minutes=30)
    print(f"\n测试2 - 已到期的长时间占用:")
    print(f"截至时间: {past_end_date}")
    print(f"是否到期: {past_end_date <= current_time}")
    print(f"应该清理: {past_end_date <= current_time}")
    
    # 测试3：刚好到期的长时间占用
    exact_end_date = current_time
    print(f"\n测试3 - 刚好到期的长时间占用:")
    print(f"截至时间: {exact_end_date}")
    print(f"是否到期: {exact_end_date <= current_time}")
    print(f"应该清理: {exact_end_date <= current_time}")
    
    print("\n✅ 时间比较逻辑测试完成")


def test_cleanup_logic():
    """测试清理逻辑"""
    print("\n测试清理逻辑...")
    
    current_time = get_current_time()
    
    # 模拟设备使用信息
    test_cases = [
        {
            "name": "未到期长时间占用",
            "is_long_term": True,
            "end_date": current_time + timedelta(hours=2),
            "should_skip": True
        },
        {
            "name": "已到期长时间占用",
            "is_long_term": True,
            "end_date": current_time - timedelta(minutes=30),
            "should_skip": False
        },
        {
            "name": "普通占用",
            "is_long_term": False,
            "end_date": None,
            "should_skip": False
        },
        {
            "name": "长时间占用但无截至时间",
            "is_long_term": True,
            "end_date": None,
            "should_skip": False
        }
    ]
    
    for case in test_cases:
        print(f"\n测试案例: {case['name']}")
        print(f"是否长时间占用: {case['is_long_term']}")
        print(f"截至时间: {case['end_date']}")
        
        # 模拟清理逻辑
        should_skip = False
        if case['is_long_term'] and case['end_date']:
            end_date = case['end_date'].replace(tzinfo=None) if case['end_date'].tzinfo else case['end_date']
            if end_date > current_time:
                should_skip = True
                print(f"跳过长时间占用设备，截至时间：{case['end_date']}")
            else:
                print(f"长时间占用设备已到期，开始清理，截至时间：{case['end_date']}")
        
        print(f"预期结果: {'跳过' if case['should_skip'] else '清理'}")
        print(f"实际结果: {'跳过' if should_skip else '清理'}")
        print(f"测试结果: {'✅ 通过' if should_skip == case['should_skip'] else '❌ 失败'}")
    
    print("\n✅ 清理逻辑测试完成")


if __name__ == "__main__":
    test_time_comparison()
    test_cleanup_logic()
