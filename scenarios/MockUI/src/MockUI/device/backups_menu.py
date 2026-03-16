from ..basic import ORANGE_HEX, RED_HEX, GenericMenu
from ..basic.symbol_lib import BTC_ICONS

class BackupsMenu(GenericMenu):
    """Menu for managing backups on SD Card."""

    TITLE_KEY = "MENU_MANAGE_BACKUPS"

    def get_menu_items(self, t, state):
        if state.SD_detected():
            return [
                (BTC_ICONS.RECEIVE, t("BACKUPS_MENU_BACKUP_TO_SD"), "backup_to_sd", None, None, None),
                (BTC_ICONS.SEND, t("BACKUPS_MENU_RESTORE_FROM_SD"), "restore_from_sd", None, None, None),
                (BTC_ICONS.CROSS, t("BACKUPS_MENU_REMOVE_FROM_SD"), "remove_backup_from_sd", RED_HEX, None, None),
            ]
        else:
            return (None, t("BACKUPS_MENU_NO_SD_DETECTED"), None, None, None, None),
