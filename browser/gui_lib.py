"""
Utilities to make building GUIs simpler.
"""

import gtk

def pack_box(box, items):
    """
    Pack a list of items into a given box object
    """
    for item in items:
        item.show()
        box.pack_start(item, False, False, 0)
    box.show()

def make_box(cls, items):
    """
    Create a box of the given class and pack the given items into it.
    """
    box = cls()
    pack_box(box, items)
    return box

def make_button(label, callback, *args):
    """
    Create a gtk.Button with the given label and callback function.
    """
    button = gtk.Button(label)
    button.connect("clicked", callback, *args)
    return button

def make_cb(values):
    """
    Create a gtk.ComboBox with the given values.
    """
    cb = gtk.combo_box_new_text()
    cb._data = values
    [cb.append_text(str(text)) for text in values]
    cb.set_active(0)
    return cb

def set_bg(widget, colour):
    """
    Set the background of the given widget to a particular colour.
    """
    widget.modify_bg(gtk.STATE_NORMAL, widget.get_colormap().alloc_color(colour))
    widget.modify_bg(gtk.STATE_ACTIVE, widget.get_colormap().alloc_color(colour))
    widget.modify_bg(gtk.STATE_PRELIGHT, widget.get_colormap().alloc_color(colour))
    widget.modify_bg(gtk.STATE_SELECTED, widget.get_colormap().alloc_color(colour))
    widget.modify_bg(gtk.STATE_INSENSITIVE, widget.get_colormap().alloc_color(colour))

    

def refill_cb(cb, values, active=0):
    """
    Reset an existing ComboBox to have a given set of values.    
    """
    for i in range(len(cb.get_model())):
        cb.remove_text(0)
    cb._data = values
    [cb.append_text(str(text)) for text in values]
    cb.set_active(active)

def get_combo_item(cb):
    """
    Get the currently selected item from a ComboBox
    """
    model = cb.get_model()
    index = cb.get_active()
    if index >= 0:
        return cb._data[index]
    

def set_combo_item(cb, value):
    """
    Set the active item of a ComboBox to be a paricular item
    """
    if value in cb._data:
        cb.set_active(cb._data.index(value))
    
    

def make_entry_button(size, label, callback, *args):
    """
    Create an entry box of a given size along with a button with a given
    label and callback. Return the entry and also a packed box with both the
    entry and button.
    """
    entry = gtk.Entry(size)
    button = make_button(label, callback, *args)
    return entry, make_box(gtk.HBox, [entry, button])


def make_radio_list(items, callback, box_class=gtk.VBox):
    """
    Create a box containing a set of radio buttons, labeled with a set
    of items. Use a given callback for the toggle event.
    """
    buttons = []
    for label, args in items:
        if buttons:
            b0 = buttons[0]
        else:
            b0 = None
        button = gtk.RadioButton(b0, label)
        button.connect("toggled", callback, *args)
        buttons.append(button)
        
    return make_box(box_class, buttons)

def make_integer_adjustment(lo, hi):
    """
    Create an Adjustemnt object for integers between lo and hi
    """
    return gtk.Adjustment(lo, lo, hi, 1, 10)
    
def make_integer_spinner(lo, hi):
    """
    Create a SpinButton for integers between lo and hi.
    """
    adj = make_integer_adjustment(lo, hi)
    spinner = gtk.SpinButton(adj, climb_rate=0.5, digits=0)
    spinner.set_numeric(True)
    spinner.set_wrap(False)
    spinner.set_snap_to_ticks(True)
    return spinner

def make_float_adjustment(val, lo, hi, step):
    """
    Create an Adjustment object for floats between lo and hi, starting at val
    and going up by step.
    """
    return gtk.Adjustment(val, lo, hi, step)

def make_float_spinner(val, lo, hi, step):
    """
    Create a SpinButton object for floats between lo and hi, starting at val
    and going up by step.
    """

    adj = make_float_adjustment(val, lo, hi, step)
    spinner = gtk.SpinButton(adj, climb_rate=0.5, digits=2)
    spinner.set_numeric(True)
    spinner.set_wrap(False)
    spinner.set_snap_to_ticks(True)
    return spinner


