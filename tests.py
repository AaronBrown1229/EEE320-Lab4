import unittest
from enum import Enum, auto

from controller import RestaurantController, TableController, OrderController, KitchenController
from model import Restaurant, OrderItem


class UI(Enum):
    """
    Used by ServerViewMock to represent the last user interface that was
    drawn.
    """
    RESTAURANT = auto()
    TABLE = auto()
    ORDER = auto()


class ServerViewMock:
    """
    A non-graphical replacement for `oorms.ServerView`, used for testing. Allows
    tests to check what was the last user interface rendered. Fully replicates the
    public interface of `ServerView`. The `set_controller` and `update` methods
    are exact copies of those in `oorms.RestaurantView`.
    """

    def __init__(self, restaurant):
        self.controller = None
        self.last_UI_created = None
        self.restaurant = restaurant
        self.set_controller(RestaurantController(self, self.restaurant))
        self.update()

    def set_controller(self, controller):
        self.controller = controller

    def update(self):
        self.controller.create_ui()

    def create_restaurant_ui(self):
        self.last_UI_created = UI.RESTAURANT

    def create_table_ui(self, table):
        self.last_UI_created = (UI.TABLE, table)

    def create_order_ui(self, order):
        self.last_UI_created = (UI.ORDER, order)

    def create_kitchen_order_ui(self):
        pass


