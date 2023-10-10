import gi
from gi.repository import GObject
from gi.repository import GdkPixbuf
from gi.repository import Gtk
import cv2
import numpy as np


gi.require_version('Gtk', '3.0')


class Frame(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)
        self.set_title("Frame")
        self.set_default_size(200, 200)
        self.set_border_width(5)
        self.connect("destroy", Gtk.main_quit)

        frame = Gtk.Frame(label="Frame")
        self.add(frame)

        #label = Gtk.Label("Label in a Frame")
        #frame.add(label)

        pic = cv2.imread("image.jpg")
        pic = cv2.cvtColor(pic, cv2.COLOR_BGR2RGB)
        pic = cv2.resize(pic, (400,600))
        pic = np.array(pic).ravel()
        print(pic.size)
        #pixbuf = GdkPixbuf.Pixbuf.new_from_data(pic,GdkPixbuf.Colorspace.RGB, False, 8, 600, 400, 3*600)
        pixbuf = GdkPixbuf.Pixbuf.new_from_data(pic.tobytes() ,GdkPixbuf.Colorspace.RGB, False, 8, 600, 400, 3*600)
        
        Image = Gtk.Image.new_from_pixbuf(pixbuf)
        frame.add(Image)


window = Frame()
window.show_all()

Gtk.main()

