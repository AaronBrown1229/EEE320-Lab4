from constants import TABLES, MENU_ITEMS


class Restaurant:

    def __init__(self):
        super().__init__()
        self.tables = [Table(seats, loc) for seats, loc in TABLES]
        self.menu_items = [MenuItem(name, price) for name, price in MENU_ITEMS]
        self.views = []

    def add_view(self, view):
        self.views.append(view)

    def notify_views(self):
        for view in self.views:
            view.update()


class Table:

    def __init__(self, seats, location):
        self.n_seats = seats
        self.location = location
        self.orders = [Order() for _ in range(seats)]

    def has_any_active_orders(self):
        for order in self.orders:
            for item in order.items:
                if item.has_been_ordered() and not item.has_been_served():
                    return True
        return False

    def has_order_for(self, seat):
        return bool(self.orders[seat].items)

    def order_for(self, seat):
        return self.orders[seat]


class Order:

    def __init__(self):
        self.items = []

    def add_item(self, menu_item):
        item = OrderItem(menu_item)
        self.items.append(item)

    def remove_item(self, item):
        self.items.remove(item)

    def place_new_orders(self):
        for item in self.unordered_items():
            item.mark_as_ordered()

    def remove_unordered_items(self):
        for item in self.unordered_items():
            self.items.remove(item)

    def unordered_items(self):
        return [item for item in self.items if not item.has_been_ordered()]

    def total_cost(self):
        return sum((item.details.price for item in self.items))


class OrderItem:

    # TODO: need to represent item state, not just ordered

    def __init__(self, menu_item):
        self.details = menu_item

        """
        0: not ordered
        1: marked as ordered
        2: marked as cooking
        3: marked as ready
        4: marked as served
        """
        self.__ordered = 0

    def mark_as_ordered(self):
        self.__ordered = 1

    def next_state(self, item):
        self.__ordered += 1

    def has_been_ordered(self):
        # if the state is 1 or more it has been ordered
        return self.__ordered >= 1

    def has_been_served(self):
        # TODO: correct implementation based on item state
        # TODONE
        # if on step 4 the item has been served
        return self.__ordered == 4

    def can_be_cancelled(self):
        # TODO: correct implementation based on item state
        # TODONE
        # if on a step less than cooking the item can be cancelled
        return self.__ordered < 2

    # used to print the correct text on the buttons in Kitchen view
    def ordered_state(self):
        return self.__ordered

class MenuItem:

    def __init__(self, name, price):
        self.name = name
        self.price = price
