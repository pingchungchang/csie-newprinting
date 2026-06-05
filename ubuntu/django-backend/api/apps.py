import logging
import os

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        # Bootstrap an initial admin from INITIAL_ADMIN_USERNAME.
        # Best-effort: if the np_admin table doesn't exist yet (pre-migration)
        # or another replica won the race, we log and move on. add_admin uses
        # ON CONFLICT DO NOTHING, so concurrent inserts are safe.
        username = os.environ.get("INITIAL_ADMIN_USERNAME", "").strip()
        if not username:
            return

        try:
            from .newprinting_db.admin.admin import add_admin
            ok = add_admin(username)
            if ok:
                logger.info(
                    f"Ensured initial admin user '{username}' is present."
                )
            else:
                logger.warning(
                    f"Failed to insert initial admin '{username}'; another "
                    "instance may have done it first or np_admin is not ready."
                )
        except Exception as e:
            logger.warning(f"Skipping initial admin bootstrap: {e}")
