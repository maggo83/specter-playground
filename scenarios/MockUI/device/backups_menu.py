from ..basic import GenericMenu
import lvgl as lv

class BackupsMenu(GenericMenu):
    """Menu for managing backups on SD Card.

    menu_id: "manage_backups"
    """

    def __init__(self, parent, *args, **kwargs):
        state = getattr(parent, "specter_state", None)

        menu_items = [
            (lv.SYMBOL.DOWNLOAD + " Backup device to SD Card " + lv.SYMBOL.SD_CARD, "backup_to_sd"),
            (lv.SYMBOL.UPLOAD + " Restore device from SD Card " + lv.SYMBOL.SD_CARD, "restore_from_sd"),
            (lv.SYMBOL.TRASH + " Remove Backup from SD Card " + lv.SYMBOL.SD_CARD, "remove_backup_from_sd"),
        ]

        title = lv.SYMBOL.COPY + " Manage Backups"

        super().__init__("manage_backups", title, menu_items, parent, *args, **kwargs)
