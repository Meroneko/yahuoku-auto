import requests
from bs4 import BeautifulSoup
import json
import time
import warnings

def get_fare_data(from_addr, to_addr):
    """发送请求获取运费数据"""
    # ヤマトの運賃表
    url = "https://form.008008.jp/mitumori/PKZI1100Action_doSearch.action"
    
    headers = {
        "Host": "form.008008.jp",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://form.008008.jp",
        "Connection": "keep-alive",
        "Referer": "https://form.008008.jp/mitumori/PKZI1100Action_doSearch.action",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Priority": "u=0, i"
    }
    
    data = {
        "add_g1_search": from_addr,
        "del_add_g1_search": to_addr,
        "sp_kbn": "",
        "execution.x": "33",
        "execution.y": "8"
    }
    
    try:
        # 使用session来维持cookie
        session = requests.Session()
        response = session.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

def parse_fare_table(html):
    """解析运费表格数据"""
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', {'class': 'result'})
    
    fare_data = {}
    unknown_ranks = []  # 记录未知价格的等级
    
    # 跳过表头行
    for row in table.find_all('tr')[1:]:
        # 获取等级和价格
        cells = row.find_all('td')
        if len(cells) >= 3:
            # 从dt标签中获取等级
            rank = cells[0].find('dt').text.replace('ランク', '')
            # 获取价格文本
            price_text = cells[2].text.replace('円', '').replace(',', '')
            
            # 处理没有价格的情况
            if price_text.strip() == '----':
                price = "unknown"
                unknown_ranks.append(rank)  # 记录未知价格的等级
            else:
                price = int(price_text)
                
            fare_data[rank] = price
            
    return fare_data, unknown_ranks

def main():
    # 读取地址列表
    with open("address_list.txt", "r", encoding="utf-8") as f:
        addresses = f.read().splitlines()
    
    # 初始化结果字典和未知价格记录
    result = {"ヤマト": {"料金表": {}}}
    unknown_prices = {}  # 记录每个地址的未知价格情况
    
    # 固定发送地址为東京都
    from_addr = "東京都"
    
    # 循环获取每个地址的运费
    for to_addr in addresses:
        print(f"正在获取 {from_addr} -> {to_addr} 的运费...")
        html = get_fare_data(from_addr, to_addr)
        
        if html:
            fare_data, unknown_ranks = parse_fare_table(html)
            result["ヤマト"]["料金表"][to_addr] = fare_data
            if unknown_ranks:  # 如果有未知价格，记录下来
                unknown_prices[to_addr] = unknown_ranks
        
        # 添加延时避免请求过快
        time.sleep(1)
    
    # 保存结果到JSON文件
    with open("new_fare_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 输出未知价格的警告信息
    if unknown_prices:
        warning_msg = "\n未能获取到以下地址的运费价格:\n"
        for addr, ranks in unknown_prices.items():
            warning_msg += f"{addr}: {', '.join(ranks)}ランク\n"
        warnings.warn(warning_msg)

if __name__ == "__main__":
    main()
