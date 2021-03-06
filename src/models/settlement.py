
from decimal import Decimal
import json
import web3
from src.models.order import Order, OrdersSerializedType
from src.models.token import (
    Token,
)
from typing import Any, Optional

class InteractionData:

    def __init__(
        self,
        target: str,
        call_data: str,
    ):
        self.value = '0'
        self.target = target
        self.call_data = call_data

    def as_dict(self) :
        """Return Order object as dictionary."""
        return  {
                'target': str(self.target),
                'value': '0',
                'call_data': [ bytes for bytes in web3.Web3.toBytes(hexstr = self.call_data)]
                }
        
        

    def __dict__(self) -> str:
        """Represent as string."""
        return json.dumps(self.as_dict(), indent=2)


class Settlement:
    """Class to represent a batch auction."""

    def __init__(
        self,
        ref_token: str,
        name: str = "batch_auction",
        metadata: Optional[dict] = None,
    ):
        self.name = name
        self.metadata = metadata if metadata else {}
        self.interaction_data = []
        self.orders = []
        self.ref_token = ref_token
        self.prices = { ref_token: 1000000000000000000}
    
    def as_dict(self) :
        """Return Order object as dictionary."""
        # Currently, only limit buy or sell orders be handled.
        return {
            "name": str(self.name),
            "metadata": None,
            "orders": {order.order_id: order.as_dict() for order in self.orders},
            "interaction_data": [ interaction.as_dict() for interaction in self.interaction_data],
            "prices":{str(key): str(price) for key,price in self.prices.items()},
            "amms": {},
            "ref_token": str(self.ref_token)
        }

    def __dict__(self) -> str:
        """Represent as string."""
        return json.dumps(self.as_dict(), indent=2)

    def add_payload(self, target, call_data):
        data = InteractionData(target, call_data)
        self.interaction_data.append(data)

    def add_order(self, order):
        self.orders.append(order)

    def insert_prices(self, order, swap_result):
        if (str(order.sell_token) in self.prices )& (str(order.buy_token) in self.prices):
            return False
        elif ( str(order.sell_token) not in self.prices) & (str(order.buy_token) in self.prices):
            self.prices[str(order.sell_token)]=int(self.prices[str(order.buy_token)] *Decimal(swap_result['fromTokenAmount']) /Decimal(swap_result['toTokenAmount']))
        elif (str(order.sell_token) in self.prices) & (str(order.buy_token) not in self.prices):
            self.prices[str(order.buy_token)]= int(self.prices[str(order.sell_token)]*Decimal(swap_result['toTokenAmount']) / Decimal(swap_result['fromTokenAmount']))
        else:
            self.prices[str(order.buy_token)]= swap_result['toTokenAmount']
            self.prices[str(order.sell_token)]= str(int(Decimal(swap_result['fromTokenAmount'])*Decimal(1.0005)))
        return True

    