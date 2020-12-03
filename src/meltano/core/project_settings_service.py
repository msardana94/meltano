from dotenv import dotenv_values

from meltano.core.settings_service import (
    SettingsService,
    SettingMissingError,
    SettingValueStore,
)
from .config_service import ConfigService
from meltano.core.utils import nest_object

UI_CFG_SETTINGS = {
    "ui.server_name": "SERVER_NAME",
    "ui.secret_key": "SECRET_KEY",
    "ui.password_salt": "SECURITY_PASSWORD_SALT",
}


class ProjectSettingsService(SettingsService):
    config_override = {}

    def __init__(self, *args, config_service: ConfigService = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.config_service = config_service or ConfigService(self.project)

        self.env_override = {**self.project.env, **self.env_override}

        self.config_override = {
            **self.__class__.config_override,
            **self.config_override,
        }

    @property
    def label(self):
        return "Meltano"

    @property
    def docs_url(self):
        return "https://meltano.com/docs/settings.html"

    @property
    def _env_prefixes(self):
        return ["meltano"]

    @property
    def _db_namespace(self):
        return "meltano"

    @property
    def _definitions(self):
        return self.config_service.settings

    @property
    def _meltano_yml_config(self):
        return self.config_service.current_config

    def _update_meltano_yml_config(self, config):
        self.config_service.update_config(config)

    def _process_config(self, config):
        return nest_object(config)

    def get_with_metadata(self, name: str, *args, **kwargs):
        value, metadata = super().get_with_metadata(name, *args, **kwargs)
        source = metadata["source"]

        if source is SettingValueStore.DEFAULT:
            # Support legacy `ui.cfg` files generated by `meltano ui setup`
            ui_cfg_value = self.get_from_ui_cfg(name)
            if ui_cfg_value is not None:
                value = ui_cfg_value
                metadata["source"] = SettingValueStore.ENV

        return value, metadata

    def get_from_ui_cfg(self, name: str):
        try:
            key = UI_CFG_SETTINGS[name]
            config = dotenv_values(self.project.root_dir("ui.cfg"))
            value = config[key]

            # Since `ui.cfg` is technically a Python file, `'None'` means `None`
            if value == "None":
                value = None

            return value
        except KeyError:
            return None