class OORMSTestCase(unittest.TestCase):

    def setUp(self):
        self.restaurant = Restaurant()
        self.view = ServerViewMock(self.restaurant)
        self.restaurant.add_view(self.view)

    def test_initial_state(self):
        self.assertEqual(UI.RESTAURANT, self.view.last_UI_created)
        self.assertIsInstance(self.view.controller, RestaurantController)

    def test_restaurant_controller_touch_table(self):
        self.view.controller.table_touched(3)
        self.assertIsInstance(self.view.controller, TableController)
        self.assertEqual(self.view.controller.table, self.restaurant.tables[3])
        self.assertEqual((UI.TABLE, self.restaurant.tables[3]), self.view.last_UI_created)

    def test_table_controller_done(self):
        self.view.controller.table_touched(5)
        self.view.controller.done()
        self.assertIsInstance(self.view.controller, RestaurantController)
        self.assertEqual(UI.RESTAURANT, self.view.last_UI_created)

    def test_table_controller_seat_touched(self):
        self.view.controller.table_touched(4)
        self.view.controller.seat_touched(0)
        self.assertIsInstance(self.view.controller, OrderController)
        self.assertEqual(self.view.controller.table, self.restaurant.tables[4])
        the_order = self.restaurant.tables[4].order_for(0)
        self.assertEqual(self.view.controller.order, the_order)
        self.assertEqual((UI.ORDER, the_order), self.view.last_UI_created)

    def order_an_item(self):
        """
        Starting from the restaurant UI, orders one instance of item 0
        for table 2, seat 4
        """
        self.view.controller.table_touched(2)
        self.view.controller.seat_touched(4)
        the_menu_item = self.restaurant.menu_items[0]
        self.view.last_UI_created = None
        self.view.controller.add_item(the_menu_item)
        return self.restaurant.tables[2].order_for(4), the_menu_item

    def test_order_controller_add_item(self):
        the_order, the_menu_item = self.order_an_item()
        self.assertIsInstance(self.view.controller, OrderController)
        self.assertEqual((UI.ORDER, the_order), self.view.last_UI_created)
        self.assertEqual(1, len(the_order.items))
        self.assertIsInstance(the_order.items[0], OrderItem)
        self.assertEqual(the_order.items[0].details, the_menu_item)
        self.assertFalse(the_order.items[0].has_been_ordered())

    def test_order_controller_update_order(self):
        the_order, the_menu_item = self.order_an_item()
        self.view.last_UI_created = None
        self.view.controller.update_order()
        self.assertEqual((UI.TABLE, self.restaurant.tables[2]), self.view.last_UI_created)
        self.assertEqual(1, len(the_order.items))
        self.assertIsInstance(the_order.items[0], OrderItem)
        self.assertEqual(the_order.items[0].details, the_menu_item)
        self.assertTrue(the_order.items[0].has_been_ordered())

    def test_order_controller_cancel(self):
        the_order, the_menu_item = self.order_an_item()
        self.view.last_UI_created = None
        self.view.controller.cancel_changes()
        self.assertEqual((UI.TABLE, self.restaurant.tables[2]), self.view.last_UI_created)
        self.assertEqual(0, len(the_order.items))

    def test_order_controller_update_several_then_cancel(self):
        self.view.controller.table_touched(6)
        self.view.controller.seat_touched(7)
        the_order = self.restaurant.tables[6].order_for(7)
        self.view.controller.add_item(self.restaurant.menu_items[0])
        self.view.controller.add_item(self.restaurant.menu_items[3])
        self.view.controller.add_item(self.restaurant.menu_items[5])
        self.view.controller.update_order()

        def check_first_three_items(menu_items, items):
            self.assertEqual(menu_items[0], items[0].details)
            self.assertEqual(menu_items[3], items[1].details)
            self.assertEqual(menu_items[5], items[2].details)

        self.assertEqual(3, len(the_order.items))
        check_first_three_items(self.restaurant.menu_items, the_order.items)

        def add_two_more(menu_items, view):
            view.controller.seat_touched(7)
            view.controller.add_item(menu_items[1])
            view.controller.add_item(menu_items[2])

        add_two_more(self.restaurant.menu_items, self.view)
        self.view.controller.cancel_changes()

        self.assertEqual(3, len(the_order.items))
        check_first_three_items(self.restaurant.menu_items, the_order.items)

        add_two_more(self.restaurant.menu_items, self.view)
        self.view.controller.update_order()

        self.assertEqual(5, len(the_order.items))
        check_first_three_items(self.restaurant.menu_items, the_order.items)
        self.assertEqual(self.restaurant.menu_items[1], the_order.items[3].details)
        self.assertEqual(self.restaurant.menu_items[2], the_order.items[4].details)

    # used to test if the x button works correctly
    def test_press_x_button(self):
        # set up copied from test_order_controller_update_several_then_cancel
        self.view.controller.table_touched(6)
        self.view.controller.seat_touched(7)
        the_order = self.restaurant.tables[6].order_for(7)
        self.view.controller.add_item(self.restaurant.menu_items[0])
        self.view.controller.add_item(self.restaurant.menu_items[3])
        self.view.controller.add_item(self.restaurant.menu_items[5])
        self.view.controller.update_order()

        def check_first_three_items(menu_items, items):
            self.assertEqual(menu_items[0], items[0].details)
            self.assertEqual(menu_items[3], items[1].details)
            self.assertEqual(menu_items[5], items[2].details)

        self.assertEqual(3, len(the_order.items))
        check_first_three_items(self.restaurant.menu_items, the_order.items)

        def add_two_more(menu_items, view):
            view.controller.add_item(menu_items[1])
            view.controller.add_item(menu_items[2])

        # adds two items then removes the items
        self.view.controller.seat_touched(7)
        add_two_more(self.restaurant.menu_items, self.view)
        self.view.controller.cancel_item(the_order.items[-1])
        self.view.controller.cancel_item(the_order.items[-1])

        # checks if successful
        self.assertEqual(3, len(the_order.items))
        check_first_three_items(self.restaurant.menu_items, the_order.items)

        # adds two items then cancels one after order has been placed
        add_two_more(self.restaurant.menu_items, self.view)
        self.view.controller.update_order()
        self.view.controller.seat_touched(7)
        self.view.controller.cancel_item(the_order.items[-1])

        # checks if successful
        self.assertEqual(4, len(the_order.items))
        check_first_three_items(self.restaurant.menu_items, the_order.items)
        self.assertEqual(self.restaurant.menu_items[1], the_order.items[3].details)


        # changes one items state then attemps to cancel
        controller_holder = self.view.controller
        self.view.set_controller(KitchenController(self.view, self.restaurant))
        self.assertIsInstance(self.view.controller, KitchenController)
        #This one line is causing errors and IDK why
        self.view.controller.progress_state(the_order.items[-1])
        self.view.set_controller(controller_holder)
        self.assertIsInstance(self.view.controller, OrderController)
        self.view.controller.cancel_item(the_order.items[-1])

        #checks if successful
        self.assertEqual(4, len(the_order.items))
        check_first_three_items(self.restaurant.menu_items, the_order.items)
        self.assertEqual(self.restaurant.menu_items[1], the_order.items[3].details)

    def test_change_state(self):

        """
             STATES
        state 1: "Start Cooking"
        state 2: "Mark as ready"
        state 3: "Mark as served"
        else: "Served"
        """

        R = RestaurantController(self.view, self.restaurant)
        K = KitchenController(self.view, self.restaurant)


        # Changes the current controller to what's being passed
        def controller_changer(change_to):
            self.view.set_controller(change_to)

        # switch to kitchen controller
        controller_changer(K)

        #  conf the switch was successful
        self.assertIsInstance(self.view.controller, KitchenController)

        controller_changer(R)
        self.assertIsInstance(self.view.controller, RestaurantController)

        #   add one dish to the order
        the_order_list = self.view.controller.table_touched(2)
        the_order_list = self.view.controller.seat_touched(1)
        the_order_list = self.view.controller.add_item(1)

        #   order the item
        self.view.controller.update_order()
        the_order_list = self.view.restaurant.tables[2].order_for(1)
        controller_changer(K)


    # CASE 1: can we order and cook one item?
        # loop through the order stages and ensure one item can be successfully ordered

        self.assertEqual("Start Cooking", self.view.controller.button_text(the_order_list.items[0]))

        #  call same comd as in oorms (self.controller.progress_state(order_item))
        #  progstate inc the state by 1, 5 times to complete the order (not ordered -> mark as served)
        for i in range(4):
            for item in the_order_list.items:
                # if item.has_been_ordered() and not item.has_been_served():
                self.view.controller.progress_state(item)


        self.assertEqual("Served", self.view.controller.button_text(the_order_list.items[0]))

        # remove the item from the list
        del the_order_list.items[:]

        # make sure it's now an empty list
        self.assertEqual(0, len(the_order_list.items))



    # CASE 2: can we order two and cook the newest one ordered?
        controller_changer(R)

        # make a new order
        the_order_list_2 = self.view.controller.table_touched(1)
        the_order_list_2 = self.view.controller.seat_touched(2)

        # add two itens to the order
        the_order_list_2 = self.view.controller.add_item(2)
        the_order_list_2 = self.view.controller.add_item(3)

        # order the item
        self.view.controller.update_order()
        the_order_list_2 = self.view.restaurant.tables[1].order_for(2)
        controller_changer(K)

        # ensure they were all orderd
        self.assertEqual("Start Cooking", self.view.controller.button_text(the_order_list_2.items[0]))
        self.assertEqual("Start Cooking", self.view.controller.button_text(the_order_list_2.items[1]))

        # 2. loop through and cook +serve the newest one
        for i in range(4):
            self.view.controller.progress_state(the_order_list_2.items[1])

        # 3. check to make sure the only item still in the order list is the first one put into it
        self.assertEqual("Start Cooking", self.view.controller.button_text(the_order_list_2.items[0]))
        self.assertEqual("Served", self.view.controller.button_text(the_order_list_2.items[1]))

    # CASE 3: can we order two and coook the oldest one ordered?
        controller_changer(R)

        # make a new order
        the_order_list_3 = self.view.controller.table_touched(3)
        the_order_list_3 = self.view.controller.seat_touched(1)

        # add two itens to the order
        the_order_list_3 = self.view.controller.add_item(4)
        the_order_list_3 = self.view.controller.add_item(5)

        # order the item
        self.view.controller.update_order()
        the_order_list_3 = self.view.restaurant.tables[3].order_for(1)
        controller_changer(K)

        # ensure they were all orderd
        self.assertEqual("Start Cooking", self.view.controller.button_text(the_order_list_3.items[0]))
        self.assertEqual("Start Cooking", self.view.controller.button_text(the_order_list_3.items[1]))

        # 2. loop through and cook +serve the oldest one
        for i in range(4):
            self.view.controller.progress_state(the_order_list_3.items[0])

        # 3. check to make sure the only item still in the order list is the last one put into it
        self.assertEqual("Served", self.view.controller.button_text(the_order_list_3.items[0]))
        self.assertEqual("Start Cooking", self.view.controller.button_text(the_order_list_3.items[1]))

