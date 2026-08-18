from .._json import error_envelope

NO_TOKEN = error_envelope(
    "not_configured",
    "No Backup Radar credentials. Send the X-BackupRadar-Api-Key and "
    "X-BackupRadar-Site headers.",
    False,
)
