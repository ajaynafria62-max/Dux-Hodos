# Dux Hodos - QGIS Plugin
# Copyright (c) 2025 Ajay Nafria Mandhana & Sharma A
# Department of Geography, CBLU
# Contact: ajaynafria62@gmail.com


def classFactory(iface):  # pylint: disable=invalid-name
    """Load DuxHodosPlugin class from file dux_hodos."""
    from .dux_hodos import DuxHodosPlugin
    return DuxHodosPlugin(iface)
