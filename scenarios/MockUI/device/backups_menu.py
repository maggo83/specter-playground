from ..basic import GenericMenu
import lvgl as lv

class BackupsMenu(GenericMenu):
    """Menu for managing backups on SD Card.

    menu_id: "manage_backups"
    """

    def __init__(self, parent, *args, **kwargs):
        state = getattr(parent, "specter_state", None)

        menu_items = [
            (lv.SYMBOL.DOWNLOAD + "  " + lv.SYMBOL.SD_CARD, "Backup to SD Card ", "backup_to_sd"),
            (lv.SYMBOL.UPLOAD + "  " + lv.SYMBOL.SD_CARD, "Restore from SD Card ", "restore_from_sd"),
            (lv.SYMBOL.CLOSE + "   " + lv.SYMBOL.SD_CARD, "Remove from SD Card ", "remove_backup_from_sd"),
        ]

        title = lv.SYMBOL.COPY + " Manage Backups"

        super().__init__("manage_backups", title, menu_items, parent, *args, **kwargs)
