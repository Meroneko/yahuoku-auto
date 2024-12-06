from config.config_manager import ConfigManager
from core.browser import BrowserManager
from gui.main_window import MainWindow

def main():
    config_manager = ConfigManager()
    browser_manager = BrowserManager()
    
    window = MainWindow(config_manager, browser_manager)
    window.run()

if __name__ == "__main__":
    main() 