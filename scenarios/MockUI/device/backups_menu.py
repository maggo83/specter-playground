from ..basic import ORANGE_HEX, RED_HEX, GenericMenu
import lvgl as lv
from ..basic.symbol_lib import BTC_ICONS

class BackupsMenu(GenericMenu):
    """Menu for managing backups on SD Card.

    menu_id: "manage_backups"
    """

    def __init__(self, parent, *args, **kwargs):
        state = getattr(parent, "specter_state", None)

        menu_items = [
            (BTC_ICONS.RECEIVE, "Backup to SD Card ", "backup_to_sd", None),
            (BTC_ICONS.SEND, "Restore from SD Card ", "restore_from_sd", None),
            (BTC_ICONS.CROSS, "Remove from SD Card ", "remove_backup_from_sd", RED_HEX),
        ]

        title = "Manage Backups"

        super().__init__("manage_backups", title, menu_items, parent, *args, **kwargs)
