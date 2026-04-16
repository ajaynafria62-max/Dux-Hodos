# -*- coding: utf-8 -*-
"""
Dux Hodos - QGIS Plugin
Navigate scattered vector point data feature-by-feature.

Copyright (c) 2025 Ajay Nafria Mandhana & Sharma A
Department of Geography, CBLU
Contact: ajaynafria62@gmail.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.
"""

__author__ = "Ajay Nafria Mandhana & Sharma A"
__email__ = "ajaynafria62@gmail.com"
__date__ = "2025"
__copyright__ = "Copyright (c) 2025 Ajay Nafria Mandhana & Sharma A"
__license__ = "GPL-2.0-or-later"
__version__ = "3.8"

from qgis.PyQt.QtWidgets import (
    QAction,
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtGui import QColor, QDesktopServices, QFont
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsDistanceArea,
    QgsGeometry,
    QgsMapLayerProxyModel,
    QgsPointXY,
    QgsProject,
    QgsRectangle,
    QgsWkbTypes,
)
from qgis.gui import QgsHighlight, QgsMapLayerComboBox


# ---------------------------------------------------------------------------
# Qt5 / Qt6 enum compatibility
# Qt6 moved many enums into scoped namespaces. _get() resolves either form.
# ---------------------------------------------------------------------------
def _get(obj, *names):
    """Return the first resolvable attribute from *names on *obj."""
    for name in names:
        val = obj
        try:
            for part in name.split("."):
                val = getattr(val, part)
            return val
        except AttributeError:
            continue
    raise AttributeError("Enum not found: {} on {}".format(names, obj))


Qt_RightDock      = _get(Qt, "DockWidgetArea.RightDockWidgetArea",  "RightDockWidgetArea")
Qt_Checked        = _get(Qt, "CheckState.Checked",                  "Checked")
Qt_Unchecked      = _get(Qt, "CheckState.Unchecked",                "Unchecked")
Qt_AlignCenter    = _get(Qt, "AlignmentFlag.AlignCenter",           "AlignCenter")
Qt_PointingHand   = _get(Qt, "CursorShape.PointingHandCursor",      "PointingHandCursor")
Qt_MoveAction     = _get(Qt, "DropAction.MoveAction",               "MoveAction")
Qt_UserRole       = _get(Qt, "ItemDataRole.UserRole",               "UserRole")
Qt_ItemEnabled    = _get(Qt, "ItemFlag.ItemIsEnabled",              "ItemIsEnabled")
Qt_ItemCheckable  = _get(Qt, "ItemFlag.ItemIsUserCheckable",        "ItemIsUserCheckable")
Qt_ItemDraggable  = _get(Qt, "ItemFlag.ItemIsDragEnabled",          "ItemIsDragEnabled")
Qt_ItemSelectable = _get(Qt, "ItemFlag.ItemIsSelectable",           "ItemIsSelectable")
QFrame_NoFrame    = _get(QFrame, "Shape.NoFrame",                   "NoFrame")
QFrame_HLine      = _get(QFrame, "Shape.HLine",                    "HLine")
DRAG_INTERNAL     = _get(QAbstractItemView, "DragDropMode.InternalMove", "InternalMove")
POPUP_INSTANT     = _get(QToolButton, "ToolButtonPopupMode.InstantPopup", "InstantPopup")
BTN_OK            = _get(QDialogButtonBox, "StandardButton.Ok",    "Ok")
BTN_CANCEL        = _get(QDialogButtonBox, "StandardButton.Cancel","Cancel")
SP_Expanding      = _get(QSizePolicy, "Policy.Expanding",           "Expanding")
SP_Preferred      = _get(QSizePolicy, "Policy.Preferred",           "Preferred")
ScrollOff         = _get(Qt, "ScrollBarPolicy.ScrollBarAlwaysOff",  "ScrollBarAlwaysOff")

# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------
_HL_COLOR   = QColor(220, 30, 30, 220)
_HL_FILL    = QColor(220, 30, 30,  60)
_HL_WIDTH   = 4

_BB = "font-size:14px;font-weight:bold;border-radius:4px;color:white;"
S_BTN_Y = _BB + "background:#1a7a3c;border:1px solid #145e2e;"
S_BTN_N = _BB + "background:#b52a2a;border:1px solid #8a1f1f;"
S_BTN_D = _BB + "background:#5a5a8a;border:1px solid #3e3e6a;"
S_CNT_Y = ("font-size:11px;font-weight:600;padding:2px 4px;"
            "border-radius:3px;background:#EAF3DE;color:#27500A;")
S_CNT_N = ("font-size:11px;font-weight:600;padding:2px 4px;"
            "border-radius:3px;background:#FCEBEB;color:#A32D2D;")
S_CNT_D = ("font-size:11px;font-weight:600;padding:2px 4px;"
            "border-radius:3px;background:#EEEDFE;color:#3C3489;")
S_NAV   = ("font-size:13px;font-weight:bold;"
           "border:1.5px solid #333;border-radius:5px;padding:7px 12px;")

# Field name/type substrings that indicate a spatial/geometry column.
# These are excluded from the Quick Edit field combo.
_SPATIAL_NAMES = ("geom", "wkt", "shape", "geometry", "the_geom")
_SPATIAL_TYPES = ("geometry", "wkb", "wkt", "point", "linestring",
                  "polygon", "multipoint", "multilinestring", "multipolygon")


# ===========================================================================
class DuxHodosPlugin:
    """QGIS plugin wrapper - registered by classFactory."""

    def __init__(self, iface):
        self.iface  = iface
        self.dock   = None
        self.action = None

    # ------------------------------------------------------------------
    def initGui(self):
        self.action = QAction("Dux Hodos", self.iface.mainWindow())
        self.action.setCheckable(True)
        self.action.setToolTip("Open Dux Hodos panel")
        self.action.triggered.connect(self.toggle_dock)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu("Dux Hodos", self.action)
        self.dock = DuxHodosDock(self.iface)
        self.iface.addDockWidget(Qt_RightDock, self.dock)
        self.dock.visibilityChanged.connect(self.action.setChecked)

    def unload(self):
        if self.action:
            self.iface.removePluginVectorMenu("Dux Hodos", self.action)
            self.iface.removeToolBarIcon(self.action)
        if self.dock:
            self.iface.removeDockWidget(self.dock)
            self.dock.cleanup()
            self.dock = None

    def toggle_dock(self, checked):
        if self.dock:
            self.dock.setVisible(checked)


