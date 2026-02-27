class TradingService:
    def __init__(self):
        pass
    
    def get_account_info(self):
        return {"balance": 0.0, "equity": 0.0}
    
    def get_open_positions(self):
        return []
    
    def get_pending_orders(self):
        return []
    
    def place_order(self, **kwargs):
        return {"status": "success", "order_id": "dummy"}
    
    def close_position(self, **kwargs):
        return {"status": "success"}
    
    def modify_order(self, **kwargs):
        return {"status": "success"}
    
    def cancel_order(self, **kwargs):
        return {"status": "success"}
