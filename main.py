from app import FinoraApp # Update with your actual import
from config import get_config

if __name__ == "__main__":
    # get_config() now returns an object, not just a class reference
    config_instance = get_config()
    
    app = FinoraApp(config_class=config_instance)
    app.run()