from qgis.PyQt.QtCore import QCoreApplication, QSettings, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QToolButton, QDialog, QVBoxLayout, QCheckBox, QListWidget, QPushButton
from qgis.gui import QgsPreviewEffect
import os

# Full labels (for tooltips and selection dialog)
MODE_FULL = [
    "Normal",
    "Monochrome",
    "Achromatopsia (Grayscale)",
    "Protanopia (No Red)",
    "Deuteranopia (No Green)",
    "Tritanopia (No Blue)",
]

# Short labels (for on-button text only)
MODE_SHORT = [
    "Normal",
    "Monochrome",
    "Grayscale",
    "Protanopia",
    "Deuteranopia",
    "Tritanopia",
]

# Enum mapping (index-aligned with the above)
MODE_ENUMS = [
    None,                                # 0 Normal -> disable preview
    QgsPreviewEffect.PreviewMono,        # 1 Monochrome
    QgsPreviewEffect.PreviewGrayscale,   # 2 Achromatopsia
    QgsPreviewEffect.PreviewProtanope,   # 3 Protanopia
    QgsPreviewEffect.PreviewDeuteranope, # 4 Deuteranopia
    QgsPreviewEffect.PreviewTritanope,   # 5 Tritanopia
]

# Icon filenames (index-aligned). Place these SVGs in <plugin>/icons/
SVG_FILES = [
    "normal.svg",
    "monochrome.svg",
    "achromatopsia.svg",
    "protanopia.svg",
    "deuteranopia.svg",
    "tritanopia.svg",
]

class ColourBlindPlugin:
    """Two-button colour-blind preview switcher with icon/text toggle and active highlight."""

    _tr_context = 'ColourBlind'

    @staticmethod
    def tr(message):
        return QCoreApplication.translate(ColourBlindPlugin._tr_context, message)

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        # Settings
        self.primary_index = int(QSettings().value("ColourBlind/primary_index", 0))
        self.secondary_index = int(QSettings().value("ColourBlind/secondary_index", 3))
        self.current_active = QSettings().value("ColourBlind/last_used", "primary")
        self.use_icons = QSettings().value("ColourBlind/use_icons", True, type=bool)
        self.disable_highlight = QSettings().value("ColourBlind/disable_highlight", False, type=bool)

        # UI
        self.toolbar = None
        self.primary_button = None
        self.secondary_button = None

        # Preload icons to avoid repeated file I/O
        self._icons = [self._load_icon(f) for f in SVG_FILES]

    # ---------- QGIS plugin entry points ----------
    def initGui(self):
        self.toolbar = self.iface.addToolBar(self.tr('ColourBlind'))
        self.toolbar.setObjectName('ColourBlind')

        # Add two mode buttons
        self.primary_button = self._create_mode_button("primary")
        self.secondary_button = self._create_mode_button("secondary")

        self.toolbar.addWidget(self.primary_button)
        self.toolbar.addWidget(self.secondary_button)

        # Initial paint
        self._update_button_display(self.primary_button)
        self._update_button_display(self.secondary_button)
        self._apply_preview_mode()

    def unload(self):
        if self.toolbar:
            self.iface.mainWindow().removeToolBar(self.toolbar)
            self.toolbar = None

    def run(self):
        pass

    # ---------- Button creation & updates ----------
    def _create_mode_button(self, name):
        btn = QToolButton()
        btn.setObjectName(name)
        btn.setCheckable(True)

        btn.clicked.connect(lambda checked, n=name: self._set_active_button(n))
        btn.setContextMenuPolicy(Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(lambda pos, b=btn: self._choose_mode_for_button(b))

        return btn

    def _update_button_display(self, button):
        idx = self.primary_index if button.objectName() == "primary" else self.secondary_index

        # Tooltip always shows full descriptive label
        button.setToolTip(MODE_FULL[idx])

        if self.use_icons:
            button.setIcon(self._icons[idx])
            button.setText("")
            button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        else:
            button.setIcon(QIcon())
            button.setText(MODE_SHORT[idx])
            button.setToolButtonStyle(Qt.ToolButtonTextOnly)
            button.setAutoRaise(False)

        # Apply highlight/checked style
        if self.disable_highlight:
            button.setStyleSheet("""
                QToolButton:checked {
                    border: none;
                    background: transparent;
                }
            """)
        else:
            button.setStyleSheet("")

        button.setChecked(button.objectName() == self.current_active)

    def _load_icon(self, filename):
        path = os.path.join(self.plugin_dir, "icons", filename)
        return QIcon(path) if os.path.exists(path) else QIcon()

    # ---------- Actions ----------
    def _set_active_button(self, name):
        self.current_active = name
        self.primary_button.setChecked(self.current_active == "primary")
        self.secondary_button.setChecked(self.current_active == "secondary")
        self._apply_preview_mode()
        self._save_settings()

    def _apply_preview_mode(self):
        canvas = self.iface.mapCanvas()
        idx = self.primary_index if self.current_active == "primary" else self.secondary_index

        if idx == 0:
            canvas.setPreviewModeEnabled(False)
        else:
            canvas.setPreviewModeEnabled(True)
            canvas.setPreviewMode(MODE_ENUMS[idx])

        canvas.refresh()

    def _choose_mode_for_button(self, button):
        dlg = QDialog(self.iface.mainWindow())
        dlg.setWindowTitle(f"{button.objectName().capitalize()} Preview Mode Settings")
        layout = QVBoxLayout(dlg)

        # Use icons checkbox
        cb_icons = QCheckBox("Use icons (disable for text option)")
        cb_icons.setChecked(self.use_icons)
        layout.addWidget(cb_icons)

        # Disable highlight checkbox
        cb_disable_highlight = QCheckBox("Disable button highlight")
        cb_disable_highlight.setChecked(self.disable_highlight)
        layout.addWidget(cb_disable_highlight)

        # Mode list
        list_widget = QListWidget()
        for label in MODE_FULL:
            list_widget.addItem(label)
        current_idx = self.primary_index if button.objectName() == "primary" else self.secondary_index
        list_widget.setCurrentRow(current_idx)
        layout.addWidget(list_widget)

        # ---------- Live update handler ----------
        def live_update():
            self.use_icons = cb_icons.isChecked()
            self.disable_highlight = cb_disable_highlight.isChecked()
            new_idx = list_widget.currentRow()
            if button.objectName() == "primary":
                self.primary_index = new_idx
            else:
                self.secondary_index = new_idx

            # Update buttons visuals
            for btn in (self.primary_button, self.secondary_button):
                self._update_button_display(btn)

            # Update preview if active button changed
            if button.objectName() == self.current_active:
                self._apply_preview_mode()

        # Connect live updates
        cb_icons.toggled.connect(live_update)
        cb_disable_highlight.toggled.connect(live_update)
        list_widget.currentRowChanged.connect(lambda _: live_update())

        # OK button (just closes dialog; settings already live)
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(dlg.accept)
        layout.addWidget(ok_btn)

        dlg.exec_()

        # Save settings at the end
        self._save_settings()

    # ---------- Settings ----------
    def _save_settings(self):
        QSettings().setValue("ColourBlind/primary_index", self.primary_index)
        QSettings().setValue("ColourBlind/secondary_index", self.secondary_index)
        QSettings().setValue("ColourBlind/last_used", self.current_active)
        QSettings().setValue("ColourBlind/use_icons", self.use_icons)
        QSettings().setValue("ColourBlind/disable_highlight", self.disable_highlight)
