from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class BrowserManager:
    def __init__(self):
        self.active_browsers = {}
    
    def launch_browser(self, profile_name, profile_path):
        """启动指定配置的浏览器"""
        options = Options()
        options.add_argument(f"user-data-dir={profile_path}")
        
        browser = webdriver.Chrome(options=options)
        self.active_browsers[profile_name] = browser
        return browser
    
    def close_browser(self, profile_name):
        """关闭指定的浏览器"""
        if profile_name in self.active_browsers:
            self.active_browsers[profile_name].quit()
            del self.active_browsers[profile_name] 

class YahooAuctionManager:
    def __init__(self, browser):
        self.browser = browser
        self.base_url = "https://auctions.yahoo.co.jp/closeduser/jp/show/mystatus"
    
    def go_to_won_auctions(self):
        """访问已中标的商品页面"""
        try:
            # 访问已中标页面
            self.browser.get(f"{self.base_url}?select=won")
            
            # 等待页面加载完成
            wait = WebDriverWait(self.browser, 10)
            
            # 检查是否需要登录
            if "login" in self.browser.current_url.lower():
                print("需要登录，请手动登录后再试")
                return False
            
            # 检查URL是否正确（确保已经跳转到目标页面）
            if "select=won" not in self.browser.current_url:
                print("页面跳转失败")
                return False
            
            try:
                # 等待商品表格
                table_element = wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "ItemTable"))
                )
                
                # 检查是否有错误消息
                error_elements = self.browser.find_elements(By.CLASS_NAME, "Error")
                if error_elements and any(e.is_displayed() for e in error_elements):
                    print("页面显示错误信息")
                    return False
                
                print("页面加载成功")
                return True
                
            except TimeoutException:
                print("等待页面元素超时")
                return False
                
        except TimeoutException:
            print("页面加载超时")
            return False
        except Exception as e:
            print(f"访问页面时发生错误: {str(e)}")
            return False
    
    def check_login_status(self):
        """检查登录状态"""
        try:
            # 检查URL是否包含login
            if "login" in self.browser.current_url.lower():
                return False
            
            # 检查是否有登录按钮或登录表单
            login_elements = self.browser.find_elements(By.CLASS_NAME, "LoginForm")
            if login_elements and any(e.is_displayed() for e in login_elements):
                return False
            
            return True
            
        except Exception as e:
            print(f"检查登录状态时发生错误: {str(e)}")
            return False
    
    def get_won_items(self):
        """获取已中标商品列表"""
        try:
            # 等待商品列表加载
            items_table = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ItemTable"))
            )
            
            # 获取所有商品行
            items = []
            rows = items_table.find_elements(By.TAG_NAME, "tr")[1:]  # 跳过表头
            
            for row in rows:
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 6:  # 确保有足够的列
                        item = {
                            "item_id": cols[1].text.strip(),
                            "title": cols[2].text.strip(),
                            "price": cols[3].text.strip(),
                            "end_time": cols[4].text.strip(),
                            "status": cols[5].text.strip()
                        }
                        
                        # 获取商品链接
                        try:
                            item["url"] = cols[2].find_element(By.TAG_NAME, "a").get_attribute("href")
                        except:
                            item["url"] = ""
                            
                        items.append(item)
                except Exception as e:
                    print(f"解析商品行时发生错误: {str(e)}")
                    continue
            
            return items
            
        except TimeoutException:
            print("等待商品列表超时")
            return []
        except Exception as e:
            print(f"获取商品列表时发生错误: {str(e)}")
            return []

# 使用示例
def test_yahoo_auction():
    # 创建浏览器管理器
    browser_manager = BrowserManager()
    
    try:
        # 启动浏览器（使用指定配置）
        browser = browser_manager.launch_browser(
            "test2", 
            "C:\\Users\\royat\\AppData\\Local\\Google\\Chrome\\test2"
        )
        
        # 创建Yahoo拍卖管理器
        auction_manager = YahooAuctionManager(browser)
        
        # 访问已中标页面
        if auction_manager.go_to_won_auctions():
            print("成功访问已中标页面")
            
            # 获取商品列表
            items = auction_manager.get_won_items()
            
            # 打印商品信息
            for item in items:
                print("\n商品信息:")
                print(f"ID: {item['item_id']}")
                print(f"标题: {item['title']}")
                print(f"价格: {item['price']}")
                print(f"结束时间: {item['end_time']}")
                print(f"状态: {item['status']}")
                print(f"链接: {item['url']}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
    
    finally:
        # 关闭浏览器
        browser_manager.close_browser("test2")

if __name__ == "__main__":
    test_yahoo_auction() 