class OutputList(object):
    """
    An object which consists of a pair of label/value columns.
    """

    def __init__(self, fields):
        """
        Create an OutputList with the given fields as labels.
        """
        left_box = make_box(gtk.VBox, [gtk.Label(field) for field in fields])
        self.right_box = make_box(gtk.VBox, [gtk.Label("") for field in fields])
        self.box = make_box(gtk.HBox, [left_box, self.right_box])

    def update(self, vals):
        """
        Set the values of the OutputList.
        """
        for label, val in zip(self.right_box.get_children(), vals):
            label.set_label(val)


def unique(items):
    """
    Return the unique items for a list of items. Removes any items which have
    previously been found in the list
    """
    return [items[i] for i in range(len(items)) if items[i] not in items[:i]]
        

def make_drop_menu(items, uniq=True):
    """
    Create a drop down menu of CheckMenuItems with a given list of labels.
    """
    if uniq:
        items = unique(items)
    menu = gtk.Menu()
    for item in items:
        menu_item = gtk.CheckMenuItem(item)
        menu.append(menu_item)
    menu_item = gtk.ImageMenuItem(gtk.STOCK_GO_DOWN)
    menu_item.child.set_label("")
    menu_item.set_submenu(menu)
    menu_bar = gtk.MenuBar()
    menu_bar.append(menu_item)
    menu_bar.show()
    return menu_bar

def get_checked_items(menu_bar):
    """
    Get those items from a drop down check menu which are checked.
    """
    menu = menu_bar.get_children()[0].get_submenu()
    return [mi.child.get_label() for mi in menu.get_children() if mi.get_active()]

def get_all_items(menu_bar):
    """
    Return all the items from a drop down check menu.
    """
    menu = menu_bar.get_children()[0].get_submenu()
    return [mi.child.get_label() for mi in menu.get_children()]


def clear_drop_list(menu_bar):
    """
    Uncheck all the items in a given menu
    """
    menu = menu_bar.get_children()[0].get_submenu()    
    for menu_item in menu.get_children():
        menu_item.set_active(False)

def update_drop_list(menu_bar, items, uniq=True):
    """
    Add a list of items to the top of menu list. Remove them from lower down
    if they exist.
    """
    if uniq:
        items = unique(items)
    menu = menu_bar.get_children()[0].get_submenu()
    existing = get_all_items(menu_bar)
    for item in items[::-1]:
        menu_item = gtk.CheckMenuItem(item)            
        menu.prepend(menu_item)
        if item in existing:
            mi = [mi for mi in menu.get_children() if mi.child.get_label() == item][1]
            menu.remove(mi)
            menu_item.set_active(True)

    menu_bar.show_all()


class DropDownCheckEntryBox(object):
    """
    A class to combine a text entry box with a drop down check menu acting as
    a history of entered values.
    """

    def __init__(self, filename, size=100):
        """
        Create a object, loading the history from the given filename.
        """
        self.filename = filename
        self.drop_list = make_drop_menu(self.get_cache())        
        self.entry = gtk.Entry(size)
        self.box = make_box(gtk.HBox, [self.drop_list, self.entry])

    def parse(self):
        """
        Parse the text entry box to create a list of items to be added to the
        drop down list.
        """
        items = [s.strip() for s in self.entry.get_text().split(" and ")]
        items = [s for s in items if s]
        return items

    def update(self):
        """
        update the list with the values from the text entry then save the list
        to the cache.
        """
        entry_items = self.parse()
        update_drop_list(self.drop_list, entry_items + get_checked_items(self.drop_list))

        self.set_cache()

    def get_items_and_entry(self):
        """
        Return the text from the entry box and a list of checked items in the
        menu.
        """
        entry = self.entry.get_text()                    
        items = get_checked_items(self.drop_list)
        return items, entry

    def clear(self):
        """
        Uncheck all items in the drop down list.
        """
        clear_drop_list(self.drop_list)

    def load(self, items):
        """
        Set the drop down checked values to be those given by items.
        """
        self.clear()
        update_drop_list(self.drop_list, items)

    def get_cache(self):
        """
        get a list of items from the objects' cache file.
        """
        f = open(self.filename, 'r')
        return [s.strip() for s in f.readlines()]

    def set_cache(self):
        """
        Save the current list of items in the drop down menu to the cache.
        """
        lines = get_all_items(self.drop_list)
        f = open(self.filename, 'w')
        for line in lines:
            f.write("%s\n" % line)
        f.close()
