import Queue

import gtk
import webkit

def launch_browser(uri, echo=True):
    # WARNING: You should call this function ONLY inside of GTK
    #          (i.e. use synchronous_gtk_message)

    window = gtk.Window()
    box = gtk.VBox(homogeneous=False, spacing=0)
    browser = webkit.WebView()

    window.set_default_size(800, 600)
    # Optional (you'll read about this later in the tutorial):
    window.connect('destroy', Global.set_quit)

    window.add(box)
    box.pack_start(browser, expand=True, fill=True, padding=0)

    window.show_all()

    # Note: All message passing stuff appears between these curly braces:
    # {
    message_queue = Queue.Queue()

    def title_changed(widget, frame, title):
        if title != 'null': message_queue.put(title)

    browser.connect('title-changed', title_changed)

    def web_recv():
        if message_queue.empty():
            return None
        else:
            msg = message_queue.get()
            if echo: print '>>>', msg
            return msg

    def web_send(msg):
        if echo: print '<<<', msg
        asynchronous_gtk_message(browser.execute_script)(msg)
    # }


    browser.open(uri)

    return browser, web_recv, web_send

uri = 'http://www.google.com/'
browser, web_recv, web_send = synchronous_gtk_message(launch_browser)(uri)