# ===========================================================================
class CollapsibleSection(QWidget):
    """A section widget whose content can be folded / unfolded."""

    def __init__(self, title, collapsed=False, parent=None):
        super(CollapsibleSection, self).__init__(parent)
        self._title = title
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.btn = QPushButton()
        self.btn.setCheckable(True)
        self.btn.setChecked(not collapsed)
        self.btn.setFlat(True)
        self.btn.setCursor(Qt_PointingHand)
        self.btn.setStyleSheet(
            "QPushButton{text-align:left;font-weight:bold;"
            "padding:4px 8px;border:none;"
            "border-bottom:1px solid palette(mid);}"
            "QPushButton:hover{background:palette(midlight);}")
        self.btn.clicked.connect(self._toggle)
        outer.addWidget(self.btn)

        self.body = QFrame()
        self.body.setFrameShape(QFrame_NoFrame)
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(4, 5, 4, 5)
        self.body_layout.setSpacing(4)
        outer.addWidget(self.body)

        self.body.setVisible(not collapsed)
        self._update_arrow(not collapsed)

    def _update_arrow(self, expanded):
        arrow = "v" if expanded else ">"
        self.btn.setText("  {}  {}".format(arrow, self._title))

    def _toggle(self, checked):
        self.body.setVisible(checked)
        self._update_arrow(checked)

    def add_widget(self, widget):
        self.body_layout.addWidget(widget)

    def add_layout(self, layout):
        self.body_layout.addLayout(layout)


