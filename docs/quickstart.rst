Quick Start
===========

Installation
------------

.. code-block:: bash

   pip install fontstack

.. note::

   FontStack does not bundle fonts.  You need to supply your own ``.ttf``,
   ``.otf``, ``.ttc``, or ``.otc`` files.  The `Noto fonts
   <https://fonts.google.com/noto>`_ provide excellent Unicode coverage.

Basic usage
-----------

.. code-block:: python

   from PIL import Image
   from fontstack import FontConfig, FontManager

   manager = FontManager(
       default_stack=[
           FontConfig(path="fonts/NotoSans[wdth,wght].ttf"),
           FontConfig(path="fonts/NotoSansArabic[wdth,wght].ttf"),
       ]
   )

   img = Image.new("RGBA", (800, 100), "white")
   manager.draw(img, "Hello مرحبا", position=(20, 20), size=48, weight=700)
   img.save("output.png")

Using a font directory
----------------------

Instead of listing each font, point to a folder:

.. code-block:: python

   manager = FontManager(font_dir="fonts/")

Fonts are loaded in alphabetical order by filename - the first file becomes the
primary font and later files act as fallbacks.

One-shot rendering
------------------

``draw_text`` creates a manager, renders, and returns a cropped image:

.. code-block:: python

   from fontstack import draw_text

   img = draw_text(
       "Hello 世界 🌍",
       font_dir="fonts/",
       size=48,
       fill="red-blue",
       padding=16,
   )
   img.save("hello.png")