# ===========================================================================
class DuxHodosDock(QDockWidget):
    """
    Main dock panel.

    State:
        nav_layer     - QgsVectorLayer being navigated
        feature_ids   - ordered list of QgsFeature IDs
        current_index - position in feature_ids
        highlight     - active QgsHighlight (red glow on current point)
        nn_mode_on    - nearest-neighbour mode active
        nn_visited    - FID history for NN back-navigation
    """

    def __init__(self, iface):
        super(DuxHodosDock, self).__init__("Dux Hodos")
        self.iface         = iface
        self.canvas        = iface.mapCanvas()
        self.nav_layer     = None
        self.feature_ids   = []
        self.current_index = 0
        self.highlight     = None
        self.nn_mode_on    = False
        self.nn_visited    = []
        self._build_ui()

    # -----------------------------------------------------------------------
    # UI construction
    # -----------------------------------------------------------------------
    def _build_ui(self):
        root = QWidget()
        vl = QVBoxLayout(root)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)
        vl.addWidget(self._build_scroll_panel())
        self.setWidget(root)

    def _build_scroll_panel(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame_NoFrame)
        scroll.setHorizontalScrollBarPolicy(ScrollOff)

        inner = QWidget()
        inner.setSizePolicy(SP_Expanding, SP_Preferred)
        ly = QVBoxLayout(inner)
        ly.setSpacing(3)
        ly.setContentsMargins(4, 4, 4, 4)

        # --- Layer row + inline Reset ---
        top = QHBoxLayout()
        top.setSpacing(4)

        self.layer_combo = QgsMapLayerComboBox()
        self.layer_combo.setFilters(
            QgsMapLayerProxyModel.Filter.VectorLayer
            if hasattr(QgsMapLayerProxyModel, "Filter")
            else QgsMapLayerProxyModel.VectorLayer)
        self.layer_combo.layerChanged.connect(self._reload_layer)

        reload_btn = QPushButton("r")
        reload_btn.setFixedSize(24, 24)
        reload_btn.setToolTip("Reload features from selected layer")
        reload_btn.clicked.connect(self._reload_layer)

        self.menu_btn = QToolButton()
        self.menu_btn.setText("...")
        self.menu_btn.setFixedSize(24, 24)
        self.menu_btn.setPopupMode(POPUP_INSTANT)
        self._build_dot_menu()

        reset_btn = QPushButton("R")
        reset_btn.setFixedSize(24, 24)
        reset_btn.setToolTip(
            "Reset all plugin settings.\n"
            "Layer DATA is never modified.")
        reset_btn.setStyleSheet(
            "font-weight:bold;color:#b52a2a;"
            "border:1px solid #b52a2a;"
            "border-radius:3px;background:transparent;")
        reset_btn.clicked.connect(self._reset_plugin)

        top.addWidget(self.layer_combo)
        top.addWidget(reload_btn)
        top.addWidget(self.menu_btn)
        top.addWidget(reset_btn)
        ly.addLayout(top)

        # --- Counter ---
        self.counter_lbl = QLabel("  --  /  --  ")
        self.counter_lbl.setAlignment(Qt_AlignCenter)
        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        self.counter_lbl.setFont(font)
        ly.addWidget(self.counter_lbl)

        # --- Navigate & Edit (open) ---
        ne = CollapsibleSection("Navigate & Edit", collapsed=False)

        row_fl = QHBoxLayout()
        self.first_btn = QPushButton("First")
        self.last_btn  = QPushButton("Last")
        self.first_btn.setMinimumHeight(24)
        self.last_btn.setMinimumHeight(24)
        self.first_btn.clicked.connect(self.go_first)
        self.last_btn.clicked.connect(self.go_last)
        row_fl.addWidget(self.first_btn)
        row_fl.addWidget(self.last_btn)
        ne.add_layout(row_fl)

        row_pn = QHBoxLayout()
        self.prev_btn = QPushButton("< Prev")
        self.next_btn = QPushButton("Next >")
        for btn in (self.prev_btn, self.next_btn):
            btn.setMinimumHeight(38)
            btn.setStyleSheet(S_NAV)
        self.prev_btn.clicked.connect(self.go_prev)
        self.next_btn.clicked.connect(self.go_next)
        row_pn.addWidget(self.prev_btn)
        row_pn.addWidget(self.next_btn)
        ne.add_layout(row_pn)

        sep = QFrame()
        sep.setFrameShape(QFrame_HLine)
        sep.setStyleSheet("color:palette(mid);")
        ne.add_widget(sep)

        row_field = QHBoxLayout()
        row_field.addWidget(QLabel("Field:"))
        self.edit_combo = QComboBox()
        self.edit_combo.currentIndexChanged.connect(self._refresh_current_value)
        self.edit_combo.currentIndexChanged.connect(self._refresh_ynd_counts)
        row_field.addWidget(self.edit_combo)
        ne.add_layout(row_field)

        self.cur_val_lbl = QLabel("Current: -")
        self.cur_val_lbl.setStyleSheet("font-size:11px;color:gray;")
        ne.add_widget(self.cur_val_lbl)

        self.bulk_chk = QCheckBox("Apply to all selected features")
        self.bulk_chk.setChecked(False)
        ne.add_widget(self.bulk_chk)

        row_ynd = QHBoxLayout()
        row_ynd.setSpacing(5)
        self.btn_Y, self.lbl_y = self._make_ynd_col(
            "Y", S_BTN_Y, S_CNT_Y, row_ynd, lambda: self._write_value("Y"))
        self.btn_N, self.lbl_n = self._make_ynd_col(
            "N", S_BTN_N, S_CNT_N, row_ynd, lambda: self._write_value("N"))
        self.btn_D, self.lbl_d = self._make_ynd_col(
            "D", S_BTN_D, S_CNT_D, row_ynd, lambda: self._write_value("D"))
        ne.add_layout(row_ynd)

        self.total_lbl = QLabel("Total marked: 0  |  Remaining: --")
        self.total_lbl.setAlignment(Qt_AlignCenter)
        self.total_lbl.setStyleSheet(
            "font-size:11px;padding:2px 4px;"
            "border-radius:3px;background:palette(window);")
        ne.add_widget(self.total_lbl)

        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt_AlignCenter)
        self.status_lbl.setStyleSheet("font-size:11px;")
        ne.add_widget(self.status_lbl)

        ly.addWidget(ne)

        # --- Feature Source (collapsed) ---
        src = CollapsibleSection("Feature Source", collapsed=True)
        self.src_all_chk = QCheckBox("All features")
        self.src_sel_chk = QCheckBox("Selected features only")
        self.src_all_chk.setChecked(True)
        self.src_all_chk.stateChanged.connect(self._on_src_all)
        self.src_sel_chk.stateChanged.connect(self._on_src_sel)
        use_sel = QPushButton("Use Current Map Selection")
        use_sel.clicked.connect(self._load_selected)
        src.add_widget(self.src_all_chk)
        src.add_widget(self.src_sel_chk)
        src.add_widget(use_sel)
        ly.addWidget(src)

        # --- Sort (collapsed) ---
        self.sort_sec = CollapsibleSection("Sort / Order by Fields", collapsed=True)
        hint = QLabel("Check fields and drag to reorder (top = primary sort):")
        hint.setStyleSheet("font-size:11px;color:gray;")
        hint.setWordWrap(True)
        self.sort_sec.add_widget(hint)
        self.sort_list = QListWidget()
        self.sort_list.setDragDropMode(DRAG_INTERNAL)
        self.sort_list.setDefaultDropAction(Qt_MoveAction)
        self.sort_list.setFixedHeight(80)
        self.sort_sec.add_widget(self.sort_list)
        row_dir = QHBoxLayout()
        row_dir.addWidget(QLabel("Direction:"))
        self.sort_dir = QComboBox()
        self.sort_dir.addItems(["Ascending (A to Z)", "Descending (Z to A)"])
        row_dir.addWidget(self.sort_dir)
        self.sort_sec.add_layout(row_dir)
        apply_sort = QPushButton("Apply Sort")
        apply_sort.clicked.connect(self._apply_sort)
        self.sort_sec.add_widget(apply_sort)
        ly.addWidget(self.sort_sec)

        # --- Nearest Neighbour (collapsed) ---
        self.nn_sec = CollapsibleSection("Nearest Neighbour", collapsed=True)
        self.nn_chk = QCheckBox("Enable Nearest Neighbour mode")
        self.nn_chk.stateChanged.connect(self._on_nn_toggle)
        self.nn_sec.add_widget(self.nn_chk)
        nn_reset = QPushButton("Reset Visited History")
        nn_reset.clicked.connect(self._nn_reset)
        self.nn_sec.add_widget(nn_reset)
        ly.addWidget(self.nn_sec)

        # --- Area Filter (collapsed) ---
        area_sec = CollapsibleSection("Area Filter", collapsed=True)
        row_al = QHBoxLayout()
        row_al.addWidget(QLabel("Layer:"))
        self.area_layer_combo = QgsMapLayerComboBox()
        self.area_layer_combo.setFilters(
            QgsMapLayerProxyModel.Filter.PolygonLayer
            if hasattr(QgsMapLayerProxyModel, "Filter")
            else QgsMapLayerProxyModel.PolygonLayer)
        self.area_layer_combo.setAllowEmptyLayer(True)
        row_al.addWidget(self.area_layer_combo)
        area_sec.add_layout(row_al)
        self.area_chk = QCheckBox("Navigate only inside this area")
        self.area_chk.stateChanged.connect(self._apply_area_filter)
        area_sec.add_widget(self.area_chk)
        self.area_sel_chk = QCheckBox("Only inside selected polygons of area layer")
        self.area_sel_chk.setEnabled(False)
        self.area_sel_chk.stateChanged.connect(self._apply_area_filter)
        self.area_chk.stateChanged.connect(
            lambda s: self.area_sel_chk.setEnabled(s == Qt_Checked))
        area_sec.add_widget(self.area_sel_chk)
        self.area_status_lbl = QLabel("")
        self.area_status_lbl.setStyleSheet("font-size:11px;color:#185FA5;")
        area_sec.add_widget(self.area_status_lbl)
        ly.addWidget(area_sec)

        # --- Raster Tile Filter - multiple rasters (collapsed) ---
        rast_sec = CollapsibleSection("Raster Tile Filter", collapsed=True)
        rast_hint = QLabel("Check one or more raster layers (union of extents):")
        rast_hint.setStyleSheet("font-size:11px;color:gray;")
        rast_hint.setWordWrap(True)
        rast_sec.add_widget(rast_hint)
        self.raster_list = QListWidget()
        self.raster_list.setFixedHeight(80)
        self.raster_list.setToolTip(
            "Points inside ANY checked raster extent will be included.")
        rast_sec.add_widget(self.raster_list)
        refresh_btn = QPushButton("Refresh Raster List")
        refresh_btn.clicked.connect(self._refresh_raster_list)
        rast_sec.add_widget(refresh_btn)
        self.raster_chk = QCheckBox("Navigate only inside selected raster extents")
        self.raster_chk.stateChanged.connect(self._apply_raster_filter)
        rast_sec.add_widget(self.raster_chk)
        self.raster_status_lbl = QLabel("")
        self.raster_status_lbl.setStyleSheet("font-size:11px;color:#185FA5;")
        rast_sec.add_widget(self.raster_status_lbl)
        ly.addWidget(rast_sec)

        # --- Map Views (collapsed) ---
        mv_sec = CollapsibleSection("Map Views", collapsed=True)
        sat_btn = QPushButton("Satellite View")
        sat_btn.setMinimumHeight(28)
        sat_btn.setStyleSheet(
            "font-size:11px;font-weight:bold;"
            "border:1.5px solid #2C5F2D;border-radius:4px;"
            "color:#2C5F2D;background:transparent;")
        sat_btn.setToolTip("Open current point in Google Maps Satellite view")
        sat_btn.clicked.connect(self._open_satellite)
        mv_sec.add_widget(sat_btn)
        sv_btn = QPushButton("Street View")
        sv_btn.setMinimumHeight(28)
        sv_btn.setStyleSheet(
            "font-size:11px;font-weight:bold;"
            "border:1.5px solid #1967D2;border-radius:4px;"
            "color:#1967D2;background:transparent;")
        sv_btn.setToolTip(
            "Open current point in Google Street View.\n"
            "Falls back to Maps view if no Street View imagery is available.")
        sv_btn.clicked.connect(self._open_street_view)
        mv_sec.add_widget(sv_btn)
        row_buf = QHBoxLayout()
        row_buf.addWidget(QLabel("Street View radius (m):"))
        self.sv_radius = QSpinBox()
        self.sv_radius.setRange(0, 5000)
        self.sv_radius.setValue(50)
        self.sv_radius.setSuffix(" m")
        self.sv_radius.setToolTip(
            "Search radius for nearest Street View imagery.\n"
            "Set 0 to use exact point coordinates.")
        row_buf.addWidget(self.sv_radius)
        mv_sec.add_layout(row_buf)
        ly.addWidget(mv_sec)

        ly.addStretch()
        scroll.setWidget(inner)
        return scroll

    def _make_ynd_col(self, letter, btn_style, cnt_style, parent_row, slot):
        """Build a Y/N/D column: button on top, count label below."""
        col = QVBoxLayout()
        col.setSpacing(2)
        btn = QPushButton(letter)
        btn.setMinimumHeight(36)
        btn.setStyleSheet(btn_style)
        btn.clicked.connect(slot)
        lbl = QLabel("{}: 0".format(letter))
        lbl.setAlignment(Qt_AlignCenter)
        lbl.setStyleSheet(cnt_style)
        col.addWidget(btn)
        col.addWidget(lbl)
        parent_row.addLayout(col)
        return btn, lbl

    # -----------------------------------------------------------------------
    # Three-dot menu
    # -----------------------------------------------------------------------
    def _build_dot_menu(self):
        menu = QMenu(self)
        jump_act = QAction("Jump to feature #...", self)
        jump_act.triggered.connect(self._show_jump_dialog)
        menu.addAction(jump_act)
        menu.addSeparator()
        self.act_highlight = QAction("Highlight current point (red)", self)
        self.act_highlight.setCheckable(True)
        self.act_highlight.setChecked(True)
        self.act_highlight.toggled.connect(self._on_highlight_toggled)
        menu.addAction(self.act_highlight)
        self.act_select = QAction("Select feature on map", self)
        self.act_select.setCheckable(True)
        self.act_select.setChecked(True)
        menu.addAction(self.act_select)
        self.menu_btn.setMenu(menu)

    def _show_jump_dialog(self):
        if not self.feature_ids:
            return
        total = len(self.feature_ids)
        dlg = QDialog(self)
        dlg.setWindowTitle("Jump to Feature")
        dlg.setFixedWidth(240)
        fl = QFormLayout(dlg)
        spin = QSpinBox()
        spin.setMinimum(1)
        spin.setMaximum(total)
        spin.setValue(self.current_index + 1)
        fl.addRow("Feature # (1 - {}):".format(total), spin)
        btns = QDialogButtonBox(BTN_OK | BTN_CANCEL)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        fl.addRow(btns)
        if dlg.exec_() == QDialog.Accepted:
            self.current_index = spin.value() - 1
            self._pan_and_refresh()

    # -----------------------------------------------------------------------
    # Source toggles
    # -----------------------------------------------------------------------
    def _on_src_all(self, state):
        if state == Qt_Checked:
            self.src_sel_chk.blockSignals(True)
            self.src_sel_chk.setChecked(False)
            self.src_sel_chk.blockSignals(False)

    def _on_src_sel(self, state):
        if state == Qt_Checked:
            self.src_all_chk.blockSignals(True)
            self.src_all_chk.setChecked(False)
            self.src_all_chk.blockSignals(False)

    # -----------------------------------------------------------------------
    # Layer loading
    # -----------------------------------------------------------------------
    def _reload_layer(self):
        """Load features from the currently selected vector layer."""
        self._clear_highlight()
        if self.nav_layer:
            try:
                self.nav_layer.selectionChanged.disconnect(self._on_map_selection)
            except Exception:
                pass

        self.nav_layer = self.layer_combo.currentLayer()
        if not self.nav_layer:
            self.feature_ids = []
            self.counter_lbl.setText("  --  /  --  ")
            self.sort_list.clear()
            self.edit_combo.clear()
            return

        self._populate_field_lists()
        self.src_all_chk.setChecked(True)
        self.feature_ids   = [f.id() for f in self.nav_layer.getFeatures()]
        self.current_index = 0
        self._nn_reset()
        self._refresh_raster_list()
        self.nav_layer.selectionChanged.connect(self._on_map_selection)
        self._pan_and_refresh()

    def _populate_field_lists(self):
        """
        Populate the sort list and the quick-edit combo.
        Geometry / spatial fields are excluded from the edit combo so that
        WKT strings never appear in the Current Value label.
        """
        self.sort_list.clear()
        self.edit_combo.clear()
        if not self.nav_layer:
            return

        flags = Qt_ItemEnabled | Qt_ItemCheckable | Qt_ItemDraggable | Qt_ItemSelectable
        for field in self.nav_layer.fields():
            fn        = field.name()
            type_name = field.typeName().lower()

            # Sort list always shows all fields
            item = QListWidgetItem(fn)
            item.setFlags(flags)
            item.setCheckState(Qt_Unchecked)
            self.sort_list.addItem(item)

            # Edit combo excludes geometry / spatial fields
            is_spatial = (
                any(t in type_name for t in _SPATIAL_TYPES) or
                any(t in fn.lower()  for t in _SPATIAL_NAMES)
            )
            if not is_spatial:
                self.edit_combo.addItem(fn)

    def _on_map_selection(self, selected_ids, deselected_ids, clear_and_select):
        """
        Jump to a feature when the user clicks it on the map.
        Only reacts to single-feature selections to avoid accidental jumps
        during multi-select operations.
        """
        if not self.nav_layer or not self.feature_ids:
            return
        sel = self.nav_layer.selectedFeatureIds()
        if len(sel) != 1:
            return
        fid = sel[0]
        if fid not in self.feature_ids:
            return
        self.current_index = self.feature_ids.index(fid)
        # Use _pan_only to avoid re-triggering selectionChanged
        self._pan_only(fid)

    def _load_selected(self):
        """Navigate only the features currently selected on the map."""
        if not self.nav_layer:
            return
        sel = self.nav_layer.selectedFeatureIds()
        if not sel:
            self.counter_lbl.setText("  0  /  0  ")
            return
        self.feature_ids   = list(sel)
        self.current_index = 0
        self.src_sel_chk.setChecked(True)
        self._nn_reset()
        self._pan_and_refresh()

    # -----------------------------------------------------------------------
    # Raster list
    # -----------------------------------------------------------------------
    def _refresh_raster_list(self):
        """Populate the raster layer checklist from the current QGIS project."""
        self.raster_list.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == layer.RasterLayer:
                item = QListWidgetItem(layer.name())
                item.setData(Qt_UserRole, layer.id())
                item.setFlags(Qt_ItemEnabled | Qt_ItemCheckable | Qt_ItemSelectable)
                item.setCheckState(Qt_Unchecked)
                self.raster_list.addItem(item)

    def _checked_raster_layers(self):
        """Return QgsRasterLayer objects for all checked items."""
        layers = []
        for i in range(self.raster_list.count()):
            item = self.raster_list.item(i)
            if item.checkState() == Qt_Checked:
                layer_id = item.data(Qt_UserRole)
                layer = QgsProject.instance().mapLayer(layer_id)
                if layer:
                    layers.append(layer)
        return layers

    # -----------------------------------------------------------------------
    # Area Filter
    # -----------------------------------------------------------------------
    def _apply_area_filter(self):
        if not self.nav_layer:
            return
        if not self.area_chk.isChecked():
            self.feature_ids = (
                list(self.nav_layer.selectedFeatureIds())
                if self.src_sel_chk.isChecked()
                else [f.id() for f in self.nav_layer.getFeatures()])
            self.area_status_lbl.setText("")
            self.current_index = 0
            self._nn_reset()
            self._pan_and_refresh()
            return

        area_layer = self.area_layer_combo.currentLayer()
        if not area_layer:
            return

        if self.area_sel_chk.isChecked():
            sel_ids = area_layer.selectedFeatureIds()
            area_geoms = [
                f.geometry() for f in area_layer.getFeatures()
                if f.id() in sel_ids
                and f.geometry() and not f.geometry().isEmpty()
            ]
        else:
            area_geoms = [
                f.geometry() for f in area_layer.getFeatures()
                if f.geometry() and not f.geometry().isEmpty()
            ]
        if not area_geoms:
            return

        tr = QgsCoordinateTransform(
            self.nav_layer.crs(), area_layer.crs(), QgsProject.instance())
        src_fids = (
            list(self.nav_layer.selectedFeatureIds())
            if self.src_sel_chk.isChecked()
            else [f.id() for f in self.nav_layer.getFeatures()])

        inside = []
        for feat in self.nav_layer.getFeatures():
            if feat.id() not in src_fids:
                continue
            g = feat.geometry()
            if not g or g.isEmpty():
                continue
            raw_pt = (
                g.asPoint()
                if QgsWkbTypes.geometryType(g.wkbType()) == QgsWkbTypes.GeometryType.PointGeometry
                else g.centroid().asPoint())
            try:
                pt = tr.transform(raw_pt)
            except Exception:
                pt = raw_pt
            pt_geom = QgsGeometry.fromPointXY(pt)
            if any(ag.contains(pt_geom) for ag in area_geoms):
                inside.append(feat.id())

        self.feature_ids = inside
        self.current_index = 0
        self.area_status_lbl.setText(
            "Inside: {} / {}".format(len(inside), self.nav_layer.featureCount()))
        self._nn_reset()
        self._pan_and_refresh()

    # -----------------------------------------------------------------------
    # Raster Tile Filter (multiple rasters)
    # -----------------------------------------------------------------------
    def _apply_raster_filter(self):
        """
        Keep only points that fall inside at least one checked raster extent.
        Multiple rasters form a union: a point inside ANY extent is kept.
        """
        if not self.nav_layer:
            return
        if not self.raster_chk.isChecked():
            self.feature_ids = (
                list(self.nav_layer.selectedFeatureIds())
                if self.src_sel_chk.isChecked()
                else [f.id() for f in self.nav_layer.getFeatures()])
            self.raster_status_lbl.setText("")
            self.current_index = 0
            self._nn_reset()
            self._pan_and_refresh()
            return

        raster_layers = self._checked_raster_layers()
        if not raster_layers:
            return

        # Transform each raster extent to nav layer CRS
        nav_extents = []
        for rl in raster_layers:
            tr = QgsCoordinateTransform(
                rl.crs(), self.nav_layer.crs(), QgsProject.instance())
            try:
                nav_extents.append(tr.transformBoundingBox(rl.extent()))
            except Exception:
                nav_extents.append(rl.extent())

        src_fids = (
            list(self.nav_layer.selectedFeatureIds())
            if self.src_sel_chk.isChecked()
            else [f.id() for f in self.nav_layer.getFeatures()])

        inside = []
        for feat in self.nav_layer.getFeatures():
            if feat.id() not in src_fids:
                continue
            g = feat.geometry()
            if not g or g.isEmpty():
                continue
            pt = (g.asPoint()
                  if QgsWkbTypes.geometryType(g.wkbType()) == QgsWkbTypes.GeometryType.PointGeometry
                  else g.centroid().asPoint())
            if any(ext.contains(pt) for ext in nav_extents):
                inside.append(feat.id())

        self.feature_ids = inside
        self.current_index = 0
        self.raster_status_lbl.setText(
            "Inside {}/{} rasters: {} / {} points".format(
                len(raster_layers), self.raster_list.count(),
                len(inside), self.nav_layer.featureCount()))
        self._nn_reset()
        self._pan_and_refresh()

    # -----------------------------------------------------------------------
    # Sort
    # -----------------------------------------------------------------------
    def _apply_sort(self):
        if not self.nav_layer or not self.feature_ids:
            return
        checked_fields = [
            self.sort_list.item(i).text()
            for i in range(self.sort_list.count())
            if self.sort_list.item(i).checkState() == Qt_Checked
        ]
        if not checked_fields:
            return

        ascending = (self.sort_dir.currentIndex() == 0)
        fid_set   = set(self.feature_ids)
        features  = [f for f in self.nav_layer.getFeatures() if f.id() in fid_set]

        def sort_key(feat):
            result = []
            for field_name in checked_fields:
                v = feat[field_name]
                if v is None:
                    result.append((1, ""))
                elif isinstance(v, str):
                    result.append((0, v.lower()))
                else:
                    result.append((0, v))
            return result

        features.sort(key=sort_key, reverse=not ascending)
        self.feature_ids   = [f.id() for f in features]
        self.current_index = 0
        self._nn_reset()
        self._pan_and_refresh()

    # -----------------------------------------------------------------------
    # Nearest Neighbour
    # -----------------------------------------------------------------------
    def _on_nn_toggle(self, state):
        self.nn_mode_on = (state == Qt_Checked)
        self.nn_visited = (
            [self.feature_ids[self.current_index]]
            if self.nn_mode_on and self.feature_ids
            else []
        )

    def _nn_reset(self):
        self.nn_visited = []

    def _point_of(self, fid):
        """Return layer-CRS QgsPointXY for a feature, or None."""
        feat = self.nav_layer.getFeature(fid)
        g    = feat.geometry()
        if not g or g.isEmpty():
            return None
        return (g.asPoint()
                if QgsWkbTypes.geometryType(g.wkbType()) == QgsWkbTypes.GeometryType.PointGeometry
                else g.centroid().asPoint())

    def _ellipsoidal_dist(self, p1, p2):
        da = QgsDistanceArea()
        da.setSourceCrs(
            self.nav_layer.crs(),
            QgsProject.instance().transformContext())
        da.setEllipsoid(QgsProject.instance().ellipsoid())
        return da.measureLine(p1, p2)

    def _nearest_unvisited_index(self):
        """Return index of the closest unvisited feature, or None."""
        cur_pt = self._point_of(self.feature_ids[self.current_index])
        if cur_pt is None:
            return None
        visited = set(self.nn_visited)
        best_dist, best_idx = float("inf"), None
        for idx, fid in enumerate(self.feature_ids):
            if fid in visited or idx == self.current_index:
                continue
            pt = self._point_of(fid)
            if pt is None:
                continue
            d = self._ellipsoidal_dist(cur_pt, pt)
            if d < best_dist:
                best_dist = d
                best_idx  = idx
        return best_idx

    # -----------------------------------------------------------------------
    # Navigation
    # -----------------------------------------------------------------------
    def go_next(self):
        if not self.feature_ids:
            return
        if self.nn_mode_on:
            ni = self._nearest_unvisited_index()
            if ni is None:
                self._nn_reset()
                return
            self.current_index = ni
            self.nn_visited.append(self.feature_ids[ni])
        else:
            self.current_index = (self.current_index + 1) % len(self.feature_ids)
        self._pan_and_refresh()

    def go_prev(self):
        if not self.feature_ids:
            return
        if self.nn_mode_on and len(self.nn_visited) >= 2:
            self.nn_visited.pop()
            prev_fid = self.nn_visited[-1]
            if prev_fid in self.feature_ids:
                self.current_index = self.feature_ids.index(prev_fid)
        else:
            self.current_index = (self.current_index - 1) % len(self.feature_ids)
        self._pan_and_refresh()

    def go_first(self):
        self.current_index = 0
        if self.nn_mode_on and self.feature_ids:
            self._nn_reset()
            self.nn_visited = [self.feature_ids[0]]
        self._pan_and_refresh()

    def go_last(self):
        if not self.feature_ids:
            return
        self.current_index = len(self.feature_ids) - 1
        self._pan_and_refresh()

    # -----------------------------------------------------------------------
    # Pan + refresh  (single entry point - no duplicate calls)
    # -----------------------------------------------------------------------
    def _pan_and_refresh(self):
        """Pan the map to the current feature and update all UI elements."""
        if not self.feature_ids or not self.nav_layer:
            return
        fid     = self.feature_ids[self.current_index]
        feature = self.nav_layer.getFeature(fid)
        g       = feature.geometry()

        if g and not g.isEmpty():
            tr = QgsCoordinateTransform(
                self.nav_layer.crs(),
                self.canvas.mapSettings().destinationCrs(),
                QgsProject.instance())
            raw_pt = (g.asPoint()
                      if QgsWkbTypes.geometryType(g.wkbType()) == QgsWkbTypes.GeometryType.PointGeometry
                      else g.centroid().asPoint())
            try:
                canvas_pt = tr.transform(raw_pt)
            except Exception:
                canvas_pt = raw_pt
            self.canvas.setCenter(canvas_pt)
            self.canvas.refresh()

        self._clear_highlight()
        if self.act_highlight.isChecked():
            self.highlight = QgsHighlight(self.canvas, feature, self.nav_layer)
            self.highlight.setColor(_HL_COLOR)
            self.highlight.setWidth(_HL_WIDTH)
            self.highlight.setFillColor(_HL_FILL)
            self.highlight.show()

        if self.act_select.isChecked():
            self.nav_layer.selectByIds([fid])

        self.counter_lbl.setText(
            "  {}  /  {}  ".format(self.current_index + 1, len(self.feature_ids)))
        self._refresh_current_value()

    def _pan_only(self, fid):
        """
        Pan and highlight without calling selectByIds.
        Used by _on_map_selection to prevent recursive signal emission.
        """
        if not self.nav_layer:
            return
        feature = self.nav_layer.getFeature(fid)
        g = feature.geometry()
        if g and not g.isEmpty():
            tr = QgsCoordinateTransform(
                self.nav_layer.crs(),
                self.canvas.mapSettings().destinationCrs(),
                QgsProject.instance())
            raw_pt = (g.asPoint()
                      if QgsWkbTypes.geometryType(g.wkbType()) == QgsWkbTypes.GeometryType.PointGeometry
                      else g.centroid().asPoint())
            try:
                canvas_pt = tr.transform(raw_pt)
            except Exception:
                canvas_pt = raw_pt
            self.canvas.setCenter(canvas_pt)
            self.canvas.refresh()

        self._clear_highlight()
        if self.act_highlight.isChecked():
            self.highlight = QgsHighlight(self.canvas, feature, self.nav_layer)
            self.highlight.setColor(_HL_COLOR)
            self.highlight.setWidth(_HL_WIDTH)
            self.highlight.setFillColor(_HL_FILL)
            self.highlight.show()

        self.counter_lbl.setText(
            "  {}  /  {}  ".format(self.current_index + 1, len(self.feature_ids)))
        self._refresh_current_value()

    # -----------------------------------------------------------------------
    # Quick Field Edit
    # -----------------------------------------------------------------------
    def _refresh_current_value(self):
        if not self.feature_ids or not self.nav_layer:
            self.cur_val_lbl.setText("Current: -")
            return
        field_name = self.edit_combo.currentText()
        if not field_name:
            return
        val = self.nav_layer.getFeature(
            self.feature_ids[self.current_index])[field_name]
        if val is None:
            display = "NULL"
        else:
            s = str(val)
            display = (s[:60] + "...") if len(s) > 60 else s
        self.cur_val_lbl.setText("Current: {}".format(display))

    def _field_accepts_text(self, layer, field_index):
        """Return True if the field can store string values (Y/N/D)."""
        type_name = layer.fields().at(field_index).typeName().lower()
        return any(t in type_name for t in ("string", "text", "varchar", "char", "str"))

    def _write_value(self, value):
        """Write Y, N or D to the selected field."""
        if not self.feature_ids or not self.nav_layer:
            self._set_status("No layer or feature loaded.", "red")
            return
        field_name = self.edit_combo.currentText()
        if not field_name:
            self._set_status("Select a field first.", "red")
            return
        layer      = self.nav_layer
        field_idx  = layer.fields().indexOf(field_name)
        if field_idx < 0:
            self._set_status("Field not found in layer.", "red")
            return
        if not self._field_accepts_text(layer, field_idx):
            self._set_status(
                "Field '{}' is type '{}'. Choose a text/string field.".format(
                    field_name, layer.fields().at(field_idx).typeName()), "red")
            return

        was_editing = layer.isEditable()
        if not was_editing:
            layer.startEditing()

        if self.bulk_chk.isChecked():
            # Apply to all currently selected features on the map
            sel_ids = layer.selectedFeatureIds()
            if not sel_ids:
                if not was_editing:
                    layer.rollBack()
                self._set_status("No features selected on map.", "red")
                return
            count = sum(
                1 for fid in sel_ids
                if layer.changeAttributeValue(fid, field_idx, value))
            if count:
                if not was_editing:
                    layer.commitChanges()
                self._refresh_ynd_counts()
                self._set_status(
                    "{} features updated: {} = {}".format(count, field_name, value),
                    "green")
                self._refresh_current_value()
            else:
                if not was_editing:
                    layer.rollBack()
                self._set_status("No changes saved.", "red")
        else:
            # Apply to current navigated feature only
            fid = self.feature_ids[self.current_index]
            ok  = layer.changeAttributeValue(fid, field_idx, value)
            if ok:
                if not was_editing:
                    layer.commitChanges()
                self._refresh_ynd_counts()
                self._set_status("Saved: {} = {}".format(field_name, value), "green")
                self._refresh_current_value()
            else:
                if not was_editing:
                    layer.rollBack()
                self._set_status("Save failed. Check field type.", "red")

    def _refresh_ynd_counts(self):
        """Read actual Y/N/D values from the layer and update count labels."""
        if not self.nav_layer or not self.feature_ids:
            self.lbl_y.setText("Y: 0")
            self.lbl_n.setText("N: 0")
            self.lbl_d.setText("D: 0")
            self.total_lbl.setText("Total marked: 0  |  Remaining: --")
            return
        field_name = self.edit_combo.currentText()
        if not field_name:
            return
        fid_set = set(self.feature_ids)
        cy = cn = cd = 0
        for feat in self.nav_layer.getFeatures():
            if feat.id() not in fid_set:
                continue
            val = feat[field_name]
            if val is None:
                continue
            s = str(val).strip().upper()
            if s == "Y":
                cy += 1
            elif s == "N":
                cn += 1
            elif s == "D":
                cd += 1
        self.lbl_y.setText("Y: {}".format(cy))
        self.lbl_n.setText("N: {}".format(cn))
        self.lbl_d.setText("D: {}".format(cd))
        marked = cy + cn + cd
        total  = len(self.feature_ids)
        self.total_lbl.setText("Total marked: {}  |  Remaining: {}".format(
            marked, max(total - marked, 0)))

    def _set_status(self, message, color):
        self.status_lbl.setStyleSheet("font-size:11px;color:{};".format(color))
        self.status_lbl.setText(message)

    # -----------------------------------------------------------------------
    # Reset
    # -----------------------------------------------------------------------
    def _reset_plugin(self):
        reply = QMessageBox.question(
            self, "Reset Plugin",
            "Reset all plugin settings?\n\n"
            "This will clear:\n"
            "  - Selected layer\n"
            "  - Area and Raster filters\n"
            "  - Sort order\n"
            "  - Nearest Neighbour history\n\n"
            "Your layer data will NOT be changed.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        self._clear_highlight()
        if self.nav_layer:
            try:
                self.nav_layer.selectionChanged.disconnect(self._on_map_selection)
            except Exception:
                pass
            self.nav_layer.removeSelection()

        self.nav_layer     = None
        self.feature_ids   = []
        self.current_index = 0
        self.nn_mode_on    = False
        self.nn_visited    = []

        self.layer_combo.setLayer(None)
        self.counter_lbl.setText("  --  /  --  ")
        self.sort_list.clear()
        self.edit_combo.clear()
        self.cur_val_lbl.setText("Current: -")
        self.status_lbl.setText("")

        for chk in (self.src_all_chk, self.src_sel_chk,
                    self.area_chk, self.area_sel_chk,
                    self.raster_chk, self.nn_chk, self.bulk_chk):
            chk.blockSignals(True)
            chk.setChecked(False)
            chk.blockSignals(False)
        self.src_all_chk.blockSignals(True)
        self.src_all_chk.setChecked(True)
        self.src_all_chk.blockSignals(False)

        self.area_status_lbl.setText("")
        self.raster_status_lbl.setText("")
        self.sort_dir.setCurrentIndex(0)
        self.lbl_y.setText("Y: 0")
        self.lbl_n.setText("N: 0")
        self.lbl_d.setText("D: 0")
        self.total_lbl.setText("Total marked: 0  |  Remaining: --")

    # -----------------------------------------------------------------------
    # Map Views
    # -----------------------------------------------------------------------
    def _wgs84_coords(self):
        """Return (lat, lon) in WGS84 for the current feature, or (None, None)."""
        if not self.feature_ids or not self.nav_layer:
            return None, None
        feat = self.nav_layer.getFeature(self.feature_ids[self.current_index])
        g    = feat.geometry()
        if not g or g.isEmpty():
            return None, None
        raw_pt = (g.asPoint()
                  if QgsWkbTypes.geometryType(g.wkbType()) == QgsWkbTypes.GeometryType.PointGeometry
                  else g.centroid().asPoint())
        wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        tr    = QgsCoordinateTransform(self.nav_layer.crs(), wgs84, QgsProject.instance())
        try:
            pt = tr.transform(raw_pt)
            return pt.y(), pt.x()
        except Exception:
            return raw_pt.y(), raw_pt.x()

    def _open_satellite(self):
        lat, lon = self._wgs84_coords()
        if lat is None:
            self._set_status("No geometry available.", "red")
            return
        url = "https://www.google.com/maps?q={},{}&t=k&z=18".format(
            round(lat, 7), round(lon, 7))
        QDesktopServices.openUrl(QUrl(url))

    def _open_street_view(self):
        lat, lon = self._wgs84_coords()
        if lat is None:
            self._set_status("No geometry available.", "red")
            return
        radius = self.sv_radius.value()
        base   = "https://www.google.com/maps?q=&layer=c&cbll={},{}&cbp=11,0,0,0,0".format(
            round(lat, 7), round(lon, 7))
        url = (base + "&radius={}".format(radius)) if radius > 0 else base
        QDesktopServices.openUrl(QUrl(url))

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------
    def _clear_highlight(self):
        if self.highlight:
            self.highlight.hide()
            self.highlight = None

    def _on_highlight_toggled(self, checked):
        if not checked:
            self._clear_highlight()
        else:
            self._pan_and_refresh()

    def cleanup(self):
        """Called by plugin.unload() to release resources."""
        self._clear_highlight()
        if self.nav_layer:
            try:
                self.nav_layer.selectionChanged.disconnect(self._on_map_selection)
            except Exception:
                pass

    def closeEvent(self, event):
        self.cleanup()
        super(DuxHodosDock, self).closeEvent(event)
